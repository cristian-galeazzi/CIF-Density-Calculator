# CIF Density Calculator

Give it a folder of CIF files, the standard output of a crystal-structure
refinement, and it returns the theoretical density of every phase inside
them, as a table you can read and a CSV you can reuse. It runs as a
Jupyter notebook, so no programming experience is needed: open it, drop
your files in a folder, press run.

## Quick start

No terminal required. If Python and a notebook editor are already set up,
start at step 3.

1. **Install Python** (version 3.11 or newer). On Windows, download the
   installer from [python.org](https://www.python.org/downloads/) and tick
   **Add python.exe to PATH** on the first screen; that checkbox is easy
   to miss and everything else assumes it. macOS and Linux usually ship a
   suitable Python already.

2. **Install a notebook editor.** [VS Code](https://code.visualstudio.com/)
   is free, works the same on Windows, macOS and Linux, and needs its
   Python and Jupyter extensions, which it offers to install the first
   time you open a notebook.

3. **Download this repository**: the green *Code* button above, then
   *Download ZIP*, then unzip it somewhere you can find again.

4. **Open `CIF_Density_Calculator.ipynb`** in VS Code, put your `.cif`
   files in the `cif_files/` folder next to it, and press *Run All*.

The first cell installs pymatgen and pandas if they are missing, so there
is nothing to install by hand. Results appear as a table under the last
cell and are written to `density_results.csv` in the same folder, which
opens in Excel or any spreadsheet.

If you would rather use a terminal, `pip install -r requirements.txt`
installs everything in one step and the notebook opens in any Jupyter
host. Tested on Python 3.11 and 3.14, with pymatgen 2026.5.4 and pandas
3.0.3.

The notebook has three cells: setup, an optional self-check against one
synthetic NaCl structure, and the batch run, which processes every CIF in
`cif_files/` and writes the CSV. `INPUT_FOLDER` and `OUTPUT_CSV`, set in
the last cell, default to `"cif_files"` and `"density_results.csv"`.

### Working in VS Code

*Select Kernel*, at the top right of the notebook, chooses which Python
runs it. If a package looks missing even though it installed a moment
ago, the notebook is almost always running on a different Python than the
one that received it; pick the other kernel and run again.

Keep `cif_density.py` in the same folder as the notebook. The notebook
imports the calculation from it rather than containing it, so on its own
it does nothing. Downloading the ZIP keeps them together.

### Working in Google Colab

**Colab means uploading your structures to Google.** Every CIF dragged
into the Files sidebar leaves your machine and is processed on someone
else's infrastructure, which an embargo, a group policy or a collaboration
agreement may not allow. Check before you upload, not after. Colab suits
published or synthetic structures; for your own unpublished ones, run
locally instead, it costs one `pip install` and keeps the files where they
are.

If that is settled: upload **both** `CIF_Density_Calculator.ipynb` and
`cif_density.py` (the notebook through *File → Upload notebook*, the
module through the *Files* sidebar) and run all cells. The `cif_files`
folder is created automatically; drag your CIF files into it and re-run
the last cell.

## What you get

One row per phase in `density_results.csv`. The theoretical density comes
second, straight after the file name, because it is the result the file
exists for; everything after it is context.

| Column | Content |
|--------|---------|
| `File` | Source file name (multi-phase files carry the structural-block index, so it still points at the right block when one is skipped) |
| `Density (g/cm^3)` | Theoretical density |
| `Formula` | Reduced chemical formula |
| `Cell composition` | Element amounts in the unit cell, unreduced |
| `Space group` | International (Hermann-Mauguin) symbol |
| `Space group number` | International number, unambiguous where the symbol depends on the setting |
| `Crystal system` | cubic, tetragonal, monoclinic and so on |
| `a (A)` | Lattice parameter a (Å) |
| `b (A)` | Lattice parameter b (Å) |
| `c (A)` | Lattice parameter c (Å) |
| `alpha (deg)` | Lattice angle alpha (°) |
| `beta (deg)` | Lattice angle beta (°) |
| `gamma (deg)` | Lattice angle gamma (°) |
| `Volume (A^3)` | Unit-cell volume |
| `Z` | Formula units per cell |
| `Sites per cell` | Crystallographic sites, not atoms: on a partially occupied structure the two differ, and the difference is the vacancy count |
| `Cell mass (g/mol)` | Total mass of the unit-cell content |
| `Molar volume (cm^3/mol)` | Volume per formula unit |

**Reduced formula or cell composition?** `Formula` is compact and familiar,
but pymatgen picks its own normalisation for each phase, so a fluorite and
a pyrochlore of the same material can print on different bases and look
like different compounds. `Cell composition` is always the content of one
unit cell, which keeps phases comparable. Both are given because neither
is right for every question.

Numbers are written at 6 significant figures, a property of the file, not
of the calculation: nothing is rounded before this point, and 6 figures is
already beyond what a refined lattice parameter supports. The notebook
table is narrower still, showing only file, space group, cell volume and
density.

## What it accepts

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
| A phase that cannot be built | Reported in the error table as "N phase(s) skipped by pymatgen", with the block number: a dropped phase is never silent |

## Limitations

What this tool computes is the *theoretical* density, also called
*crystallographic* density, or *X-ray density* when the unit cell comes
from a refinement against X-ray diffraction data: the mass of the refined
unit cell divided by its volume. The arithmetic does not know what
produced the cell, so a structure refined from neutron data or relaxed by
DFT is treated identically, which is why the IUCr core dictionary stores
this quantity as `_exptl_crystal_density_diffrn` rather than under an
X-ray-specific name. It is not a measured density, and this tool does not
compute *relative* density (measured / theoretical): that would need an
experimental value, e.g. from Archimedes weighing, which falls outside
what this repository sets out to do.

No tool can check a refinement against reality; that would mean knowing
the true structure already. A wrong occupancy in the CIF therefore becomes
a wrong density, silently. One case is caught: an element declared in the
CIF but never placed is reported, since that leaves the density too low.
The arithmetic is validated; the crystallography remains yours.

## How it works and how it was checked

Density follows from the refined unit cell:

$$\rho = \frac{m_\text{cell}}{V_\text{cell}} = \frac{\sum_i o_i\, M_i}{N_A \cdot V_\text{cell}}$$

$o_i$ is the site occupancy, $M_i$ the standard atomic weight (g mol⁻¹),
$V_\text{cell}$ the unit-cell volume and
$N_A = 6.022\,140\,76 \times 10^{23}\ \text{mol}^{-1}$ the Avogadro
constant (exact since the 2019 SI revision). Partial occupancies
(vacancies, dopants, mixed sites) are included rigorously.

Everything runs in double precision (machine epsilon ≈ 2.2 × 10⁻¹⁶),
unrounded until the CSV is written at 6 significant figures. One
exception never touches the density: element amounts are rounded to two
decimals before `Formula` and `Z` are derived, so a site at 0.9998 does
not produce an absurd formula; `Cell composition`, `Cell mass` and the
density itself keep the raw amounts. A second, smaller effect: pymatgen
converts atomic mass to grams via the CODATA atomic mass constant, while
the formula above divides by the exact Avogadro constant. Since the 2019
SI redefinition these are no longer identical, differing by about
1.05 × 10⁻⁹ relative with the CODATA 2022 value, a figure that follows
CODATA revisions and is worth recomputing rather than quoting.

[`test_cif_density.py`](test_cif_density.py) generates six synthetic test
files at run time and runs the whole pipeline on them:

```bash
pytest
```

Run it without a path: `pyproject.toml`'s `--doctest-modules` also runs
the `>>>` examples in `cif_density.py`; naming the file explicitly skips
them.

| Case | Purpose |
|------|---------|
| NaCl (rock salt, a = 5.6402 Å) | Symmetry expansion from the space-group symbol |
| Si (diamond, a = 5.43095 Å, P1 setting) | Explicit atom list without symmetry operators |
| CeO₂ in a GSAS-II-style multi-block file | Filtering of non-structural data blocks |
| CeO₂ with 12.5 % oxygen vacancies | Partial occupancies in the density |
| Defect fluorite (La,Y)₂Zr₂O₇ | Several cations sharing one site at fractional occupancy |
| A deliberately corrupt file | Error isolation (the batch must not stop) |

Two tolerances are checked: internal self-consistency (< 10⁻⁸ relative,
density must equal ρ = m_cell / (N_A · V) recomputed from the reported
mass and volume; the ~10⁻⁹ residual is the CODATA correction above plus
floating-point rounding < 10⁻¹⁵), and accuracy (< 0.2 % relative, against
densities hand-calculated from IUPAC standard atomic weights, independent
of pymatgen). The notebook also carries a self-check (one NaCl structure)
for environments without pytest, e.g. Colab, raising `AssertionError` on
failure so a headless run cannot pass silently.

## Project layout

`cif_density.py` is the calculation engine, importable from scripts and
other notebooks. `CIF_Density_Calculator.ipynb` is only the user
interface. `test_cif_density.py` is the validation suite, run with
`pytest`, synthetic data only.

## Privacy: nothing private gets published

No experimental or personal data is included in this repository, and none
must ever be committed or published. Three layers enforce this:

1. **Ignored paths** - `cif_files/`, `*.cif`, `density_results.csv` and
   `*.csv` are excluded via [`.gitignore`](.gitignore); the validation
   suite and the notebook self-check use only synthetic structures.
2. **Stripped notebook outputs** - executed cells embed their results
   (tables, file names) inside the `.ipynb` file. Strip them before every
   commit:

   ```bash
   jupyter nbconvert --clear-output --inplace CIF_Density_Calculator.ipynb
   ```

3. **Automatic strip on commit (recommended)** - install
   [nbstripout](https://github.com/kynan/nbstripout) once per clone so git
   strips outputs transparently at commit time, and a forgotten manual
   strip can never leak data:

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
