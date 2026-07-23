# How it works and how it is checked

Density follows from the refined unit cell:

$$\rho = \frac{m_\text{cell}}{V_\text{cell}} = \frac{\sum_i o_i\, M_i}{N_A \cdot V_\text{cell}}$$

$o_i$ is the site occupancy, $M_i$ the standard atomic weight (g mol⁻¹),
$V_\text{cell}$ the unit-cell volume and
$N_A = 6.022\,140\,76 \times 10^{23}\ \text{mol}^{-1}$ the Avogadro constant
(exact since the 2019 SI revision). Partial occupancies (vacancies, dopants,
mixed sites) are included rigorously.

Everything runs in double precision (machine epsilon ≈ 2.2 × 10⁻¹⁶), unrounded
until the CSV is written at 6 significant figures. One exception never touches
the density: element amounts are rounded to two decimals before `Z` is derived,
so a site refined at 0.9998 does not produce an absurd formula; `Cell
composition`, `Cell mass` and the density itself keep the raw amounts. A second,
smaller effect: pymatgen converts atomic mass to grams via the CODATA atomic
mass constant, while the formula above divides by the exact Avogadro constant.
Since the 2019 SI redefinition these are no longer identical, differing by about
1.05 × 10⁻⁹ relative with the CODATA 2022 value, a figure that follows CODATA
revisions and is worth recomputing rather than quoting.

## The validation suite

[`test_cif_density.py`](../test_cif_density.py) generates six synthetic test
files at run time and runs the whole pipeline on them:

```bash
pytest
```

Run it without a path: `pyproject.toml`'s `--doctest-modules` also runs the
`>>>` examples in `cif_density.py`; naming the file explicitly skips them.

| Case | Purpose |
|------|---------|
| NaCl (rock salt, a = 5.6402 Å) | Symmetry expansion from the space-group symbol |
| Si (diamond, a = 5.43095 Å, P1 setting) | Explicit atom list without symmetry operators |
| CeO₂ in a GSAS-II-style multi-block file | Filtering of non-structural data blocks |
| CeO₂ with 12.5 % oxygen vacancies | Partial occupancies in the density |
| A cubic oxide with three cations on one site | Occupancies summed per element across a shared site |
| A deliberately corrupt file | Error isolation (the batch must not stop) |

Two tolerances are checked: internal self-consistency (< 10⁻⁸ relative, density
must equal ρ = m_cell / (N_A · V) recomputed from the reported mass and volume;
the ~10⁻⁹ residual is the CODATA correction above plus floating-point rounding
< 10⁻¹⁵), and accuracy (< 0.2 % relative, against densities hand-calculated from
IUPAC standard atomic weights, independent of pymatgen). The notebook also
carries a self-check (one NaCl structure) for environments without pytest, e.g.
Colab, raising `AssertionError` on failure so a headless run cannot pass
silently.
