"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bkr_scenario import adjacency_from_edges  # noqa: E402


@pytest.fixture
def mini():
    """5 Sendungen: das Dreieck {0, 1, 2}, der Pendelknoten 3 an 2, der isolierte Knoten 4.
    Von Hand: maximale Cliquen {0,1,2}, {2,3}, {4}. Aufrufe: ohne Pivot 11, mit Pivot 6, mit Degeneracy-Ordnung [4,3,0,1,2] (d = 2) 8;
    Auswahlkosten des Pivots 14."""
    return adjacency_from_edges(5, [(0, 1), (0, 2), (1, 2), (2, 3)])
