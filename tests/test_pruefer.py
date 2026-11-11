"""Der Prüfer (`bwp_rup` als Kopie des Kerns, `bwp_pruefer` mit Erklärung): Handbeispiel PHP(2) von Hand, Fehlerort, Löschzeilen, Hinweise, Randfälle, Unabhängigkeit vom Löser."""

import ast
import itertools
from pathlib import Path

import pytest

import bwp_algorithm as A
import bwp_pruefer as P
import bwp_scenario as S
from bwp_cdcl import solve
from bwp_instanzen import rand3
from bwp_rup import ist_rup, pruefe_beweis

ROOT = Path(__file__).resolve().parent.parent

KLEIN = [(1, 2), (-1, 2), (1, -2), (-1, -2)]          # (a ∨ b)(¬a ∨ b)(a ∨ ¬b)(¬a ∨ ¬b): unerfüllbar, Beweis (b), ()
KLEIN_BEWEIS = [("a", (2,)), ("a", ())]


# ------------------------------------------------------------------------------------------------------------------------------ Handbeispiel von Hand

def test_handbeispiel_alle_fuenf_zeilen_akzeptiert(php2, beweis):
    n, kl = php2
    b = P.pruefe_protokoll(kl, beweis)
    assert b.ok and b.geprueft == 5 and b.fehler_zeile is None and len(b.zeilen) == 5 and all(z.ok for z in b.zeilen)
    assert [z.nr for z in b.zeilen] == [10, 11, 12, 13, 14]                      # Formel 1 bis 9, Lemmas A bis E = 10 bis 14
    assert pruefe_beweis([list(c) for c in kl], beweis)[:2] == (True, 5)


def test_handtabelle_zeile_a_und_b_kette_der_einheiten(php2, beweis):
    """A: x1, x4 wahr -> Loch 1: ¬x3 (Klausel 4), ¬x5 (5); Loch 2: ¬x2 (7), ¬x6 (9) -> Taube 3 (Klausel 3) verletzt. B: x2, x3 wahr -> ¬x1 (4), ¬x5 (6), ¬x4 (7), ¬x6 (8) -> Klausel 3."""
    kl = php2[1]
    a = P.erklaere_zeile(kl, beweis, 1)["erklaerung"]
    assert a.annahmen == (1, 4) and a.widerspruch == 3 and set(a.kette) == {(4, -3), (5, -5), (7, -2), (9, -6)}
    b = P.erklaere_zeile(kl, beweis, 2)["erklaerung"]
    assert b.annahmen == (2, 3) and b.widerspruch == 3 and set(b.kette) == {(4, -1), (6, -5), (7, -4), (8, -6)}


def test_handtabelle_zeile_c_bis_e(php2, beweis):
    """C: x1 wahr -> A (Klausel 10) gibt ¬x4, Klausel 2 gibt x3, Klausel 4 verletzt; D: x2 wahr -> B (11) gibt ¬x3, Klausel 2 gibt x4, Klausel 7 verletzt;
    E: Klausel 1 mit ¬x1 (C = 12) und ¬x2 (D = 13) verletzt. Die Suche des Prüfers findet je nach Reihenfolge der Klauseln eine andere, ebenfalls gültige Herleitung
    (C: Klausel 2 statt 4 verletzt); deshalb wird die Kette selbst nachgerechnet statt abgeschrieben."""
    kl = php2[1]
    c = P.erklaere_zeile(kl, beweis, 3)["erklaerung"]
    d = P.erklaere_zeile(kl, beweis, 4)["erklaerung"]
    e = P.erklaere_zeile(kl, beweis, 5)["erklaerung"]
    assert c.annahmen == (1,) and (10, -4) in c.kette and c.widerspruch in (2, 4)
    assert d.annahmen == (2,) and (11, -3) in d.kette and d.widerspruch in (2, 7)
    assert e.annahmen == () and e.kette == ((12, -1), (13, -2)) and e.widerspruch == 1


def kette_ist_gueltig(db: dict, annahmen, kette, widerspruch) -> bool:
    """Unabhängige Nachrechnung einer Erklärung: jede erzwingende Klausel hat unter der bisherigen Belegung genau das erzwungene Literal offen und alle anderen falsch."""
    wert = {abs(l): l > 0 for l in annahmen}

    def lit_wert(l):
        x = wert.get(abs(l))
        return None if x is None else x == (l > 0)

    for nr, lit in kette:
        andere = [l for l in db[nr] if l != lit]
        if lit not in db[nr] or lit_wert(lit) is not None or any(lit_wert(l) is not False for l in andere):
            return False
        wert[abs(lit)] = lit > 0
    return widerspruch is None or all(lit_wert(l) is False for l in db[widerspruch])


