"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b): das Handbeispiel PHP(2).

PHP(2): 3 Tauben, 2 Löcher; x1 = (Taube 1, Loch 1), x2 = (1, 2), x3 = (2, 1), x4 = (2, 2), x5 = (3, 1), x6 = (3, 2). Neun Klauseln, unerfüllbar.
Beweis von Hand A bis E: (¬x1 ∨ ¬x4), (¬x2 ∨ ¬x3), (¬x1), (¬x2), ()."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Handwerte unabhängig von bwp_scenario und bwp_constants (aus dem Handbeispiel abgeschrieben, nicht aus dem Code gelesen)
PHP2_KLAUSELN = [(1, 2), (3, 4), (5, 6), (-1, -3), (-1, -5), (-3, -5), (-2, -4), (-2, -6), (-4, -6)]
BEWEIS_AE = [("a", (-1, -4)), ("a", (-2, -3)), ("a", (-1,)), ("a", (-2,)), ("a", ())]


@pytest.fixture
def php2():
    return 6, list(PHP2_KLAUSELN)


@pytest.fixture
def g_formel():
    """G = PHP(2) ohne (x3 x4) und (x5 x6): erfüllbar, 7 Modelle von 64."""
    return 6, [c for c in PHP2_KLAUSELN if c not in ((3, 4), (5, 6))]


@pytest.fixture
def beweis():
    return list(BEWEIS_AE)
