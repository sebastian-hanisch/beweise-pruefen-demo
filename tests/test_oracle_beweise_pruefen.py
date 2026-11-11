"""Orakel-Tests des Prüfers (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12): jeweils ein anderer Rechenweg als der der Demo.

1. **Solidität gegen Aufzählung** (eigene Schleife über alle 2^n Belegungen im Test, nicht `bwp_algorithm.modelle`): an erfüllbaren Formeln mit n = 6 Variablen jede der 60 Zweierklauseln und
   jede Resolvente zweier Formelklauseln (vollständig); was der Prüfer akzeptiert, folgt aus der Formel, und jede Resolvente wird akzeptiert.
2. **Solidität gegen den Löser und gegen OR-Tools CP-SAT** an Zufallsformeln n = 30: akzeptiert heißt „Formel plus verneinte Klausel“ ist für CP-SAT unerfüllbar.
3. **Jede vom Löser als unerfüllbar beantwortete Formel hat ein akzeptiertes Protokoll** (Zufalls-3-SAT n = 20 bis 40, mit und ohne Löschzeilen), die Antwort stimmt mit CP-SAT überein.
4. **Zweig-Test:** alle vier Zellen der Tafel sind besetzt (die Fehlerzelle nur durch einen absichtlich fehlerhaften Prüfer im Test, der Mutant steht nicht im Repo-Code).
5. **Hinweisprüfer** gegen die Suche (siehe auch tests/test_pruefer.py).

Im Scratch-Lauf der Bauphase liefen dieselben Prüfungen an mehr Formeln (siehe README, Abschnitt Tests); im Repo steht die kleine, schnelle Fassung."""

import itertools

import pytest

import bwp_algorithm as A
import bwp_instanzen as I
import bwp_pruefer as P
import bwp_scenario as S
from bwp_cdcl import solve
from bwp_rup import ist_rup, pruefe_beweis

cp_model = pytest.importorskip("ortools.sat.python.cp_model")


def cpsat_antwort(n, klauseln):
    m = cp_model.CpModel()
    x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
    for c in klauseln:
        m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 30
    return {cp_model.OPTIMAL: True, cp_model.FEASIBLE: True, cp_model.INFEASIBLE: False}[s.Solve(m)]


def modelle_brute_force(n, klauseln):
    """Eigene Aufzählung aller 2^n Belegungen (unabhängig von bwp_algorithm.modelle)."""
    return [bits for bits in itertools.product([False, True], repeat=n)
            if all(any(bits[abs(l) - 1] == (l > 0) for l in c) for c in klauseln)]


def folgt_brute_force(modell_liste, klausel):
    return all(any(m[abs(l) - 1] == (l > 0) for l in klausel) for m in modell_liste)


def resolventen(klauseln):
    """Alle Resolventen zweier Formelklauseln ohne Tautologie (an jedem Pivot)."""
    ergebnis = []
    for c1, c2 in itertools.combinations(klauseln, 2):
        for p in [l for l in c1 if -l in c2]:
            r = tuple(dict.fromkeys([l for l in c1 if l != p] + [l for l in c2 if l != -p]))
            if not any(-l in r for l in r):
                ergebnis.append(r)
    return ergebnis


# ------------------------------------------------------------------------------------------------------------------------------ 1. Aufzählung

def test_solidaet_gegen_aufzaehlung_n6_alle_zweierklauseln_und_alle_resolventen():
    erfuellbar = akzeptiert_resolventen = akzeptiert_zweier = 0
    for seed in range(80):
        inst = I.rand3(6, 8, 900 + seed) if seed % 2 else I.rand3(6, 6, 900 + seed)
        kl = [list(c) for c in inst.klauseln]
        modelle = modelle_brute_force(6, inst.klauseln)
        if not modelle:
            continue
        erfuellbar += 1
        for c in A.alle_zweierklauseln(6):
            if ist_rup(kl, list(c)):
                akzeptiert_zweier += 1
                assert folgt_brute_force(modelle, c), (seed, c)                       # Solidität: akzeptiert heißt gefolgert
            assert A.Wahrheit(6, inst.klauseln).folgt(c) == folgt_brute_force(modelle, c)
        for r in resolventen(inst.klauseln):
            assert ist_rup(kl, list(r)) and folgt_brute_force(modelle, r), (seed, r)  # jede Resolvente ist RUP und gefolgert
            akzeptiert_resolventen += 1
    assert erfuellbar == 80 and akzeptiert_resolventen > 100 and akzeptiert_zweier > 50


# ------------------------------------------------------------------------------------------------------------------------------ 2. Löser und CP-SAT an n = 30

