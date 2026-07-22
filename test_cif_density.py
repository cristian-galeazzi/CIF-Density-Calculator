"""Validation suite for cif_density (synthetic data only).

Regenerates six synthetic test files at run time and runs the whole
pipeline on them. Lattice parameters are published values, except for the
mixed-site fluorite case, whose cell and occupancies are chosen so that the
exact cell content is known in advance. Two independent tolerance levels:

1. internal self-consistency (< 1e-8 relative): the reported density must
   equal rho = m_cell / (N_A * V) recomputed from the reported cell mass
   and volume. The residual ~1e-9 deviation is the documented difference
   between the CODATA atomic-mass constant used by pymatgen and the exact
   Avogadro route (see README), plus floating-point rounding (< 1e-15);
2. accuracy (< 0.2 % relative): agreement with densities hand-calculated
   from IUPAC standard atomic weights, fully independently of pymatgen.

Run with: pytest test_cif_density.py
"""
import pytest

from cif_density import (ANGSTROM3_TO_CM3, AVOGADRO, process_folder,
                         render_results)

# pytest resets warning filters, bypassing the module-level filters in
# cif_density; re-apply them here for the benign CIF parser warnings.
pytestmark = [
    pytest.mark.filterwarnings("ignore:Issues encountered while parsing CIF"),
    pytest.mark.filterwarnings("ignore:No _symmetry_equiv_pos_as_xyz"),
    pytest.mark.filterwarnings("ignore:Missing elements"),
]

# IUPAC standard atomic weights (2021), g/mol - independent reference data
IUPAC_MASS = {"Na": 22.98976928, "Cl": 35.45, "Si": 28.085, "Ce": 140.116,
              "O": 15.999, "La": 138.90547, "Y": 88.905838, "Zr": 91.224}

NACL_A, SI_A, CEO2_A, FLUORITE_A = 5.6402, 5.43095, 5.4113, 5.24

