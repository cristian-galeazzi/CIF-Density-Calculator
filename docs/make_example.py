"""Generate example CIF structures for documentation."""

from pymatgen.core import Structure, Lattice
from pathlib import Path


def make_nacl():
    """Rock salt NaCl structure: Fm-3m, a = 5.6402 Å."""
    lattice = Lattice.cubic(5.6402)
    structure = Structure(
        lattice,
        ["Na", "Cl"],
        [[0, 0, 0], [0.5, 0.5, 0.5]],
    )
    return structure


def make_ceo2():
    """Fluorite CeO2 structure: Fm-3m, a = 5.4117 Å."""
    lattice = Lattice.cubic(5.4117)
    structure = Structure(
        lattice,
        ["Ce", "O"],
        [[0, 0, 0], [0.25, 0.25, 0.25]],
    )
    return structure


def make_defect_fluorite():
    """Defect fluorite RE2Zr2O7 (Ce2Zr2O7) structure: Fm-3m."""
    lattice = Lattice.cubic(10.5)
    structure = Structure(
        lattice,
        ["Ce", "Zr", "O"],
        [[0, 0, 0], [0.5, 0.5, 0.5], [0.375, 0.375, 0.375]],
    )
    return structure


def main():
    """Generate example CIF files."""
    docs_dir = Path(__file__).parent
    cif_dir = docs_dir.parent / "cif_files"
    cif_dir.mkdir(exist_ok=True)

    structures = {
        "nacl_example.cif": make_nacl(),
        "ceo2_example.cif": make_ceo2(),
        "defect_fluorite_example.cif": make_defect_fluorite(),
    }

    for filename, structure in structures.items():
        filepath = cif_dir / filename
        structure.to(filename=str(filepath), fmt="cif")
        print(f"Generated {filepath}")


if __name__ == "__main__":
    main()
