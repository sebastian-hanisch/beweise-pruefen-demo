"""Kern-Regressionstest des Beweisprüfers (aus kern/tests/test_rup.py übernommen, Importe auf bwp_ umgestellt): Handbeispiel, Beweise des Lösers, Solidität an erfüllbaren Formeln."""

import bwp_instanzen as I
from bwp_cdcl import solve
from bwp_rng import SplitMix64
from bwp_rup import ist_rup, pruefe_beweis


def test_handbeispiel():
    # (a ∨ b)(¬a ∨ b)(a ∨ ¬b)(¬a ∨ ¬b), a = 1, b = 2: unerfüllbar. Lemma (b) ist RUP (¬b erzwingt a und ¬a), danach die leere Klausel.
    kl = [(1, 2), (-1, 2), (1, -2), (-1, -2)]
    assert ist_rup(kl, (2,))
    assert not ist_rup(kl, (3,))                                 # Variable 3 kommt nicht vor: keine Propagation, kein Widerspruch
    ok, geprueft, schritte = pruefe_beweis(kl, [("a", [2]), ("a", [])])
    assert ok and geprueft == 2 and schritte > 0
    assert pruefe_beweis(kl, [("a", [])])[0] is False            # die leere Klausel ist ohne das Lemma nicht RUP
    assert pruefe_beweis(kl, [("a", [2])])[0] is False           # ohne leere Klausel am Ende kein Beweis


def test_beweise_des_loesers_werden_akzeptiert():
    for h in (3, 4, 5):
        inst = I.pigeonhole(h)
        erg = solve(inst.n, inst.klauseln, proof=True)
        assert erg.antwort is False and erg.beweis[-1] == ("a", [])
        assert pruefe_beweis(inst.klauseln, erg.beweis)[0]
    # mit Löschen: Löschzeilen im Protokoll
    inst = I.pigeonhole(5)
    erg = solve(inst.n, inst.klauseln, proof=True, delete=True, delete_every=10)
    assert any(a == "d" for a, _ in erg.beweis)
    assert pruefe_beweis(inst.klauseln, erg.beweis)[0]


def test_verfaelschter_beweis_wird_abgelehnt():
    inst = I.pigeonhole(4)
    erg = solve(inst.n, inst.klauseln, proof=True)
    abgelehnt = 0
    for i, (art, c) in enumerate(erg.beweis[:-1]):
        if art == "a" and len(c) >= 2:
            schlecht = [(a, list(x)) for a, x in erg.beweis]
            schlecht[i] = ("a", [-c[0]])                        # ein Literal verkehrt, Rest weg: meist nicht RUP
            abgelehnt += not pruefe_beweis(inst.klauseln, schlecht)[0]
    assert abgelehnt >= 10


def test_solidaet_an_erfuellbaren_formeln():
    """Wenn der Prüfer eine Klausel annimmt, folgt sie aus der Formel (Gegenprobe: Formel plus verneinte Klausel unerfüllbar).
    Resolventen zweier Klauseln sind immer RUP; zufällige Klauseln meist nicht."""
    rng = SplitMix64(11)
    angenommen = resolventen = 0
    for seed in range(12):
        inst = I.rand3(30, 100, 1200 + seed)
        if solve(inst.n, inst.klauseln).antwort is not True:
            continue
        for _ in range(40):
            if rng.coin():
                vs = rng.sample(range(1, 31), 2 + rng.below(2))
                c = [v if rng.coin() else -v for v in vs]
            else:
                c1, c2 = rng.sample(inst.klauseln, 2)
                piv = [l for l in c1 if -l in c2]
                if not piv:
                    continue
                p = piv[0]
                c = list(dict.fromkeys([l for l in c1 if l != p] + [l for l in c2 if l != -p]))
                if any(-l in c for l in c):
                    continue
                assert ist_rup(inst.klauseln, c)                # Resolventen sind immer RUP
                resolventen += 1
            if ist_rup(inst.klauseln, c):
                angenommen += 1
                gegenprobe = solve(inst.n, inst.klauseln + [(-l,) for l in c])
                assert gegenprobe.antwort is False              # folgt wirklich
    assert resolventen > 20 and angenommen >= resolventen


def test_rup_strenger_als_folgerung():
    # unerfüllbar (also folgt die leere Klausel), aber ohne Lemma erzwingt die Einheitspropagation nichts: die leere Klausel ist nicht RUP;
    # das Lemma (a) ist RUP, und danach genügen die vier Fallklauseln auf b, c nicht mehr direkt, sie brauchen zwei weitere Lemmas.
    kl = [(1, 2), (1, -2), (-1, 3, 4), (-1, 3, -4), (-1, -3, 4), (-1, -3, -4)]
    assert not ist_rup(kl, ())
    assert ist_rup(kl, (1,))
    kl2 = kl + [(1,)]
    assert ist_rup(kl2, (3,)) and not ist_rup(kl2, ())
    assert pruefe_beweis(kl, [("a", [1]), ("a", [3]), ("a", [])])[0]
