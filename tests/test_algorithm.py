"""Einheiten der Demo an Mini-Instanzen von Hand (DEMO-PLAYBOOK §1b): Handbeispiel PHP(2), erfüllbare Formel G, Prüfschritte, Wahrheit, Solidität, Manipulation, Messzeilen."""

import pytest

import bwp_algorithm as A
import bwp_constants as C
import bwp_scenario as S
from bwp_rup import ist_rup, pruefe_beweis


# ------------------------------------------------------------------------------------------------------------------------------ Prüfschritte von Hand ausgezählt

def test_pruefschritte_des_handbeispiels_von_hand_ausgezaehlt(php2, beweis):
    """Jede angesehene Klausel ist ein Schritt. Zeile A: 1. Durchlauf 9 Klauseln (4: ¬x3, 5: ¬x5, 7: ¬x2, 9: ¬x6), 2. Durchlauf Klausel 1, 2, 3 (verletzt) = 12.
    B = 13, C = 13, D = 14, E = 14 (ebenso gezählt), zusammen 66."""
    from bwp_pruefer import pruefe_protokoll
    b = pruefe_protokoll(php2[1], beweis)
    assert [z.schritte for z in b.zeilen] == [12, 13, 13, 14, 14] and b.schritte == 66
    assert pruefe_beweis([list(c) for c in php2[1]], beweis)[2] == 66


def test_protokoll_des_loesers_fuer_php2_hat_zwei_zeilen_und_44_pruefschritte(php2):
    """Löser: ¬x2 (die Annahme x2 liefert nach 15 Schritten einen Widerspruch), dann die leere Klausel (29 Schritte)."""
    l = A.lauf(S.php2())
    assert l.antwort is False and l.protokoll == (("a", (-2,)), ("a", ())) and l.stat["konflikte"] == 2
    assert l.befund.ok and l.befund.schritte == 15 + 29 == 44


def test_lemma_literale_und_max_lebend(php2, beweis):
    assert A.lemma_literale(beweis) == 2 + 2 + 1 + 1 + 0
    assert A.max_lebend(php2[1], beweis) == 9 + 5
    assert A.max_lebend(php2[1], [("a", (-1,)), ("d", (-1,)), ("d", (-1, -3))]) == 10


# ------------------------------------------------------------------------------------------------------------------------------ Wahrheit und Solidität an G

def test_g_hat_sieben_modelle_und_die_klausel_a_folgt_nicht(g_formel):
    n, kl = g_formel
    assert len(A.modelle(n, kl)) == 7
    w = A.Wahrheit(n, kl)
    assert w.weg == "aufzaehlung" and not w.folgt((-1, -4)) and w.folgt((1, 2))
    modell = A.gegenbeispiel(n, kl, (-1, -4))
    assert modell[1] and modell[4] and all(any((modell[abs(l)] if l > 0 else not modell[abs(l)]) for l in c) for c in kl)
    assert A.gegenbeispiel(n, kl, (1, 2)) is None


def test_soliditaet_an_g_alle_sechzig_zweierklauseln(g_formel):
    n, kl = g_formel
    kand = A.alle_zweierklauseln(n)
    assert len(kand) == 60
    t = A.soliditaet(n, kl, kand)
    assert t.zellen() == (15, 0, 0, 45) and t.summe == 60 and t.fehler == ()
    assert t.beispiele[(True, True)] == (1, 2) and t.beispiele[(False, False)] == (1, -2)
    assert not ist_rup([list(c) for c in kl], [-1, -4])                      # A wird in G abgelehnt, und sie folgt nicht


def test_wahrheit_loeser_und_aufzaehlung_stimmen_bei_g_ueberein(g_formel):
    n, kl = g_formel
    aufz, loes = A.Wahrheit(n, kl, "aufzaehlung"), A.Wahrheit(n, kl, "loeser")
    assert all(aufz.folgt(c) == loes.folgt(c) for c in A.alle_zweierklauseln(n))
    with pytest.raises(ValueError):
        A.modelle(C.AUFZAEHLUNG_MAX_N + 1, [])


def test_wahrheit_leere_klausel_folgt_nur_aus_unerfuellbarer_formel(php2, g_formel):
    assert A.wahrheit(6, php2[1], ()) is True and A.wahrheit(6, g_formel[1], ()) is False
    assert A.wahrheit(6, php2[1], (), "loeser") is True and A.wahrheit(6, g_formel[1], (), "loeser") is False