def test_jede_erklaerung_ist_selbst_nachrechenbar(php2, beweis):
    for pos in range(1, 6):
        info = P.erklaere_zeile(php2[1], beweis, pos)
        e = info["erklaerung"]
        assert e.ok and kette_ist_gueltig(info["db"], e.annahmen, e.kette, e.widerspruch), pos


# ------------------------------------------------------------------------------------------------------------------------------ Fehlerort, Löschzeilen, Reihenfolge

def test_loeschzeile_klausel_4_vor_zeile_c_macht_c_unbeweisbar(php2, beweis):
    kl = php2[1]
    mit_loeschzeile = beweis[:2] + [("d", (-1, -3))] + beweis[2:]
    b = P.pruefe_protokoll(kl, mit_loeschzeile)
    assert not b.ok and b.fehler_zeile == 4 and b.geprueft == 2 and "Zeile 4" in b.grund
    assert pruefe_beweis([list(c) for c in kl], mit_loeschzeile)[:2] == (False, 2)
    assert b.zeilen[2].art == "d" and b.zeilen[2].nr == 4 and not b.zeilen[2].unbekannt
    # ohne Klausel 4 erzwingt x1 nur ¬x4 (Zeile A), x3, ¬x5, x6 und ¬x2; danach ist keine Klausel verletzt (Handrechnung)
    info = P.erklaere_zeile(kl, mit_loeschzeile, 4)["erklaerung"]
    assert not info.ok and {l for _, l in info.kette} == {-4, 3, -5, 6, -2}


def test_eine_geloeschte_klausel_darf_nicht_mehr_benutzt_werden():
    ok = P.pruefe_protokoll(KLEIN, KLEIN_BEWEIS)
    assert ok.ok and ok.geprueft == 2
    schlecht = [("a", (2,)), ("d", (2,)), ("a", ())]                     # das Lemma (b) wird vor der leeren Klausel gelöscht
    b = P.pruefe_protokoll(KLEIN, schlecht)
    assert not b.ok and b.fehler_zeile == 3
    assert pruefe_beweis([list(c) for c in KLEIN], schlecht)[0] is False


def test_reihenfolge_zaehlt_das_lemma_muss_vor_seiner_verwendung_stehen(php2, beweis):
    """E = () braucht C und D: vor ihnen steht sie nicht herleitbar; die Reihenfolge A B E C D wird in Zeile 3 abgelehnt."""
    kl = php2[1]
    vertauscht = [beweis[0], beweis[1], beweis[4], beweis[2], beweis[3]]
    b = P.pruefe_protokoll(kl, vertauscht)
    assert not b.ok and b.fehler_zeile == 3 and b.geprueft == 2 and b.ungeprueft == 2
    assert KLEIN_BEWEIS[::-1][0][1] == () and not P.pruefe_protokoll(KLEIN, KLEIN_BEWEIS[::-1]).ok


def test_vertauschen_von_a_und_c_wird_nicht_abgelehnt_weil_c_schon_aus_der_formel_folgt(php2, beweis):
    """Abweichung vom Plan (er nannte diesen Fall als abgelehnt): C = (¬x1) ist ohne A herleitbar (x1 erzwingt ¬x3, ¬x5, x4 und ¬x6; Klausel 3 verletzt), A wird danach gebraucht nicht mehr."""
    kl = php2[1]
    vertauscht = [beweis[2], beweis[1], beweis[0], beweis[3], beweis[4]]
    assert P.pruefe_protokoll(kl, vertauscht).ok


def test_protokoll_ohne_leere_klausel_gilt_nicht_als_beweis(php2, beweis):
    b = P.pruefe_protokoll(php2[1], beweis[:-1])
    assert not b.ok and b.fehler_zeile is None and "leere Klausel" in b.grund and b.geprueft == 4
    assert pruefe_beweis([list(c) for c in php2[1]], beweis[:-1])[0] is False


def test_loeschzeile_fuer_nicht_vorhandene_klausel_wird_ignoriert_aber_gemeldet():
    b = P.pruefe_protokoll(KLEIN, [("d", (7, 8)), ("a", (2,)), ("a", ())])
    assert b.ok and b.unbekannt_geloescht == 1 and b.zeilen[0].unbekannt and b.zeilen[0].nr is None
    assert pruefe_beweis([list(c) for c in KLEIN], [("d", (7, 8)), ("a", (2,)), ("a", ())])[0] is True


