"""Theoretical density from crystallographic CIF files.

Engine behind ``CIF_Density_Calculator.ipynb``: CIF reading, structural
block filtering and density calculation, with batch processing over a
folder. All arithmetic is IEEE-754 double precision with no intermediate
rounding; values are rounded only when written to the output CSV.

Method, input format and numerical-precision notes: see ``README.md``.
Validation suite: ``test_cif_density.py`` (run with ``pytest``).
"""
from __future__ import annotations

import re
import warnings
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # IPython is a notebook-time dependency, not an import-time one
    from IPython.display import HTML

import pandas as pd
from pymatgen.core import Composition, Structure
from pymatgen.io.cif import CifParser

__version__ = "1.0.0"

__all__ = [
    "AVOGADRO",
    "ANGSTROM3_TO_CM3",
    "CSV_FLOAT_FORMAT",
    "read_cif_text",
    "select_structural_blocks",
    "parse_cif_structures",
    "phase_indices",
    "density_record",
    "process_folder",
    "render_results",
]

# CIFs from Rietveld software trigger benign parser warnings; keep output
# clean (filter by message: the warning is attributed to the calling frame)
warnings.filterwarnings("ignore", message=".*Issues encountered while parsing CIF.*")
warnings.filterwarnings("ignore", message=".*stoichiometry.*")
warnings.filterwarnings("ignore", message=".*No _symmetry_equiv_pos_as_xyz.*")
# "Missing elements ..." is deliberately NOT silenced. On a single-block CIF it
# means pymatgen failed to place a declared element, which makes the density
# too low. On multi-block files it is spurious (see CLAUDE.md), but silencing
# it here would hide the real case too.

AVOGADRO = 6.02214076e23   # mol^-1, exact (SI, 2019)
ANGSTROM3_TO_CM3 = 1e-24
CSV_FLOAT_FORMAT = "%.6g"  # rounding happens only at output time

# Multi-phase files carry the phase index inside the File value. The display
# keeps that string intact rather than parsing it back out: two phases of one
# file can share a space group, so the index is what makes the rows distinct.
PHASE_LABEL = "{name} (phase {index})"

# pymatgen reports a section it could not build as "No structure parsed for
# section N in CIF."; N is 1-based over the blocks it was given.
SKIPPED_SECTION = re.compile(r"No structure parsed for section (\d+)")


def read_cif_text(path: Path) -> str:
    """Read a CIF file as text (UTF-8 with Latin-1 fallback)."""
    path = Path(path)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def select_structural_blocks(cif_text: str) -> str:
    """Keep only data_ blocks that define a unit cell.

    Rietveld programs (e.g. GSAS-II) export CIFs whose first blocks hold
    publication metadata or diffractogram data without any crystal
    structure; those blocks would make the parser fail. Blocks are split
    only at lines *starting* with 'data_'.
    """
    blocks = re.split(r"(?m)^(?=data_)", cif_text)
    keep = [b for b in blocks if b.startswith("data_") and "_cell_length_a" in b]
    return "\n".join(keep) if keep else cif_text


def parse_cif_structures(path: Path) -> tuple[list[Structure], list[str]]:
    """Parse every phase of a CIF file, with the parser's own warnings.

    The warnings are returned because pymatgen drops a block it cannot build
    and only records ``No structure parsed for section N``; without them a
    phase disappears from the batch silently.
    """
    text = select_structural_blocks(read_cif_text(path))
    parser = CifParser.from_str(text)
    return parser.parse_structures(primitive=False), list(parser.warnings)


def phase_indices(n_built: int, skipped_notes: list[str]) -> list[int]:
    """Section number of each structure pymatgen managed to build.

    A structure's position in the parsed list is not its section number:
    pymatgen drops the sections it cannot build, so every skipped one shifts
    all the following indices down. The lost section numbers are in the
    parser warnings, so the survivors are what is left of ``1..N``.

    Falls back to a plain ``1..n_built`` if a warning cannot be read, which
    is no worse than assuming nothing was skipped.

    >>> phase_indices(3, [])
    [1, 2, 3]
    >>> phase_indices(2, ["No structure parsed for section 2 in CIF."])
    [1, 3]
    >>> phase_indices(2, ["some warning in an unexpected format"])
    [1, 2]
    """
    lost = {int(n) for note in skipped_notes for n in SKIPPED_SECTION.findall(note)}
    if len(lost) != len(skipped_notes):
        return list(range(1, n_built + 1))
    return [i for i in range(1, n_built + len(lost) + 1) if i not in lost]


def density_record(structure: Structure, label: str = "") -> dict:
    """Full-precision summary of one phase (no intermediate rounding)."""
    lattice = structure.lattice
    comp = structure.composition
    # Element amounts are rounded (2 decimals) only to absorb refinement
    # noise in occupancies before deriving the *displayed* reduced formula;
    # the density itself always uses the raw composition.
    cleaned = Composition({el: round(n, 2) for el, n in comp.get_el_amt_dict().items()})
    try:
        space_group = structure.get_space_group_info()[0]
    except Exception:
        space_group = "N/A"
    _, z_units = cleaned.get_reduced_composition_and_factor()
    return {
        "File": label,
        "Formula": cleaned.reduced_formula,
        "Space group": space_group,
        "a (A)": lattice.a,
        "b (A)": lattice.b,
        "c (A)": lattice.c,
        "alpha (deg)": lattice.alpha,
        "beta (deg)": lattice.beta,
        "gamma (deg)": lattice.gamma,
        "Volume (A^3)": structure.volume,
        "Z": z_units,
        "Cell mass (g/mol)": float(comp.weight),
        "Density (g/cm^3)": structure.density,
    }