def test_zufallskandidaten_sind_deterministisch_und_haben_beide_arten():
    f = S.zufallsformel(30, 1200, 100)
    a, b = A.zufallskandidaten(30, f.klauseln, 60, 11), A.zufallskandidaten(30, f.klauseln, 60, 11)
    assert a == b and {art for art, _ in a} == {"zufällig", "Resolvente"} and len(a) <= 60
    assert a != A.zufallskandidaten(30, f.klauseln, 60, 12)
    assert all(2 <= len(c) <= 3 for art, c in a if art == "zufällig")


# ------------------------------------------------------------------------------------------------------------------------------ Manipulation

def test_manipuliere_jede_art_aendert_genau_eine_stelle(beweis):
    orig = [(a, tuple(c)) for a, c in beweis]
    neu, text, zeile = A.manipuliere(beweis, "kuerzen", 1)
    assert zeile in (1, 2) and len(neu[zeile - 1][1]) == 1 and neu[:zeile - 1] + neu[zeile:] == orig[:zeile - 1] + orig[zeile:] and "gestrichen" in text
    neu, text, zeile = A.manipuliere(beweis, "tauschen", 2)
    assert sum(1 for x, y in zip(neu, orig) if x != y) == 1 and neu[zeile - 1][1] != orig[zeile - 1][1] and len(neu[zeile - 1][1]) == len(orig[zeile - 1][1])
    neu, text, zeile = A.manipuliere(beweis, "vertauschen", 3)
    assert sorted(neu) == sorted(orig) and neu != orig and neu[zeile - 1] == orig[zeile] and neu[zeile] == orig[zeile - 1]
    neu, text, zeile = A.manipuliere(beweis, "loeschen", 4)
    assert len(neu) == 4 and () == neu[-1][1] and orig[zeile - 1] not in neu


def test_manipuliere_ist_deterministisch_und_ohne_passende_zeile_unveraendert():
    assert A.manipuliere(((("a", (1, 2)),) + (("a", ()),)), "kuerzen", 5) == A.manipuliere((("a", (1, 2)), ("a", ())), "kuerzen", 5)
    leer = (("a", ()),)
    for art in C.MANIPULATIONEN:
        neu, text, zeile = A.manipuliere(leer, art, 0)
        assert neu == list(leer) and zeile is None and "unverändert" in text
    with pytest.raises(ValueError):
        A.manipuliere(leer, "unbekannt", 0)


def test_manipuliertes_handprotokoll_an_der_unerfuellbaren_formel(php2, beweis):
    """In PHP(2) folgt jede Klausel, und auch (¬x1 ∨ x4) ist durch Einheitspropagation herleitbar (x1 wahr, x4 falsch: Klausel 4 und 5 erzwingen ¬x3 und ¬x5, Klausel 2 erzwingt x3):
    Ein Manipulationstest an einer unerfüllbaren Formel ist leer. Abgelehnt wird nur, was die Herleitung wirklich bricht: das Weglassen der leeren Klausel."""
    from bwp_pruefer import pruefe_protokoll
    ersetzt = [("a", (-1, 4))] + beweis[1:]
    assert pruefe_protokoll(php2[1], ersetzt).ok
    ohne_a = beweis[1:]                                                     # A weglassen: B, C, D, E bleiben beweisbar (C folgt schon aus der Formel)
    assert pruefe_protokoll(php2[1], ohne_a).ok
    assert not pruefe_protokoll(php2[1], beweis[:-1]).ok


# ------------------------------------------------------------------------------------------------------------------------------ Löser, Suche, Messzeilen

def test_naechste_unerfuellbare_ueberspringt_erfuellbare_formeln():
    treffer = A.naechste_unerfuellbare(30, 7000)
    f, s = treffer
    assert s >= 7000 and f == S.zufallsformel(30, s)
    assert A.solve(f.n, [list(c) for c in f.klauseln]).antwort is False
    for fruehere in range(7000, s):
        assert A.solve(30, [list(c) for c in S.zufallsformel(30, fruehere).klauseln]).antwort is True
    assert A.naechste_unerfuellbare(30, 7000, versuche=0) is None


def test_lauf_erfuellbar_unerfuellbar_und_budget():
    sat = A.lauf(S.formel_g())
    assert sat.antwort is True and sat.modell_ok is True and sat.befund is None
    unsat = A.lauf(S.schubfach(4))
    assert unsat.antwort is False and unsat.befund.ok and len(unsat.protokoll) == unsat.stat["konflikte"] == 28 and unsat.protokoll[-1] == ("a", ())
    nein = A.lauf(S.schubfach(5), budget=3)
    assert nein.antwort is None and nein.befund is None and nein.modell_ok is None


