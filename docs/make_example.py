"""Build the synthetic structures behind the README example image.

Writes three public-domain / invented cubic structures (NaCl, CeO2, a defect
fluorite) as CIF files, runs the density pipeline on them, and saves the
four display columns as a small CSV. The PNG in the README is a screenshot of
the notebook's rendered table on these same structures; rerun this module,
open the notebook on the generated folder, and screenshot to refresh it.

No experimental data: every structure here is synthetic, matching the
validation suite's fixtures.

Run from the repository root:  python docs/make_example.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cif_density import process_folder  # noqa: E402  (after sys.path setup)

_CUBIC = """data_{name}
_cell_length_a {a}
_cell_length_b {a}
_cell_length_c {a}
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M '{spg}'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_occupancy
{sites}
"""

# (filename, a, space group, atom sites) - synthetic, no measurement.
_STRUCTURES = [
    ("NaCl.cif", 5.6402, "F m -3 m",
     "Na1 Na 0 0 0 1\nCl1 Cl 0.5 0.5 0.5 1"),
    ("CeO2.cif", 5.4113, "F m -3 m",
     "Ce1 Ce 0 0 0 1\nO1 O 0.25 0.25 0.25 1"),
    ("fluorite_defect.cif", 5.24, "F m -3 m",
     "La1 La 0 0 0 0.25\nY1 Y 0 0 0 0.25\n"
     "Zr1 Zr 0 0 0 0.5\nO1 O 0.25 0.25 0.25 0.875"),
]

_DISPLAY_COLUMNS = ["File", "Space group", "Volume (A^3)", "Density (g/cm^3)"]


def build_example(dest: Path):
    """Write the example display CSV to ``dest`` and return the full frame.

    >>> import tempfile, pathlib
    >>> frame = build_example(pathlib.Path(tempfile.mkdtemp()) / "ex.csv")
    >>> float(round(frame.set_index("File").loc["NaCl.cif", "Density (g/cm^3)"], 2))
    2.16
    """
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for name, a, spg, sites in _STRUCTURES:
            (folder / name).write_text(
                _CUBIC.format(name=name.split(".")[0], a=a, spg=spg, sites=sites))
        results, _ = process_folder(folder)
    dest.parent.mkdir(parents=True, exist_ok=True)
    results[_DISPLAY_COLUMNS].to_csv(dest, index=False, float_format="%.6g")
    return results


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "example_output_display.csv"
    frame = build_example(out)
    print(frame[_DISPLAY_COLUMNS].to_string(index=False))
    print(f"\nWrote {out}")