CUBIC_CIF = """data_{name}
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

SI_SITES = "\n".join(
    f"Si{i + 1} Si {x} {y} {z} 1"
    for i, (x, y, z) in enumerate([
        (0, 0, 0), (0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5),
        (0.25, 0.25, 0.25), (0.75, 0.75, 0.25), (0.75, 0.25, 0.75), (0.25, 0.75, 0.75),
    ])
)


def cubic_density(mass_per_cell_g_mol: float, a_angstrom: float) -> float:
    """Analytic reference: rho = m_cell / (N_A * a^3), a in Angstrom."""
    return mass_per_cell_g_mol / (AVOGADRO * (a_angstrom * 1e-8) ** 3)


# Defect fluorite (La,Y)2Zr2O7: three cations disordered on the same 4a site
# at fractional occupancy, plus a partly vacant anion site. This is the case
# the research use hits (several elements sharing one site), and the one the
# single-cation tests above cannot catch: occupancies must be summed per
# element across a shared site before the mass is formed.
# Cations 4a: La 1/4 + Y 1/4 + Zr 1/2 -> per cell La1 Y1 Zr2; O 8c at 7/8 -> O7.
FLUORITE_SITES = ("La1 La 0 0 0 0.25\n"
                  "Y1 Y 0 0 0 0.25\n"
                  "Zr1 Zr 0 0 0 0.5\n"
                  "O1 O 0.25 0.25 0.25 0.875")
FLUORITE_MASS = (IUPAC_MASS["La"] + IUPAC_MASS["Y"]
                 + 2 * IUPAC_MASS["Zr"] + 7 * IUPAC_MASS["O"])

# (file name) -> (independent reference density, expected reduced formula)
EXPECTED = {
    "NaCl.cif": (cubic_density(4 * (IUPAC_MASS["Na"] + IUPAC_MASS["Cl"]), NACL_A), "NaCl"),
    "Si.cif": (cubic_density(8 * IUPAC_MASS["Si"], SI_A), "Si"),
    "CeO2_multiblock.cif": (cubic_density(4 * (IUPAC_MASS["Ce"] + 2 * IUPAC_MASS["O"]), CEO2_A), "CeO2"),
    "CeO2_vacancies.cif": (cubic_density(4 * (IUPAC_MASS["Ce"] + 2 * 0.875 * IUPAC_MASS["O"]), CEO2_A), "Ce4O7"),
    "fluorite_mixed_site.cif": (cubic_density(FLUORITE_MASS, FLUORITE_A), "LaYZr2O7"),
}


@pytest.fixture(scope="module")
def batch(tmp_path_factory):
    """Write the six synthetic test files and process them once."""
    tmp = tmp_path_factory.mktemp("cif_validation")
    # NaCl: symmetry expansion from the space-group symbol.
    (tmp / "NaCl.cif").write_text(CUBIC_CIF.format(
        name="NaCl", a=NACL_A, spg="F m -3 m",
        sites="Na1 Na 0 0 0 1\nCl1 Cl 0.5 0.5 0.5 1"))
    # Si: explicit P1 atom list without symmetry operators.
    (tmp / "Si.cif").write_text(CUBIC_CIF.format(
        name="Si", a=SI_A, spg="P 1", sites=SI_SITES))
    # CeO2 behind a GSAS-II-style non-structural block.
    ceo2 = CUBIC_CIF.format(
        name="CeO2", a=CEO2_A, spg="F m -3 m",
        sites="Ce1 Ce 0 0 0 1\nO1 O 0.25 0.25 0.25 1")
    header = ("data_publication\n"
              "_audit_creation_method 'created in GSAS-II'\n"
              "_pd_phase_name 'metadata only, no structure'\n\n")
    (tmp / "CeO2_multiblock.cif").write_text(header + ceo2)
    # CeO2 with 12.5 % oxygen vacancies: partial occupancies.
    (tmp / "CeO2_vacancies.cif").write_text(CUBIC_CIF.format(
        name="CeO2_def", a=CEO2_A, spg="F m -3 m",
        sites="Ce1 Ce 0 0 0 1\nO1 O 0.25 0.25 0.25 0.875"))
    # Defect fluorite with three cations sharing one site at partial occupancy.
    (tmp / "fluorite_mixed_site.cif").write_text(CUBIC_CIF.format(
        name="fluorite_mixed", a=FLUORITE_A, spg="F m -3 m",
        sites=FLUORITE_SITES))
    # Corrupt file: must be isolated, not fatal.
    (tmp / "corrupt.cif").write_text("this file is deliberately not a valid CIF\n")

    results, errors = process_folder(tmp, output_csv=tmp / "out.csv")
    return results, errors, tmp


def row(results, fname):
    match = results[results["File"] == fname]
    assert len(match) == 1, f"expected exactly one row for {fname}"
    return match.iloc[0]


def test_phase_count(batch):
    results, _, _ = batch
    assert len(results) == len(EXPECTED)


def test_corrupt_file_isolated(batch):
    _, errors, _ = batch
    assert list(errors["File"]) == ["corrupt.cif"]


def test_csv_written(batch):
    results, _, tmp = batch
    out = (tmp / "out.csv").read_text().splitlines()
    assert len(out) == len(results) + 1  # header + one row per phase


def test_multiphase_rows_stay_distinguishable(tmp_path):
    """Two phases of one file must not collapse into identical display rows.

    Both phases here are Fm-3m, so the space group alone cannot tell them
    apart; the "(phase N)" suffix in the file name is what does.
    """
    two_phases = (
        CUBIC_CIF.format(name="phase_one", a=NACL_A, spg="F m -3 m",
                         sites="Na1 Na 0 0 0 1\nCl1 Cl 0.5 0.5 0.5 1")
        + CUBIC_CIF.format(name="phase_two", a=CEO2_A, spg="F m -3 m",
                           sites="Ce1 Ce 0 0 0 1\nO1 O 0.25 0.25 0.25 1"))
    (tmp_path / "two_phases.cif").write_text(two_phases)

    results, errors = process_folder(tmp_path)
    assert errors.empty
    assert list(results["File"]) == ["two_phases.cif (phase 1)",
                                     "two_phases.cif (phase 2)"]

    assert list(results["Space group"]) == ["Fm-3m", "Fm-3m"]

    html = render_results(results).data
    assert "<td>two_phases.cif (phase 1)</td>" in html
    assert "<td>two_phases.cif (phase 2)</td>" in html


@pytest.mark.parametrize("fname", EXPECTED)
def test_internal_self_consistency(batch, fname):
    results, _, _ = batch
    r = row(results, fname)
    rho_self = r["Cell mass (g/mol)"] / (AVOGADRO * r["Volume (A^3)"] * ANGSTROM3_TO_CM3)
    assert r["Density (g/cm^3)"] == pytest.approx(rho_self, rel=1e-8)


@pytest.mark.parametrize("fname", EXPECTED)
def test_density_vs_independent_reference(batch, fname):
    results, _, _ = batch
    rho_ref, _ = EXPECTED[fname]
    assert row(results, fname)["Density (g/cm^3)"] == pytest.approx(rho_ref, rel=2e-3)


@pytest.mark.parametrize("fname", EXPECTED)
def test_reduced_formula(batch, fname):
    results, _, _ = batch
    _, formula_ref = EXPECTED[fname]
    assert row(results, fname)["Formula"] == formula_ref
