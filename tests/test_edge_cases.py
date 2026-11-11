"""Randfälle (DEMO-PLAYBOOK §12): leere Formel, Formel mit leerer Klausel, Einheitsklausel, n = 1, Protokoll mit nur der leeren Klausel, Löschzeile für eine nicht vorhandene Klausel,
Grenzen der Regler."""

import pytest

import bwp_algorithm as A
import bwp_constants as C
import bwp_evaluation as ev
import bwp_pruefer as P
import bwp_scenario as S


def formel(n, klauseln):
    return S.Formel(n, tuple(tuple(c) for c in klauseln), "Randfall")


def test_leere_formel_ist_erfuellbar_und_braucht_kein_protokoll():
    l = A.lauf(formel(1, []))
    assert l.antwort is True and l.protokoll == () and l.befund is None and l.modell_ok is True
    assert A.modelle(0, ()) == [0]                                           # eine Belegung (die leere), alle Klauseln (keine) erfüllt


def test_formel_mit_leerer_klausel_braucht_genau_eine_zeile():
    l = A.lauf(formel(1, [()]))
    assert l.antwort is False and len(l.protokoll) == 1 and l.protokoll[0][0] == "a" and not l.protokoll[0][1] and l.befund.ok and l.befund.geprueft == 1
    assert l.befund.schritte == 1                                            # eine Klausel angesehen: die leere, sofort verletzt


def test_einheitsklausel_und_n_gleich_eins():
    erfuellbar = A.lauf(formel(1, [(1,)]))
    assert erfuellbar.antwort is True and erfuellbar.modell_ok
    unerfuellbar = A.lauf(formel(1, [(1,), (-1,)]))
    assert unerfuellbar.antwort is False and len(unerfuellbar.protokoll) == 1 and unerfuellbar.befund.ok
    assert unerfuellbar.befund.schritte == 2                                 # (x1) erzwingt x1, (¬x1) ist verletzt: zwei Klauseln angesehen


def test_protokoll_mit_nur_der_leeren_klausel_und_loeschzeile_fuer_fehlende_klausel():
    f = formel(2, [(1, 2), (-1, 2), (1, -2), (-1, -2)])
    assert not P.pruefe_protokoll(f.klauseln, [("a", ())]).ok                 # ohne das Lemma (b) ist die leere Klausel nicht herleitbar
    b = P.pruefe_protokoll(f.klauseln, [("d", (5, 6)), ("a", (2,)), ("a", ())])
    assert b.ok and b.unbekannt_geloescht == 1


def test_manipulation_eines_einzeiligen_protokolls_bleibt_unveraendert():
    for art in C.MANIPULATIONEN:
        neu, text, zeile = A.manipuliere([("a", ())], art, 3)
        assert neu == [("a", ())] and zeile is None


def test_messzeile_ohne_unerfuellbare_formel_hat_keine_werte_und_das_verdikt_warnt():
    z = A.zeile_zufall(30, [], 3)
    assert z["formeln"] == 0 and z["zeilen_je_konflikt"] is None
    assert ev.verdict_groesse([z])[0] == "warning"
    assert ev.verdict_groesse([])[0] == "warning"


def test_zufallsformel_an_den_reglergrenzen_hat_eine_unerfuellbare_formel_oder_meldet_das():
    for n in (C.N_MIN, C.N_MAX):
        g = ev.formel_von(ev.Settings(C.FAMILIE_ZUFALL, n, C.DEFAULT_H, C.LOESCHEN_AUS, C.QUELLE_LOESER, C.SEED_MAX))
        assert g.formel.n == n
        if g.gefunden:
            l = A.lauf(g.formel)
            assert l.antwort is False and l.befund.ok
    for h in (C.H_MIN, C.H_MAX):
        l = A.lauf(S.schubfach(h), True)
        assert l.befund.ok


def test_budget_erreicht_gibt_kein_protokoll_und_ein_warnendes_verdikt():
    l = A.lauf(S.schubfach(5), budget=2)
    assert l.antwort is None and l.befund is None
    assert ev.verdict_kernfrage(l)[0] == "warning"


@pytest.mark.parametrize("text, erwartet", [("1 2", (1, 2)), ("  -3   4 ", (-3, 4)), ("x1 ¬x2", (1, -2)), ("1,2,-3", (1, 2, -3))])
def test_klauseleingabe_toleriert_trennzeichen_und_schreibweisen(text, erwartet):
    assert S.parse_klausel(text, 6) == (erwartet, None)
