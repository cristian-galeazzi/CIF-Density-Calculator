# What it accepts

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