def process_folder(input_dir, output_csv=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute the density of every phase in every CIF file of a folder.

    Returns (results, errors) as two DataFrames. Files that cannot be
    parsed are reported in `errors` and never interrupt the batch. The
    extension match is case-insensitive (.cif/.CIF) on every OS without
    producing duplicates.

    The phase index in the File value is the CIF section number, so it stays
    correct when pymatgen skips a section, and it is written whenever the
    file holds more than one section, even if only one of them was built.
    """
    input_dir = Path(input_dir)
    cif_files = sorted(
        (p for p in input_dir.iterdir() if p.suffix.lower() == ".cif"),
        key=lambda p: p.name.lower(),
    )
    records, failures = [], []
    for cif_file in cif_files:
        try:
            structures, parser_notes = parse_cif_structures(cif_file)
            if not structures:
                raise ValueError("no crystal structure found in file")
            # A phase pymatgen could not build must not vanish from the batch.
            skipped = [n for n in parser_notes if "No structure parsed" in n]
            if skipped:
                failures.append({
                    "File": cif_file.name,
                    "Error": f"{len(skipped)} phase(s) skipped by pymatgen: "
                             + "; ".join(n.splitlines()[0] for n in skipped),
                })
            single_phase = len(structures) + len(skipped) == 1
            for index, structure in zip(phase_indices(len(structures), skipped),
                                        structures):
                label = (cif_file.name if single_phase
                         else PHASE_LABEL.format(name=cif_file.name, index=index))
                records.append(density_record(structure, label))
        except Exception as exc:
            failures.append({"File": cif_file.name, "Error": str(exc)})
    results = pd.DataFrame(records)
    errors = pd.DataFrame(failures)
    if output_csv is not None and not results.empty:
        results.to_csv(output_csv, index=False, float_format=CSV_FLOAT_FORMAT)
    return results, errors


# Display-side only. Headers carry real typographic units (the CSV keeps the
# ASCII ones); tabular-nums lines the digits up; the grey borders are given
# as rgba so the table reads on both light and dark notebook themes.
_CSS = """<style>
.cif-density { border-collapse: collapse; font-variant-numeric: tabular-nums; }
.cif-density th { text-align: left; font-weight: 600; padding: 7px 18px 7px 0;
                  border-bottom: 2px solid rgba(128,128,128,.55); white-space: nowrap; }
.cif-density td { padding: 6px 18px 6px 0; border-bottom: 1px solid rgba(128,128,128,.22); }
.cif-density tr:last-child td { border-bottom: none; }
.cif-density th:nth-child(n+3), .cif-density td:nth-child(n+3) { text-align: right; }
.cif-density caption { caption-side: bottom; text-align: left; padding-top: 8px;
                       font-size: .85em; opacity: .65; }
</style>"""


def render_results(results: pd.DataFrame, caption: str = "") -> "HTML":
    """Notebook table: file, space group, cell volume, theoretical density.

    Display only, so the CSV keeps its full ``CSV_FLOAT_FORMAT`` precision.
    The file name keeps the ``(phase N)`` suffix that ``process_folder``
    appends for multi-phase files: two phases of one file can share a space
    group, so the index is what keeps the rows distinguishable.

    Requires IPython, which every Jupyter/Colab kernel provides; importing
    ``cif_density`` from a plain script does not need it.

    >>> df = pd.DataFrame({"File": ["a.cif (phase 2)", "b.cif"],
    ...                    "Space group": ["Fd-3m", "Fm-3m"],
    ...                    "Volume (A^3)": [143.8778, 177.5],
    ...                    "Density (g/cm^3)": [6.678707, 2.186912]})
    >>> html = render_results(df).data
    >>> "<td>6.6787</td>" in html and "<td>177.50</td>" in html
    True
    >>> "<td>Fd-3m</td>" in html and "<td>a.cif (phase 2)</td>" in html
    True
    """
    from IPython.display import HTML  # notebook-only; keeps pytest import light

    if results.empty:
        return HTML("<em>No phases to display.</em>")
    html = (
        results[["File", "Space group", "Volume (A^3)", "Density (g/cm^3)"]]
        .rename(columns={"Volume (A^3)": "Cell volume (Å³)",
                         "Density (g/cm^3)": "Theoretical density (g/cm³)"})
        .to_html(index=False, border=0, classes="cif-density", justify="left",
                 formatters={"Cell volume (Å³)": "{:.2f}".format,
                             "Theoretical density (g/cm³)": "{:.4f}".format})
    )
    if caption:
        # Escaped by hand and placed before <thead>: to_html escapes cell
        # values but not this, and the HTML spec wants caption first.
        html = html.replace(
            "<thead>", f"<caption>{escape(caption)}</caption><thead>", 1)
    return HTML(_CSS + html)

