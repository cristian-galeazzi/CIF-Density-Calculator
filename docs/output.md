# Output columns

One row per phase in `density_results.csv`. The theoretical density comes
second, straight after the file name, because it is the result the file exists
for; everything after it is context.

| Column | Content |
|--------|---------|
| `File` | Source file name (multi-phase files carry the structural-block index, so it still points at the right block when one is skipped) |
| `Density (g/cm^3)` | Theoretical density |
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

## Why the composition is not reduced

A reduced formula is compact, and earlier versions reported one, but it has two
failings that matter here. It is normalised per phase, so two polymorphs of the
same material print on different bases and look like different compounds. Worse,
it has to be built from rounded occupancies to stay readable, and rounding
deletes a trace dopant: a refinement with Ce at 0.999 and Gd at 0.001 came out
as `CeO2`, with the gadolinium still in the mass and the density. The unreduced
cell composition reports `Ce3.996 Gd0.004 O8` and cannot hide anything the mass
contains.

## Precision of the written numbers

Numbers are written at 6 significant figures, a property of the file, not of
the calculation: nothing is rounded before this point, and 6 figures is already
beyond what a refined lattice parameter supports. The notebook table is
narrower still, showing only file, space group, cell volume and density.