def test_zeilen_nach_der_leeren_klausel_werden_nicht_gelesen():
    b = P.pruefe_protokoll(KLEIN, KLEIN_BEWEIS + [("a", (99,))])
    assert b.ok and b.ungeprueft == 1 and len(b.zeilen) == 2


# ------------------------------------------------------------------------------------------------------------------------------ Randfälle

def test_randfaelle():
    assert not P.pruefe_protokoll([], [("a", ())]).ok                                    # leere Formel: die leere Klausel folgt nicht
    assert P.pruefe_protokoll([()], [("a", ())]).ok                                      # Formel mit leerer Klausel: eine Zeile genügt
    assert P.pruefe_protokoll([(1,), (-1,)], [("a", ())]).ok                              # n = 1, Einheitsklauseln: die leere Klausel allein
    assert P.pruefe_protokoll([(1, 2)], [("a", (1, -1))]).ok is False                    # Tautologie ist RUP, aber ohne leere Klausel kein Beweis
    assert P.pruefe_protokoll([(1, 2)], [("a", (1, -1))]).zeilen[0].ok
    assert P.pruefe_protokoll(KLEIN, []).ok is False                                     # leeres Protokoll
    assert P.propagiere_erklaert([(1, (1, 2))], (3, -3)).tautologie                      # Tautologie: trivial wahr, keine Propagation nötig
    assert P.propagiere_erklaert([(1, (1, 2))], (3, 3)).ok is False                      # doppeltes Literal: wird einmal angenommen, nichts folgt
    assert ist_rup([[1, 2]], [3, -3]) and not ist_rup([[1, 2]], [3, 3])
    with pytest.raises(ValueError):
        P.erklaere_zeile(KLEIN, KLEIN_BEWEIS, 3)


def test_bestand_loescht_die_zuletzt_hinzugefuegte_kopie():
    b = P.Bestand([(1, 2), (1, 2), (3,)])
    assert b.loesche((2, 1)) == 2 and b.loesche((1, 2)) == 1 and b.loesche((1, 2)) is None and b.anzahl() == 1


# ------------------------------------------------------------------------------------------------------------------------------ gleiches Urteil wie der Kern-Prüfer

def _proofs():
    for seed in range(12):
        inst = rand3(30, 128, 7000 + seed)
        for delete in (False, True):
            e = solve(inst.n, inst.klauseln, proof=True, delete=delete, delete_every=10)
            if e.antwort is False:
                yield inst.klauseln, e.beweis


def test_pruefer_mit_erklaerung_und_kern_pruefer_zaehlen_gleich_auch_bei_veraenderten_protokollen():
    gesehen = 0
    for klauseln, beweis in _proofs():
        gesehen += 1
        kandidaten = [beweis] + [A.manipuliere(beweis, art, s)[0] for art in ("kuerzen", "tauschen", "vertauschen", "loeschen") for s in range(3)]
        for protokoll in kandidaten:
            b = P.pruefe_protokoll(klauseln, protokoll)
            ok, geprueft, schritte = pruefe_beweis([list(c) for c in klauseln], protokoll)
            assert (b.ok, b.geprueft, b.schritte) == (ok, geprueft, schritte)
    assert gesehen >= 6


# ------------------------------------------------------------------------------------------------------------------------------ Hinweise (Ausblick)

def test_hinweise_von_hand_aus_dem_handbeispiel_werden_akzeptiert(php2, beweis):
    """Klauselnummern: Formel 1 bis 9, Lemmas A bis E = 10 bis 14; Handlisten aus dem Handbeispiel (Teil C), zwischen 3 und 5 Klauseln je Zeile."""
    hand = [[4, 5, 7, 9, 3], [7, 8, 4, 6, 3], [10, 2, 4], [11, 2, 7], [12, 13, 1]]
    zeilen = [("a", c, h) for (_, c), h in zip(beweis, hand)]
    r = P.pruefe_hinweisprotokoll(php2[1], zeilen)
    assert r["ok"] and r["gelesen"] == 5 + 5 + 3 + 3 + 3


def test_erzeugte_hinweise_sind_knapp_und_werden_akzeptiert(php2, beweis):
    zeilen = P.hinweisprotokoll(php2[1], beweis)
    assert [z[2] for z in zeilen] == [[5, 9, 3], [6, 8, 3], [4, 10, 2], [7, 11, 2], [12, 13, 1]]
    assert P.pruefe_hinweisprotokoll(php2[1], zeilen)["ok"]