def test_solidaet_gegen_loeser_und_cpsat_an_zufallsformeln_n30():
    r = A.soliditaet_reihe(formeln=6, kandidaten_je_formel=30)
    assert r["erfuellbar"] >= 4 and r["fehler"] == [] and r["gesamt"][1] == 0
    # dritter Weg: CP-SAT entscheidet „Formel plus verneinte Klausel“ für jede akzeptierte Klausel
    pruefte = 0
    for k in range(6):
        f = S.zufallsformel(30, 1200 + k, 100)
        if solve(f.n, [list(c) for c in f.klauseln]).antwort is not True:
            continue
        for art, c in A.zufallskandidaten(30, f.klauseln, 30, 11 + k):
            if ist_rup([list(x) for x in f.klauseln], list(c)):
                assert cpsat_antwort(30, list(f.klauseln) + [(-l,) for l in c]) is False
                pruefte += 1
            # die Wahrheit des Lösers stimmt mit CP-SAT überein
            assert A.wahrheit(30, f.klauseln, c) == (cpsat_antwort(30, list(f.klauseln) + [(-l,) for l in c]) is False)
    assert pruefte >= 10


# ------------------------------------------------------------------------------------------------------------------------------ 3. jedes Protokoll wird akzeptiert

@pytest.mark.parametrize("loeschen", [False, True])
def test_jede_unerfuellbare_zufallsformel_hat_ein_akzeptiertes_protokoll(loeschen):
    unerfuellbar = 0
    for seed in range(60):
        n = (20, 30, 40)[seed % 3]
        f = S.zufallsformel(n, 5000 + seed)
        e = A.loese(f, loeschen, takt=10)
        assert e.antwort is not None
        assert e.antwort == cpsat_antwort(f.n, f.klauseln), (n, seed)                    # Antwort gegen CP-SAT
        if e.antwort is False:
            unerfuellbar += 1
            assert pruefe_beweis([list(c) for c in f.klauseln], e.beweis)[0], (n, seed)
            b = P.pruefe_protokoll(f.klauseln, e.beweis)
            assert b.ok and e.beweis[-1][0] == "a" and not e.beweis[-1][1]
            if loeschen:
                assert pruefe_beweis([list(c) for c in f.klauseln], [z for z in e.beweis if z[0] == "a"])[0]   # auch ohne Löschzeilen akzeptiert
        else:
            assert I.pruefe_modell(f.klauseln, e.modell)
    assert unerfuellbar >= 20


def test_schubfach_protokolle_mit_und_ohne_loeschzeilen_werden_akzeptiert():
    for h in (3, 4, 5):
        f = S.schubfach(h)
        ohne, mit = A.loese(f, False), A.loese(f, True, takt=20)
        assert ohne.antwort is False and mit.antwort is False and cpsat_antwort(f.n, f.klauseln) is False
        assert P.pruefe_protokoll(f.klauseln, ohne.beweis).ok and P.pruefe_protokoll(f.klauseln, mit.beweis).ok
    assert any(a == "d" for a, _ in A.loese(S.schubfach(5), True, takt=20).beweis)


# ------------------------------------------------------------------------------------------------------------------------------ 4. Zweig-Test

def test_alle_vier_zellen_besetzt_und_der_fehlerfall_wird_von_einem_mutanten_getroffen():
    r = A.soliditaet_reihe(formeln=8)
    zellen = r["gesamt"]
    assert zellen[0] > 0 and zellen[2] > 0 and zellen[3] > 0 and zellen[1] == 0           # akzeptiert+folgt, abgelehnt+folgt, abgelehnt+folgt nicht; Fehlerzelle leer

    def mutant_nimmt_alles_an_was_nicht_widerspricht(klauseln, klausel):
        """Absichtlich fehlerhaft: akzeptiert jede Klausel, deren Verneinung die Formel nicht sofort verletzt (keine Propagation)."""
        wert = {abs(l): l < 0 for l in klausel}
        return all(any(wert.get(abs(x)) == (x > 0) or wert.get(abs(x)) is None for x in c) for c in klauseln)

    gemessen = A.soliditaet_reihe(formeln=8, pruefer=mutant_nimmt_alles_an_was_nicht_widerspricht)
    assert gemessen["gesamt"][1] > 0 and gemessen["fehler"]                              # der Test würde den Fehler erkennen
    g = S.formel_g()
    t = A.soliditaet(g.n, g.klauseln, A.alle_zweierklauseln(g.n), pruefer=lambda kl, c: True)
    assert t.akzeptiert_folgt_nicht == 45 and t.fehler and t.zellen() == (15, 45, 0, 0)  # ein Prüfer, der alles annimmt, fällt an G sofort auf


# ------------------------------------------------------------------------------------------------------------------------------ 5. Hinweise

def test_hinweisprotokolle_der_solver_beweise_werden_akzeptiert():
    gesehen = 0
    for seed in range(40):
        f = S.zufallsformel(20, 5000 + seed)
        e = A.loese(f, seed % 2 == 0, takt=10)
        if e.antwort is not False:
            continue
        gesehen += 1
        zeilen = P.hinweisprotokoll(f.klauseln, e.beweis)
        assert len(zeilen) == len(e.beweis) and all(z[0] == "d" or z[2] is not None for z in zeilen)
        assert P.pruefe_hinweisprotokoll(f.klauseln, zeilen)["ok"]
    assert gesehen >= 8
