# CIF Density Calculator

*Theoretical (X-ray) density from crystallographic CIF files - batch
processing, built-in validation, cross-platform.*

A single, self-contained Jupyter notebook that computes the theoretical
density of every phase in a folder of CIF files and exports the results to
CSV. It handles multi-block CIFs exported by Rietveld software (e.g.
GSAS-II), multi-phase files, partial site occupancies (vacancies, dopants,
mixed sites) and non-UTF-8 encodings, and isolates unreadable files without
stopping the batch. Structure parsing and symmetry analysis are delegated
to [pymatgen](https://pymatgen.org) and
[spglib](https://spglib.readthedocs.io).

**Scope.** The quantity computed here is the *theoretical* density, also
called X-ray or crystallographic density: the mass of the refined unit
cell divided by its volume. It is not a measured density, and this tool
does not compute *relative* density (measured / theoretical) - that would
require an experimental value, e.g. from Archimedes weighing, which is
outside the scope of this repository.

## Contents

- [Project layout](#project-layout)
- [How to use](#how-to-use)
- [Input format](#input-format)
- [Output](#output)
- [Method](#method)
- [Validation and testing](#validation-and-testing)
- [Numerical precision](#numerical-precision)
- [Privacy: nothing private gets published](#privacy-nothing-private-gets-published)
- [How to cite](#how-to-cite)
- [AI assistance](#ai-assistance)
- [License](#license)

## Project layout

The calculation engine is a plain Python module, importable from scripts
and other notebooks; the notebook is only the user interface.

| File | Role |
|------|------|
| [`cif_density.py`](cif_density.py) | Calculation engine: CIF reading, block filtering, density calculation, batch driver |
| [`CIF_Density_Calculator.ipynb`](CIF_Density_Calculator.ipynb) | User interface: dependency bootstrap, quick self-check, batch run |
| [`test_cif_density.py`](test_cif_density.py) | Validation suite (`pytest`), synthetic data only |

```python
from cif_density import process_folder

results, errors = process_folder("cif_files", output_csv="density_results.csv")
```

## How to use

### Requirements

- Python ≥ 3.10 with `pymatgen` and `pandas`
  (see [`requirements.txt`](requirements.txt)); `pytest` is needed only to
  run the validation suite.
- Tested on Python 3.13 with pymatgen 2025.10.7.
- On Google Colab no installation is needed: the first cell installs any
  missing dependency automatically.

### Running locally

1. Install the dependencies and open the notebook:

   ```bash
   pip install -r requirements.txt
   jupyter lab CIF_Density_Calculator.ipynb
   ```

2. Copy your `.cif` files into the `cif_files/` folder (shipped empty with
   the repository, and created automatically on first run if missing).
3. Run all cells. Results are shown as a table and written to
   `density_results.csv`.

### Running on Google Colab

Upload **both** `CIF_Density_Calculator.ipynb` and `cif_density.py` to
[Colab](https://colab.research.google.com/) (the notebook goes through
*File → Upload notebook*, the module through the *Files* sidebar) and run
all cells: the `cif_files` folder is created automatically. Drag your CIF
files into it from the Files sidebar and re-run the last cell.

### Notebook structure

| Section | Purpose |
|---------|---------|
| 1 - Setup | Installs missing dependencies; imports the engine from `cif_density.py` |
| 2 - Quick self-check (optional) | End-to-end check on one synthetic NaCl structure |
| 3 - Batch run | Processes every CIF in `cif_files/` and writes `density_results.csv` |

### Configuration

Both user-adjustable parameters live in the last code cell:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `INPUT_FOLDER` | `"cif_files"` | Folder containing your `.cif` files |
| `OUTPUT_CSV` | `"density_results.csv"` | Results table, written next to the notebook |

## Input format

Standard crystallographic CIF files; any block that defines a unit cell is
processed. Accepted variations:

| Feature | Behavior |
|---------|----------|
| Multi-block CIFs (Rietveld exports, e.g. GSAS-II) | Non-structural blocks (publication metadata, diffractogram data) are filtered out automatically |
| Multi-phase files | One result row per phase |
| Partial site occupancies | Vacancies, dopants and mixed sites enter the density rigorously |
| Symmetry | Both space-group symbols (sites expanded by symmetry) and explicit P1 atom lists are accepted |
| File extension | `.cif` and `.CIF`, matched case-insensitively on every OS |
| Text encoding | UTF-8, with Latin-1 fallback |
| Malformed / unreadable files | Listed in a separate error table; batch processing continues |
| A phase that cannot be built | Reported in the error table as "only N of M phases": a dropped phase is never silent |

## Output

One row per phase in `density_results.csv`, values rounded to 6
significant figures at output time only:

| Column | Content |
|--------|---------|
| `File` | Source file name (with a phase index for multi-phase files) |
| `Formula` | Reduced chemical formula |
| `Space group` | International (Hermann-Mauguin) symbol |
| `a (A)`, `b (A)`, `c (A)` | Lattice parameters (Å) |
| `alpha (deg)`, `beta (deg)`, `gamma (deg)` | Lattice angles |
| `Volume (A^3)` | Unit-cell volume |
| `Z` | Formula units per cell |
| `Cell mass (g/mol)` | Total mass of the unit-cell content |
| `Density (g/cm^3)` | Theoretical density |

The table shown in the notebook is deliberately narrower than the CSV:
`render_results` displays only source file, space group, cell volume and
theoretical density, rounded for reading. The CSV always keeps all the
columns above at full precision, so nothing is lost by the compact view.

## Method

The theoretical density of a crystalline phase follows directly from the
refined unit-cell content:

$$\rho = \frac{m_\text{cell}}{V_\text{cell}} = \frac{\sum_i o_i\, M_i}{N_A \cdot V_\text{cell}}$$

where the sum runs over all atomic sites $i$ in the unit cell, $o_i$ is
the site occupancy, $M_i$ the standard atomic weight (g mol⁻¹),
$V_\text{cell}$ the unit-cell volume and
$N_A = 6.022\,140\,76 \times 10^{23}\ \text{mol}^{-1}$ the Avogadro
constant (exact by definition since the 2019 revision of the SI). Partial
site occupancies (vacancies, dopants, mixed sites) are therefore included
rigorously.

## Validation and testing

The validation suite [`test_cif_density.py`](test_cif_density.py)
generates six synthetic test files at run time from published lattice
parameters - no experimental data is shipped or required - and runs the
whole pipeline on them:

```bash
pip install pytest
pytest
```

Run `pytest` without a path: `pyproject.toml` sets `--doctest-modules`, so
a bare run also executes the `>>>` examples in `cif_density.py`. Naming the
test file explicitly skips them.

| Case | Purpose |
|------|---------|
| NaCl (rock salt, a = 5.6402 Å) | Symmetry expansion from the space-group symbol |
| Si (diamond, a = 5.43095 Å, P1 setting) | Explicit atom list without symmetry operators |
| CeO₂ in a GSAS-II-style multi-block file | Filtering of non-structural data blocks |
| CeO₂ with 12.5 % oxygen vacancies | Partial occupancies in the density |
| Defect fluorite (La,Y)₂Zr₂O₇ | Several cations sharing one site at fractional occupancy |
| A deliberately corrupt file | Error isolation (the batch must not stop) |

Two independent tolerance levels are asserted:

1. **Internal self-consistency** (< 10⁻⁸ relative): the reported density
   must equal ρ = m_cell / (N_A · V) recomputed from the reported cell
   mass and volume (see [Numerical precision](#numerical-precision) for
   the origin of the residual ~10⁻⁹ deviation).
2. **Accuracy** (< 0.2 % relative): agreement with densities
   hand-calculated from IUPAC standard atomic weights, fully independently
   of pymatgen.

The suite is a standard pytest module, so it can run in any CI pipeline.
Section 2 of the notebook additionally provides a quick self-check (one
synthetic NaCl structure compared against its hand-calculated density) for
environments without pytest, e.g. Google Colab; it raises
`AssertionError` on failure, so a headless run
(`jupyter nbconvert --execute`) cannot pass silently either.

## Numerical precision

All calculations are carried out in IEEE-754 double precision (relative
machine epsilon ≈ 2.2 × 10⁻¹⁶). No intermediate rounding is performed
anywhere in the pipeline; values are rounded only when written to the
output table (6 significant figures). The dominant sources of uncertainty
in a computed density are therefore experimental, not computational:
refined lattice parameters (typically known to 10⁻⁴-10⁻⁵ relative) and
site occupancies limit the physically meaningful precision to far fewer
digits than double-precision arithmetic provides.

One subtlety is made explicit rather than hidden: pymatgen converts atomic
masses to grams through the CODATA value of the atomic mass constant,
whereas the textbook formula above divides by the exact Avogadro constant.
Since the 2019 SI redefinition these two routes are no longer identical by
definition; they differ by the molar-mass-constant correction, about
3 × 10⁻¹⁰ relative. The self-consistency tolerance of 10⁻⁸ covers this
constant difference plus floating-point rounding (< 10⁻¹⁵) - both utterly
negligible against experimental uncertainty, but quantified instead of
assumed.

## Privacy: nothing private gets published

No experimental or personal data is included in this repository, and none
must ever be committed or published. Three layers enforce this:

1. **Ignored paths** - `cif_files/`, `*.cif`, `density_results.csv` and
   `*.csv` are excluded via [`.gitignore`](.gitignore); the validation
   suite and the notebook self-check use only synthetic structures
   generated in temporary directories.
2. **Stripped notebook outputs** - executed cells embed their results
   (tables, file names) inside the `.ipynb` file. Strip them before every
   commit:

   ```bash
   jupyter nbconvert --clear-output --inplace CIF_Density_Calculator.ipynb
   ```

3. **Automatic strip on commit (recommended)** - install
   [nbstripout](https://github.com/kynan/nbstripout) once per clone and
   git will strip outputs transparently at commit time, so a forgotten
   manual strip can never leak data:

   ```bash
   pip install nbstripout
   nbstripout --install        # run inside the git repository
   ```

## How to cite

See [`CITATION.cff`](CITATION.cff) (GitHub shows a "Cite this repository"
button). For a permanent, versioned DOI, archive a tagged release on
[Zenodo](https://zenodo.org).

Please also cite the libraries this notebook relies on:

- S. P. Ong *et al.*, "Python Materials Genomics (pymatgen): A robust,
  open-source python library for materials analysis", *Comput. Mater.
  Sci.* **68**, 314-319 (2013),
  doi:[10.1016/j.commatsci.2012.10.028](https://doi.org/10.1016/j.commatsci.2012.10.028)
- A. Togo & I. Tanaka, "Spglib: a software library for crystal symmetry
  search", [arXiv:1808.01590](https://arxiv.org/abs/1808.01590) (2018)

Reference data used by the validation section:

- IUPAC Commission on Isotopic Abundances and Atomic Weights, *Standard
  atomic weights of the elements 2021*
- BIPM, *The International System of Units (SI)*, 9th edition (2019) -
  exact value of the Avogadro constant

## AI assistance

This software was developed with the assistance of Claude (Anthropic):
the initial version with Claude Fable, later revisions with Claude Opus.
Every change was supervised and reviewed by the author, who remains
solely responsible for the method, the validation suite and any result
published using this software.

## License

MIT - see [`LICENSE`](LICENSE).