def test_lauf_mit_loeschzeilen_und_handprotokoll():
    mit = A.lauf(S.schubfach(5), loeschen=True)
    assert mit.befund.ok and any(a == "d" for a, _ in mit.protokoll) and len(mit.protokoll) > mit.stat["konflikte"]
    hand = A.lauf_mit_protokoll(S.php2(), [("a", c) for c in C.HB_BEWEIS])
    assert hand.antwort is False and hand.befund.ok and len(hand.protokoll) == 5 and hand.befund.schritte == 66


def test_messe_formel_von_hand_ausgezaehlt():
    """PHP(2): Protokoll (¬x2), () mit 2 Konflikten, 2 Zeilen, 1 gelerntem Literal und 44 Prüfschritten (siehe oben)."""
    r = A.messe_formel(S.php2())
    assert (r["konflikte"], r["zeilen"], r["lemma_literale"], r["schritte"], r["ok"], r["geprueft"], r["loeschzeilen"]) == (2, 2, 1, 44, True, 2, 0)
    assert A.messe_formel(S.formel_g()) is None                              # erfüllbar: kein Beweis
    assert r["propagationen"] > 0 and r["max_lebend"] == 11


def test_zeile_zufall_aggregiert_median_und_spanne_von_hand():
    werte = [{"konflikte": 10, "zeilen": 10, "lemma_literale": 40, "schritte": 500, "propagationen": 10, "ok": True},
             {"konflikte": 30, "zeilen": 30, "lemma_literale": 100, "schritte": 2400, "propagationen": 40, "ok": True},
             {"konflikte": 20, "zeilen": 20, "lemma_literale": 70, "schritte": 1000, "propagationen": 20, "ok": True}]
    z = A.zeile_zufall(30, werte, 5)
    assert (z["formeln"], z["versuche"], z["ok"], z["alle_ok"]) == (3, 5, 3, True)
    assert (z["konflikte"], z["konflikte_min"], z["konflikte_max"], z["zeilen"], z["lemma_literale"], z["schritte"]) == (20, 10, 30, 20, 70, 1000)
    assert (z["schritte_je_propagation"], z["schritte_je_propagation_min"], z["schritte_je_propagation_max"]) == (50, 50, 60)
    assert z["zeilen_je_konflikt"] == 1.0
    leer = A.zeile_zufall(30, [], 7)
    assert leer["formeln"] == 0 and leer["konflikte"] is None and leer["alle_ok"] is False


def test_messreihe_zufall_klein():
    z = A.messreihe_zufall((30,), 3)[0]
    assert z["formeln"] == 3 and z["alle_ok"] and z["zeilen_je_konflikt"] == 1.0 and z["versuche"] >= 3 and len(z["seeds"]) == 3
    assert z["konflikte_min"] <= z["konflikte"] <= z["konflikte_max"]


def test_messreihe_schubfach_klein():
    zeilen = A.messreihe_schubfach((3, 4))
    assert [(z["h"], z["ohne"]["konflikte"], z["ohne"]["zeilen"]) for z in zeilen] == [(3, 7, 7), (4, 28, 28)]
    assert all(z["mit"]["ok"] and z["ohne"]["ok"] for z in zeilen)
    assert (zeilen[0]["variablen"], zeilen[0]["klauseln"]) == (12, 4 + 3 * 6)   # 4 Tauben-Klauseln, je Loch C(4,2) = 6 Paare


def test_scenario_formeln_und_parser():
    assert S.make_formel(C.FAMILIE_ZUFALL, 20, seed=5) == S.zufallsformel(20, 5) and len(S.zufallsformel(20, 5).klauseln) == 85
    assert S.klauselzahl(50) == 213 and S.klauselzahl(30) == 128
    assert S.parse_klausel("-1 -4", 6) == ((-1, -4), None) and S.parse_klausel("¬x1, x4", 6) == ((-1, 4), None)
    assert S.parse_klausel("", 6) == ((), None)
    assert S.parse_klausel("7", 6)[0] is None and S.parse_klausel("a", 6)[0] is None and S.parse_klausel("0", 6)[0] is None
    assert S.klausel_text(()) == "()" and S.klausel_text((-1, 4)) == "¬x1 ∨ x4"
    with pytest.raises(ValueError):
        S.make_formel("unbekannt")
