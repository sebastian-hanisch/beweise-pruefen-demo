"""Verdikte als reine Funktionen (`bwp_evaluation.verdict_*`): Schwellen und jede Zahl im Text an handgesetzten Werten."""

import bwp_algorithm as A
import bwp_constants as C
import bwp_evaluation as ev
import bwp_pruefer as P
import bwp_scenario as S


def _zeile(n, formeln=20, ok=20, konflikte=62.5, zeilen=62.5, sp=57.0, sp_min=51.0, sp_max=63.0):
    return {"n": n, "formeln": formeln, "ok": ok, "konflikte": konflikte, "zeilen": zeilen, "zeilen_je_konflikt_min": 1.0, "zeilen_je_konflikt_max": 1.0,
            "schritte_je_propagation": sp, "schritte_je_propagation_min": sp_min, "schritte_je_propagation_max": sp_max}


def test_kernfrage_unerfuellbar_akzeptiert(php2, beweis):
    l = A.lauf_mit_protokoll(S.php2(), beweis)
    kind, text = ev.verdict_kernfrage(l)
    assert kind == "success" and "5 Zeilen (5 hinzugefügte Klauseln)" in text and "66 Prüfschritte" in text and "Löschzeilen" not in text


def test_kernfrage_mit_loeschzeilen_nennt_deren_zahl():
    l = A.lauf(S.schubfach(5), True)
    kind, text = ev.verdict_kernfrage(l)
    n_d = sum(1 for a, _ in l.protokoll if a == "d")
    assert kind == "success" and f"davon {ev.de(n_d)} Löschzeilen" in text and f"{ev.de(len(l.protokoll))} Zeilen" in text


def test_kernfrage_abgelehnt_erfuellbar_und_budget(php2, beweis):
    abgelehnt = A.Lauf(S.php2(), False, {}, tuple(beweis[:-1]), P.pruefe_protokoll(php2[1], beweis[:-1]), None)
    kind, text = ev.verdict_kernfrage(abgelehnt)
    assert kind == "error" and "endet ohne leere Klausel" in text
    sat = A.lauf(S.formel_g())
    kind, text = ev.verdict_kernfrage(sat)
    assert kind == "info" and "7 Klauseln" in text and "Zeuge" in text
    falsch = sat._replace(modell_ok=False)
    assert ev.verdict_kernfrage(falsch)[0] == "error"
    kind, text = ev.verdict_kernfrage(A.lauf(S.schubfach(5), budget=2))
    assert kind == "warning" and "20.000 Konflikten" in text


def test_zeile_akzeptiert_abgelehnt_loeschzeile_tautologie(php2, beweis):
    kl = php2[1]
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, beweis, 1))
    assert kind == "success" and "x1 = wahr, x4 = wahr" in text and "erzwingt die Einheitspropagation 4 Literale" in text and "Klausel 3 (x5 ∨ x6)" in text and "12 Prüfschritte" in text
    schlecht = beweis[:2] + [("d", (-1, -3))] + beweis[2:]
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, schlecht, 4))
    assert kind == "error" and "5 Literale" in text and "keine Klausel wird verletzt" in text
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, schlecht, 3))
    assert kind == "info" and "Klausel 4 (¬x1 ∨ ¬x3)" in text and "Davor lebten 11 Klauseln" in text
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, [("d", (8, 9))] + beweis, 1))
    assert kind == "warning" and "ignoriert" in text
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, [("a", (1, -1))] + beweis, 1))
    assert kind == "info" and "immer wahr" in text
    kind, text = ev.verdict_zeile(P.erklaere_zeile(kl, beweis, 5))
    assert kind == "success" and "nichts (die leere Klausel hat kein Literal)" in text and "verletzt dann die Klausel 1 (x1 ∨ x2)" in text


def test_groesse_nennt_median_spannen_und_schritte_je_propagation():
    kind, text = ev.verdict_groesse([_zeile(30, sp=39.9), _zeile(50)])
    assert kind == "success"
    assert "n = 50" in text and "62,5 Zeilen für 62,5 Konflikte" in text and "1,00 bis 1,00" in text and "57,0 Schritte je Löser-Propagation (Spanne 51,0 bis 63,0)" in text and "alle 20 Protokolle" in text
    assert "bei n = 30 im Median bei 39,9, bei n = 50 bei 57,0" in text
    kind, text = ev.verdict_groesse([_zeile(50, ok=18)])
    assert kind == "error" and "2 von 20" in text
    assert "bei n = 30" not in ev.verdict_groesse([_zeile(50)])[1]                      # eine einzige Zeile: kein Vergleich


