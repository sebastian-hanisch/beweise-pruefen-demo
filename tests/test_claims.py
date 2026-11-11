"""Jede Zahl der README an festen Formeln und Zufalls-Seeds (SplitMix64, ganzzahlige Zähler: auf jeder Plattform dieselben Werte, deshalb exakte Vergleiche).

Gemessen wird in Konflikten, Protokollzeilen, Prüfschritten (geprüfte Klauseln des Prüfers) und Propagationen des Lösers, nie in Sekunden. Messreihen: je n die ersten 20 unerfüllbaren
Zufalls-3-SAT-Formeln ab Zufalls-Seed 7000 (m = 4,26 n), Schubfach eine feste Formel je h, Solidität 25 feste Formeln n = 30, m = 100 (Zufalls-Seeds 1200 bis 1224).
Die vorgerechneten Zeilen (n = 60 bis 80 und Schubfach h = 7) liegen in `bwp_messreihen.json`; ihre Neumessung läuft hier für n = 60 bis 80 und h = 7 ohne Löschzeilen (Löser);
die vollständige Neumessung von h = 7 mit Prüfer (rund eine Minute) und mit Löschzeilen prüft `BWP_LANGSAM=1 pytest tests/test_claims.py -k vorgerechnet`."""

import functools
import json
import os
from pathlib import Path
from statistics import median

import pytest

import bwp_algorithm as A
import bwp_constants as C
import bwp_evaluation as ev
import bwp_pruefer as P
import bwp_scenario as S
from bwp_cdcl import solve

ROOT = Path(__file__).resolve().parent.parent
LANGSAM = os.environ.get("BWP_LANGSAM") == "1"


@functools.lru_cache(maxsize=None)
def zufall_reihe():
    return {z["n"]: z for z in A.messreihe_zufall()}


@functools.lru_cache(maxsize=None)
def schubfach_reihe():
    return {z["h"]: z for z in A.messreihe_schubfach()}


@functools.lru_cache(maxsize=None)
def sol_reihe():
    return A.soliditaet_reihe()


