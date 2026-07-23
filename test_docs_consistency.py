"""Guard the README and docs against silent drift from the engine.

The docs are the user-facing spec (see CLAUDE.md): the CSV column list and
the release version live there as prose, so they can fall out of step with
the code. These tests tie them back to the engine and fail if they diverge.
"""
import re
from pathlib import Path

from pymatgen.core import Lattice, Structure

import cif_density
from cif_density import density_record

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"


def engine_columns() -> list[str]:
    """The exact CSV column order the engine produces, from a real record."""
    nacl = Structure(Lattice.cubic(5.6402), ["Na", "Cl"],
                     [[0, 0, 0], [0.5, 0.5, 0.5]])
    return list(density_record(nacl).keys())


def test_output_doc_lists_every_engine_column():
    """docs/output.md must document exactly the CSV columns, in order.

    Each column is the first backtick-quoted token on its table row, so a
    renamed, reordered, added or dropped column breaks this immediately.
    """
    text = (DOCS / "output.md").read_text(encoding="utf-8")
    documented = re.findall(r"^\|\s*`([^`]+)`", text, flags=re.MULTILINE)
    assert documented == engine_columns()


def test_citation_version_matches_engine():
    """CITATION.cff and __version__ are a matched pair (CLAUDE.md)."""
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pattern = rf'(?m)^version:\s*["\']?{re.escape(cif_density.__version__)}\b'
    assert re.search(pattern, cff), f"CITATION.cff version != {cif_density.__version__}"