def test_soliditaet_erfolg_nur_bei_null_fehlern():
    kind, text = ev.verdict_soliditaet((15, 0, 0, 45))
    assert kind == "success" and "0 von 60 Kandidaten" in text and "15 gefolgerte Klauseln akzeptiert" in text and "0 gefolgerte abgelehnt" in text and "45 nicht gefolgerte abgelehnt" in text
    kind, text = ev.verdict_soliditaet((128, 0, 154, 575), " (25 erfüllbare Formeln)")
    assert kind == "success" and "0 von 857 Kandidaten (25 erfüllbare Formeln)" in text
    kind, text = ev.verdict_soliditaet((15, 2, 0, 43))
    assert kind == "error" and "2 von 60" in text and "FEHLER" in text


def test_klausel_alle_vier_faelle():
    assert ev.verdict_klausel(True, True)[0] == "success" and "richtig" in ev.verdict_klausel(True, True)[1]
    assert ev.verdict_klausel(False, False)[0] == "success" and "folgt nicht" in ev.verdict_klausel(False, False)[1]
    kind, text = ev.verdict_klausel(False, True)
    assert kind == "info" and "strenger als Folgerung" in text
    assert ev.verdict_klausel(True, False)[0] == "error"


def test_manipulation_abgelehnt_und_akzeptiert(php2, beweis):
    schlecht = beweis[:2] + [("d", (-1, -3))] + beweis[2:]
    kind, text = ev.verdict_manipulation(P.pruefe_protokoll(php2[1], schlecht), "Klausel 4 gelöscht")
    assert kind == "success" and "in Zeile 4" in text and "Klausel 4 gelöscht" in text
    kind, text = ev.verdict_manipulation(P.pruefe_protokoll(php2[1], beweis[:-1]), "letzte Zeile weggelassen")
    assert kind == "success" and "am Ende" in text
    kind, text = ev.verdict_manipulation(P.pruefe_protokoll(php2[1], beweis), "nichts")
    assert kind == "info" and "trotzdem" in text and "folgt jede Klausel" in text


def _sz(h, ohne, mit=None):
    return {"h": h, "ohne": ohne, "mit": mit, "vorgerechnet": False}


def _r(konflikte, zeilen=None, d=0, lebend=10, ok=True):
    return {"konflikte": konflikte, "zeilen": zeilen or konflikte, "loeschzeilen": d, "max_lebend": lebend, "ok": ok}


def test_schubfach_faktoren_und_loeschzeilen():
    zeilen = [_sz(3, _r(7), _r(7)), _sz(4, _r(28), _r(28)), _sz(5, _r(159), _r(167, 212, 45, 203))]
    zeilen[2]["ohne"]["max_lebend"] = 240
    kind, text = ev.verdict_schubfach(zeilen)
    assert kind == "success" and "von 7 Zeilen bei h = 3 auf 159 bei h = 5" in text and "4,0- bis 5,7-Fache" in text and "alle 3 Protokolle" in text
    assert f"alle {C.LOESCH_TAKT} Konflikte" in text and "167 statt 159 Konflikte" in text and "212 Zeilen, davon 45 Löschzeilen" in text and "höchstens 203 statt 240" in text
    assert ev.verdict_schubfach(zeilen[:1])[0] == "warning"
    zeilen[1]["ohne"]["ok"] = False
    assert ev.verdict_schubfach(zeilen)[0] == "error"


def test_hinweise_verdikt_alle_akzeptiert_loeschzeile_und_falscher_hinweis():
    kind, text = ev.verdict_hinweise(A.hinweis_beispiel("hand", "normal")["je_zeile"])
    assert kind == "success" and "Alle 5 hinzugefügten Zeilen" in text and "liest zusammen 19 Klauseln" in text and "66 Prüfschritte" in text
    kind, text = ev.verdict_hinweise(A.hinweis_beispiel("hand", "loeschen")["je_zeile"])
    assert kind == "success" and "Beide Prüfer lehnen das Protokoll in Zeile 4 ab" in text and "Klausel 4 gibt es nicht" in text
    kind, text = ev.verdict_hinweise(A.hinweis_beispiel("hand", "falsch")["je_zeile"])
    assert kind == "success" and "Der Hinweisprüfer lehnt das Protokoll in Zeile 3 ab" in text and "obwohl die Suche die Zeile selbst akzeptieren würde" in text
    fehler = [{"pos": 1, "art": "a", "hinweise_ok": True, "suche_ok": False, "gelesen": 1, "schritte": 1, "grund": ""}]
    assert ev.verdict_hinweise(fehler)[0] == "error"


def test_zahlenformat_deutsch():
    assert ev.de(1234567) == "1.234.567" and ev.de(1234.5, 1) == "1.234,5" and ev.de(0.5, 2) == "0,50" and ev.de(999) == "999"
