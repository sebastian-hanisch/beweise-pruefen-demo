# Herkunft: Kopie von sat-cp-planung/kern/rup.py (Kern-Version 885e1c74ce170cd5, Datei HASHES.txt vom 2026-11-10), nur Importe auf bwp_ umgestellt.
# Nicht von Hand ändern: tests/test_copies.py vergleicht diese Datei mit dem Kern-Hash.
"""Unabhängiger Beweisprüfer (RUP: reverse unit propagation) des Kern-Pakets.

Kein Code aus `cdcl.py`: Der Prüfer arbeitet mit Zählern statt mit beobachteten Literalen und ist absichtlich einfach und langsam.
Eine Lemma-Klausel C ist RUP, wenn aus den Klauseln der Formel und den bisher bewiesenen Lemmas nach Annahme der Verneinung von C
durch Einheitspropagation ein Widerspruch folgt. Ein Beweis ist eine Liste von Schritten ("a", klausel) (Klausel hinzufügen,
muss RUP sein) und ("d", klausel) (Klausel löschen) und endet bei Erfolg mit ("a", []), der leeren Klausel.
RUP ist strenger als logische Folgerung: Der Prüfer kann Gefolgertes ablehnen, nimmt aber nie etwas an, das nicht folgt.
"""


def propagiere_bis_widerspruch(klauseln, annahmen):
    """Belegt die Literale in `annahmen`, propagiert Einheitsklauseln bis zum Fixpunkt.
    Rückgabe (Widerspruch gefunden, Zahl der Klausel-Prüfungen)."""
    wert = {}
    schritte = 0
    for l in annahmen:
        if wert.get(abs(l)) == (l < 0):
            return True, schritte
        wert[abs(l)] = l > 0
    geaendert = True
    while geaendert:
        geaendert = False
        for c in klauseln:
            schritte += 1
            offen, erfuellt = [], False
            for l in c:
                x = wert.get(abs(l))
                if x is None:
                    offen.append(l)
                elif x == (l > 0):
                    erfuellt = True
                    break
            if erfuellt:
                continue
            if not offen:
                return True, schritte
            if len(offen) == 1:
                wert[abs(offen[0])] = offen[0] > 0
                geaendert = True
    return False, schritte


def ist_rup(klauseln, klausel):
    """Einzelprüfung: folgt `klausel` aus `klauseln` durch Einheitspropagation nach Annahme ihrer Verneinung?"""
    gefunden, _ = propagiere_bis_widerspruch(klauseln, [-l for l in klausel])
    return gefunden


def pruefe_beweis(klauseln, beweis):
    """Prüft einen Beweis. Rückgabe (ok, Zahl geprüfter Lemmas, Zahl Klausel-Prüfungen insgesamt)."""
    lebend = {}
    for c in klauseln:
        lebend.setdefault(tuple(sorted(c)), []).append(list(c))
    schritte = 0
    geprueft = 0
    for art, c in beweis:
        schluessel = tuple(sorted(c))
        if art == "d":
            liste = lebend.get(schluessel)
            if liste:
                liste.pop()
            continue
        alle = [x for liste in lebend.values() for x in liste]
        gefunden, s = propagiere_bis_widerspruch(alle, [-l for l in c])
        schritte += s
        if not gefunden:
            return False, geprueft, schritte
        geprueft += 1
        lebend.setdefault(schluessel, []).append(list(c))
        if not c:
            return True, geprueft, schritte
    return False, geprueft, schritte