@functools.lru_cache(maxsize=None)
def vorgerechnet():
    return json.loads((ROOT / C.MESSREIHEN_DATEI).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------------------------------ Handbeispiel PHP(2)

def test_claim_handbeispiel_beweis_a_bis_e(php2, beweis):
    b = P.pruefe_protokoll(php2[1], beweis)
    assert b.ok and [z.schritte for z in b.zeilen] == [12, 13, 13, 14, 14] and b.schritte == 66


def test_claim_handbeispiel_loeser_schreibt_zwei_zeilen_mit_44_pruefschritten():
    l = A.lauf(S.php2())
    assert l.protokoll == (("a", (-2,)), ("a", ())) and l.stat["konflikte"] == 2 and l.befund.schritte == 44


def test_claim_handbeispiel_loeschzeile_klausel_4_macht_zeile_c_unbeweisbar(php2, beweis):
    b = P.pruefe_protokoll(php2[1], beweis[:2] + [("d", (-1, -3))] + beweis[2:])
    assert not b.ok and b.fehler_zeile == 4


def test_claim_handbeispiel_hinweise_19_gelesene_klauseln_gegen_66_pruefschritte():
    bsp = A.hinweis_beispiel("hand", "normal")
    assert sum(z["gelesen"] for z in bsp["je_zeile"]) == 19 and bsp["suche"].schritte == 66 and bsp["hinweis"]["ok"]
    erzeugt = A.hinweis_beispiel("suche", "normal")
    assert [z["hinweise"] for z in erzeugt["je_zeile"]] == [[5, 9, 3], [6, 8, 3], [4, 10, 2], [7, 11, 2], [12, 13, 1]]
    assert sum(z["gelesen"] for z in erzeugt["je_zeile"]) == 15


# ------------------------------------------------------------------------------------------------------------------------------ Solidität

def test_claim_solidaet_g_sieben_modelle_und_15_0_0_45(g_formel):
    n, kl = g_formel
    assert len(A.modelle(n, kl)) == 7
    t = A.soliditaet(n, kl, A.alle_zweierklauseln(n))
    assert t.zellen() == (15, 0, 0, 45)
    assert ev.verdict_soliditaet(t.zellen())[0] == "success"


def test_claim_solidaet_zufallsformeln_n30():
    r = sol_reihe()
    assert (r["formeln"], r["erfuellbar"], r["kandidaten"]) == (25, 25, 857)
    assert r["nach_art"] == {"zufällig": [20, 0, 154, 575], "Resolvente": [108, 0, 0, 0]}
    assert r["gesamt"] == [128, 0, 154, 575] and r["fehler"] == []
    assert sum(r["nach_art"]["zufällig"]) == 749


# ------------------------------------------------------------------------------------------------------------------------------ Beweisgröße

ZUFALL = {
    # n: (Klauseln, Versuche, Konflikte Median, min, max, Zeilen Median, gelernte Literale Median, Prüfschritte Median, Schritte je Propagation Median, min, max)
    30: (128, 63, 22.5, 13, 35, 22.5, 70.0, 9312.5, "39,9", "33,0", "45,7"),
    40: (170, 66, 43.0, 24, 70, 43.0, 164.0, 26481.5, "48,2", "41,2", "53,8"),
    50: (213, 55, 62.5, 23, 112, 62.5, 294.5, 51465.0, "56,9", "51,2", "62,9"),
}


@pytest.mark.parametrize("n", list(ZUFALL))
def test_claim_beweisgroesse_zufall_live(n):
    z = zufall_reihe()[n]
    kl, versuche, k, kmin, kmax, zeilen, lit, schritte, sp, spmin, spmax = ZUFALL[n]
    assert (z["klauseln"], z["versuche"], z["konflikte"], z["konflikte_min"], z["konflikte_max"]) == (kl, versuche, k, kmin, kmax)
    assert (z["zeilen"], z["lemma_literale"], z["schritte"]) == (zeilen, lit, schritte)
    assert (ev.de(z["schritte_je_propagation"], 1), ev.de(z["schritte_je_propagation_min"], 1), ev.de(z["schritte_je_propagation_max"], 1)) == (sp, spmin, spmax)
    assert z["formeln"] == z["ok"] == 20 and z["alle_ok"]
    assert z["zeilen_je_konflikt_min"] == z["zeilen_je_konflikt_max"] == z["zeilen_je_konflikt"] == 1.0       # genau eine Zeile je Konflikt in allen 20 Protokollen


def test_claim_beweisgroesse_schritte_je_propagation_in_den_medianen_wachsend_von_n30_bis_n80():
    live = zufall_reihe()
    werte = [live[n]["schritte_je_propagation"] for n in (30, 40, 50)] + [z["schritte_je_propagation"] for z in vorgerechnet()["zufall"]]
    assert all(b > a for a, b in zip(werte, werte[1:])) and [ev.de(w, 1) for w in werte] == ["39,9", "48,2", "56,9", "64,5", "72,6", "83,1"]


def test_claim_beweisgroesse_vorgerechnet_n60_bis_n80_gleicht_der_neumessung():
    vor = {z["n"]: z for z in vorgerechnet()["zufall"]}
    assert set(vor) == {60, 70, 80}
    for n, z in vor.items():
        neu = A.messreihe_zufall((n,), C.FORMELN_JE_N)[0]
        for key in ("klauseln", "formeln", "versuche", "ok", "konflikte", "konflikte_min", "konflikte_max", "zeilen", "lemma_literale", "schritte", "schritte_je_propagation", "seeds"):
            assert z[key] == neu[key], (n, key)
    assert [vor[n]["konflikte"] for n in (60, 70, 80)] == [100.5, 140.5, 201.5]
    assert [vor[n]["schritte"] for n in (60, 70, 80)] == [104611.5, 179726.5, 331995.5]


def test_claim_vormessung_n50_m213_seeds_0_bis_29_neu_gemessen():
    """Die Phase-0-Messung (Python-random, 11 Formeln, Median 55,6 Schritte je Propagation) gilt als überholt: Mit SplitMix64-Formeln sind es 10 unerfüllbare Formeln von 30,
    alle mit höchstens 120 Konflikten und alle akzeptiert."""
    werte = []
    for seed in range(30):
        m = A.messe_formel(S.zufallsformel(50, seed))
        if m is not None:
            werte.append(m)
    assert len(werte) == 10 and all(w["ok"] and w["konflikte"] <= 120 for w in werte)
    assert median(w["zeilen"] / w["konflikte"] for w in werte) == 1.0
    assert ev.de(median(w["schritte"] / w["propagationen"] for w in werte), 1) == "57,7"
    assert sorted(w["konflikte"] for w in werte) == [48, 53, 57, 59, 60, 63, 72, 76, 78, 99]


# ------------------------------------------------------------------------------------------------------------------------------ Schubfach

SCHUBFACH = {
    # h: (Variablen, Klauseln, Konflikte, gelernte Literale, Prüfschritte, Propagationen, max. lebend)
    3: (12, 22, 7, 12, 435, 55, 29),
    4: (20, 45, 28, 103, 4788, 297, 73),
    5: (30, 81, 159, 1283, 64154, 1827, 240),
    6: (42, 133, 1004, 13600, 1654563, 13097, 1137),
}
SCHUBFACH_MIT = {
    # h: (Konflikte, Zeilen, Löschzeilen, gelernte Literale, Prüfschritte, max. lebend)
    3: (7, 7, 0, 12, 435, 29),
    4: (28, 28, 0, 103, 4788, 73),
    5: (167, 212, 45, 1307, 64896, 203),
    6: (2428, 4708, 2280, 33104, 1786925, 351),
}


@pytest.mark.parametrize("h", list(SCHUBFACH))
def test_claim_schubfach_ohne_loeschen(h):
    z = schubfach_reihe()[h]
    o = z["ohne"]
    assert (z["variablen"], z["klauseln"]) == SCHUBFACH[h][:2]
    assert (o["konflikte"], o["lemma_literale"], o["schritte"], o["propagationen"], o["max_lebend"]) == SCHUBFACH[h][2:]
    assert o["zeilen"] == o["konflikte"] and o["loeschzeilen"] == 0 and o["ok"]


@pytest.mark.parametrize("h", list(SCHUBFACH_MIT))
def test_claim_schubfach_mit_loeschzeilen_takt_100(h):
    m = schubfach_reihe()[h]["mit"]
    assert C.LOESCH_TAKT == 100
    assert (m["konflikte"], m["zeilen"], m["loeschzeilen"], m["lemma_literale"], m["schritte"], m["max_lebend"]) == SCHUBFACH_MIT[h] and m["ok"]
    assert m["zeilen"] == m["konflikte"] + m["loeschzeilen"]


def test_claim_schubfach_faktoren_je_loch_und_loeschzeilen_vergleich():
    konflikte = [schubfach_reihe()[h]["ohne"]["konflikte"] for h in (3, 4, 5, 6)] + [vorgerechnet()["schubfach"][0]["ohne"]["konflikte"]]
    assert konflikte == [7, 28, 159, 1004, 4811]
    assert [ev.de(b / a, 1) for a, b in zip(konflikte, konflikte[1:])] == ["4,0", "5,7", "6,3", "4,8"]
    s6 = schubfach_reihe()[6]
    assert s6["mit"]["konflikte"] > s6["ohne"]["konflikte"] and s6["mit"]["max_lebend"] < s6["ohne"]["max_lebend"] and s6["mit"]["schritte"] > s6["ohne"]["schritte"]


def test_claim_schubfach_h7_vorgerechnet_in_sich_stimmig_und_loeser_gleicht_der_neumessung():
    z = vorgerechnet()["schubfach"][0]
    assert (z["h"], z["variablen"], z["klauseln"], z["vorgerechnet"]) == (7, 56, 204, True)
    o, m = z["ohne"], z["mit"]
    assert (o["konflikte"], o["zeilen"], o["lemma_literale"], o["schritte"], o["propagationen"], o["max_lebend"], o["ok"]) == (4811, 4811, 93191, 32802504, 63653, 5015, True)
    assert (m["konflikte"], m["zeilen"], m["loeschzeilen"], m["lemma_literale"], m["schritte"], m["propagationen"], m["max_lebend"], m["ok"]) == (47374, 94529, 47155, 910398, 48482118, 702550, 454, True)
    assert m["zeilen"] == m["konflikte"] + m["loeschzeilen"] and vorgerechnet()["budget"] == C.BUDGET_VORGERECHNET == 100000
    f = S.schubfach(7)
    assert solve(f.n, [list(c) for c in f.klauseln]).stat["konflikte"] == 4811            # der Löser ohne Prüfer (einige Sekunden)


@pytest.mark.skipif(not LANGSAM, reason="BWP_LANGSAM=1: Prüfer auf 4.811 und 94.529 Zeilen")
def test_claim_schubfach_h7_vorgerechnet_gleicht_der_neumessung():
    z = vorgerechnet()["schubfach"][0]
    f = S.schubfach(7)
    assert A.messe_formel(f, False, budget=C.BUDGET_VORGERECHNET) == z["ohne"]
    assert A.messe_formel(f, True, budget=C.BUDGET_VORGERECHNET) == z["mit"]


# ------------------------------------------------------------------------------------------------------------------------------ Presets

def test_claim_preset_kleine_zufallsformel_und_schubfach_h5():
    g = ev.formel_von(ev.Settings(**C.PRESETS["Kleine Zufallsformel (n = 20)"]))
    l = A.lauf(g.formel)
    assert (g.seed_benutzt, len(g.formel.klauseln), l.stat["konflikte"], len(l.protokoll), l.befund.schritte) == (7001, 85, 22, 22, 5404)
    s = A.lauf(S.schubfach(5))
    assert (len(s.protokoll), s.befund.schritte) == (159, 64154)
    sm = A.lauf(S.schubfach(5), True)
    assert (len(sm.protokoll), sm.stat["konflikte"], sm.befund.schritte) == (212, 167, 64896)


def test_claim_kern_loeschtakt_2000_gaebe_bis_h6_keine_loeschzeile():
    for h in (3, 4, 5, 6):
        e = A.loese(S.schubfach(h), True, takt=2000)
        assert e.stat["konflikte"] < 2000 and not any(a == "d" for a, _ in e.beweis)
