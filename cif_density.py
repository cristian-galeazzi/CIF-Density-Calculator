"""Theoretical (X-ray) density from crystallographic CIF files.

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
from pathlib import Path

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
    "density_record",
    "process_folder",
]

# CIFs from Rietveld software trigger benign parser warnings; keep output
# clean (filter by message: the warning is attributed to the calling frame)
warnings.filterwarnings("ignore", message=".*Issues encountered while parsing CIF.*")
warnings.filterwarnings("ignore", message=".*stoichiometry.*")
warnings.filterwarnings("ignore", message=".*No _symmetry_equiv_pos_as_xyz.*")

AVOGADRO = 6.02214076e23   # mol^-1, exact (SI, 2019)
ANGSTROM3_TO_CM3 = 1e-24
CSV_FLOAT_FORMAT = "%.6g"  # rounding happens only at output time


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


def parse_cif_structures(path: Path) -> list[Structure]:
    """Parse every crystal structure (phase) contained in a CIF file."""
    text = select_structural_blocks(read_cif_text(path))
    parser = CifParser.from_str(text)
    return parser.parse_structures(primitive=False)


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


def process_folder(input_dir, output_csv=None):
    """Compute the density of every phase in every CIF file of a folder.

    Returns (results, errors) as two DataFrames. Files that cannot be
    parsed are reported in `errors` and never interrupt the batch. The
    extension match is case-insensitive (.cif/.CIF) on every OS without
    producing duplicates.
    """
    input_dir = Path(input_dir)
    cif_files = sorted(
        (p for p in input_dir.iterdir() if p.suffix.lower() == ".cif"),
        key=lambda p: p.name.lower(),
    )
    records, failures = [], []
    for cif_file in cif_files:
        try:
            structures = parse_cif_structures(cif_file)
            if not structures:
                raise ValueError("no crystal structure found in file")
            for i, structure in enumerate(structures):
                label = (cif_file.name if len(structures) == 1
                         else f"{cif_file.name} (phase {i + 1})")
                records.append(density_record(structure, label))
        except Exception as exc:
            failures.append({"File": cif_file.name, "Error": str(exc)})
    results = pd.DataFrame(records)
    errors = pd.DataFrame(failures)
    if output_csv is not None and not results.empty:
        results.to_csv(output_csv, index=False, float_format=CSV_FLOAT_FORMAT)
    return results, errors
