"""Regressionstests der kopierten Kern-Module `bwp_rng` und `bwp_instanzen` (aus kern/tests/test_rng_instanzen_dpll.py übernommen, Importe auf bwp_ umgestellt)
und ein Stichprobentest des kopierten Lösers `bwp_cdcl` an den Handbeispielen dieser Demo."""

import sys
from pathlib import Path

import pytest

import bwp_instanzen as I
from bwp_cdcl import solve
from bwp_rng import SplitMix64

PROJEKTE = Path(__file__).resolve().parents[2]


def lade_original(ordner, modul):
    pfad = PROJEKTE / ordner
    if not (pfad / f"{modul}.py").exists():
        pytest.skip(f"{ordner}/{modul}.py nicht vorhanden")
    sys.path.insert(0, str(pfad))
    try:
        return __import__(modul)
    finally:
        sys.path.remove(str(pfad))


def test_splitmix_bekannte_werte():
    # Veröffentlichte Referenzwerte der SplitMix64-Konvention für Seed 0 (Vigna)
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    assert SplitMix64(12345).next() == 2454886589211414944


def test_splitmix_gleich_dem_original():
    red = lade_original("reduktionskette-demo", "red_scenario")
    a, b = SplitMix64(99), red.SplitMix64(99)
    for _ in range(50):
        assert a.next() == b.next()
    assert [SplitMix64(7).below(10) for _ in range(1)] == [red.SplitMix64(7).below(10)]


def test_hilfsmethoden():
    g = SplitMix64(5)
    xs = [g.random() for _ in range(1000)]
    assert all(0 <= x < 1 for x in xs) and 0.45 < sum(xs) / 1000 < 0.55
    liste = list(range(20))
    SplitMix64(3).shuffle(liste)
    assert sorted(liste) == list(range(20)) and liste != list(range(20))
    probe = SplitMix64(3).sample(range(50), 7)
    assert len(set(probe)) == 7
    assert SplitMix64(3).sample(range(50), 7) == probe          # deterministisch
    assert SplitMix64(1).randrange(10) == SplitMix64(1).below(10)


def test_rand3_gleich_dem_original_und_praefix():
    red = lade_original("reduktionskette-demo", "red_scenario")
    for n, m, seed in [(5, 3, 7), (30, 128, 11), (60, 270, 4)]:
        assert I.rand3(n, m, seed).klauseln == red.random_formula(n, m, seed)
    kurz, lang = I.rand3(20, 30, 1).klauseln, I.rand3(20, 40, 1).klauseln
    assert lang[:30] == kurz                                      # wächst m, bleiben die früheren Klauseln
    assert all(len({abs(l) for l in c}) == 3 for c in lang)


def test_schubfach_handwerte():
    inst = I.pigeonhole(2)                      # 3 Tauben, 2 Löcher
    assert inst.n == 6
    assert len(inst.klauseln) == 3 + 2 * 3     # 3 Taubenklauseln, je Loch 3 Paare
    assert (1, 2) in inst.klauseln and (-1, -3) in inst.klauseln
    assert solve(inst.n, inst.klauseln).antwort is False


def test_pruefe_modell():
    assert I.pruefe_modell([(1, 2), (-1, 2)], {1: True, 2: True})
    assert not I.pruefe_modell([(1, 2), (-1, -2)], {1: True, 2: True})


def test_schubfach_konfliktzahlen_des_kerns():
    """Kern-README: Schubfach h = 4 / 5 / 6 braucht 28 / 159 / 1 004 Konflikte (deterministisch, ohne Zufall)."""
    for h, konflikte in {4: 28, 5: 159, 6: 1004}.items():
        inst = I.pigeonhole(h)
        assert solve(inst.n, inst.klauseln).stat["konflikte"] == konflikte