def test_hinweise_loeschzeile_und_falscher_hinweis_werden_abgelehnt(php2, beweis):
    kl = php2[1]
    hand = [[4, 5, 7, 9, 3], [7, 8, 4, 6, 3], [10, 2, 4], [11, 2, 7], [12, 13, 1]]
    zeilen = [("a", c, h) for (_, c), h in zip(beweis, hand)]
    mit_d = zeilen[:2] + [("d", 4)] + zeilen[2:]
    r = P.pruefe_hinweisprotokoll(kl, mit_d)
    assert not r["ok"] and r["fehler_zeile"] == 4 and "gelöscht" in r["grund"]
    falsch = zeilen[:2] + [("a", (-1,), [10, 2, 1])] + zeilen[3:]
    r = P.pruefe_hinweisprotokoll(kl, falsch)
    assert not r["ok"] and r["fehler_zeile"] == 3
    # beide Ablehnungen stimmen mit der Suche überein (hb_06, Teil C)
    for quelle in ("hand", "suche"):
        bsp = A.hinweis_beispiel(quelle, "loeschen")
        assert not bsp["hinweis"]["ok"] and not bsp["suche"].ok                  # beide Prüfer lehnen Zeile C ab
        bsp = A.hinweis_beispiel(quelle, "falsch")
        assert not bsp["hinweis"]["ok"] and bsp["suche"].ok                      # nur der falsche Hinweis wird abgelehnt, die Zeile selbst stimmt


def test_hinweispruefer_akzeptiert_genau_was_die_suche_akzeptiert():
    """An erfüllbaren Zufallsformeln (n = 12): für jede Kandidatenklausel akzeptiert der Hinweisprüfer die aus der Suche erzeugten Hinweise genau dann, wenn die Suche akzeptiert;
    für nicht herleitbare Klauseln lehnt er jede Hinweisliste ab, auch die Hinweise anderer Klauseln."""
    formeln = 0
    for seed in range(60):
        inst = rand3(12, 36, 3000 + seed)
        if solve(inst.n, inst.klauseln).antwort is not True:
            continue
        formeln += 1
        db = list(enumerate(inst.klauseln, 1))
        lebend = dict(db)
        kandidaten = A.zufallskandidaten(12, inst.klauseln, 25, seed)
        andere = [P.hinweise(db, c) for _, c in kandidaten]
        andere = [h for h in andere if h] or [[1]]
        for art, c in kandidaten:
            such = ist_rup([list(x) for x in inst.klauseln], list(c))
            h = P.hinweise(db, c)
            assert (h is not None) == such
            if such:
                assert P.pruefe_hinweise(lebend, c, h).ok
            else:
                assert not any(P.pruefe_hinweise(lebend, c, x).ok for x in andere + [[], list(lebend)[:3]])
    assert formeln >= 20


def test_hinweise_sind_knapp_nur_benoetigte_klauseln(php2):
    db = list(enumerate(php2[1], 1))
    h = P.hinweise(db, (-1, -4))
    assert h == [5, 9, 3]                                                         # die Klauseln 4 und 7 erzwingen ¬x3 und ¬x2: für den Widerspruch nicht nötig


# ------------------------------------------------------------------------------------------------------------------------------ Unabhängigkeit vom Löser

@pytest.mark.parametrize("datei", ["bwp_rup.py", "bwp_pruefer.py"])
def test_pruefer_importiert_weder_den_loeser_noch_dessen_namen(datei):
    """Quelle des Vertrauens ist getrennter Code: Quelltextprüfung auf Importe und auf Namen aus `bwp_cdcl`."""
    quelle = (ROOT / datei).read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    for node in ast.walk(baum):
        if isinstance(node, ast.Import):
            assert not any("cdcl" in a.name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert "cdcl" not in (node.module or "") and node.module in (None, "typing")
    namen = {n.id for n in ast.walk(baum) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(baum) if isinstance(n, ast.Attribute)}
    assert not namen & {"Loeser", "solve", "analysiere", "propagiere", "Ergebnis"}
    zeilen = [z for z in quelle.splitlines() if z.startswith(("import ", "from "))]
    assert all("bwp_" not in z for z in zeilen)                                  # nicht einmal ein anderes Modul der Demo


def test_formeln_des_handbeispiels_stimmen_mit_den_handwerten_ueberein(php2):
    assert [tuple(c) for c in S.php2().klauseln] == php2[1]
    assert A.modelle(6, S.formel_g().klauseln) and len(A.modelle(6, S.formel_g().klauseln)) == 7
    assert list(itertools.islice(A.modelle(6, php2[1]), 1)) == []                # PHP(2): kein Modell unter allen 64 Belegungen
