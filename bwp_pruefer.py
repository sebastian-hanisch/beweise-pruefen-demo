"""Der Prüfer des Protokolls mit Erklärung: einfach, zählerfrei lesbar, ohne den Löser zu kennen.

Dieses Modul importiert nichts aus `bwp_cdcl` (Quelltextprüfung in `tests/test_pruefer.py`): Das Vertrauen in das Urteil „unerfüllbar“ kommt daraus, dass
ein getrennter, kurzer Code jede Zeile des Protokolls nachrechnet. Die Prüfung ist dieselbe wie in `bwp_rup.py` (RUP: Annahme, dass alle Literale der Zeile falsch
sind, danach Einheitspropagation; ein Widerspruch beweist die Zeile). Hier kommen dazu, was `bwp_rup.py` (wörtliche Kopie des Kerns) nicht liefert:

  `propagiere_erklaert`        die Kette der erzwungenen Literale mit der Nummer der erzwingenden Klausel und der verletzten Klausel
  `pruefe_protokoll`           Zeile für Zeile, mit der Nummer der abgelehnten Zeile und dem Hinweis auf Löschzeilen für nie vorhandene Klauseln
  `erklaere_zeile`             eine Zeile des Protokolls erklärt (angenommene falsche Literale, Kette, Widerspruch)
  `hinweise`                   LRAT-ähnliche Hinweisliste einer Zeile (nur zur Veranschaulichung, kein LRAT-Format)
  `pruefe_hinweise`            Hinweisprüfer: liest die Nummern der Reihe nach, sucht nicht
  `hinweisprotokoll`, `pruefe_hinweisprotokoll`   ganze Protokolle mit Hinweisen und Löschzeilen nach Klauselnummer

Klauselnummern: die Formelklauseln haben die Nummern 1 bis m in Eingabereihenfolge, jede angenommene Zeile des Protokolls (auch die leere Klausel) die nächste.
Die Reihenfolge, in der die Klauseln durchsucht werden, ist dieselbe wie in `bwp_rup.pruefe_beweis` (Klauseln gleichen Inhalts stehen zusammen, in der Reihenfolge
des ersten Auftretens), damit beide Prüfer dieselben Prüfschritte zählen; `tests/test_pruefer.py` vergleicht das.
"""

from typing import NamedTuple


class Erklaerung(NamedTuple):
    ok: bool                 # Widerspruch gefunden (oder Tautologie): die Klausel ist RUP
    annahmen: tuple          # Literale, die als wahr angenommen werden: die Verneinung der geprüften Klausel
    kette: tuple             # ((Klauselnummer, erzwungenes Literal), ...) in der Reihenfolge der Propagation
    widerspruch: object      # Nummer der Klausel, deren Literale alle falsch sind; None bei Tautologie oder ohne Widerspruch
    tautologie: bool         # die Klausel enthält ein Literal und sein Gegenteil: trivial wahr
    schritte: int            # geprüfte Klauseln (Prüfschritte), wie in bwp_rup


class Zeile(NamedTuple):
    pos: int                 # Zeilennummer im Protokoll, ab 1
    art: str                 # "a" (hinzufügen) oder "d" (löschen)
    klausel: tuple
    nr: object               # a: vergebene Klauselnummer (nur wenn angenommen); d: Nummer der gelöschten Klausel, None wenn keine vorhanden war
    ok: bool                 # a: RUP; d: immer True (auch eine Löschzeile ohne Klausel wird wie im Kern ignoriert)
    schritte: int
    unbekannt: bool          # d: es gab keine Klausel dieses Inhalts


class Befund(NamedTuple):
    ok: bool                 # der Beweis ist akzeptiert: jede Zeile bis zur leeren Klausel ist RUP
    geprueft: int            # Zahl der angenommenen Lemmas (Löschzeilen zählen nicht)
    schritte: int
    fehler_zeile: object     # Zeilennummer der ersten abgelehnten Zeile, sonst None
    grund: str
    zeilen: tuple            # Zeile für Zeile bis zur ersten Ablehnung oder zur leeren Klausel
    unbekannt_geloescht: int
    ungeprueft: int          # Zeilen nach der leeren Klausel (werden wie im Kern nicht mehr gelesen)


class Bestand:
    """Die lebenden Klauseln mit Nummern; Gruppierung und Löschregel wie in `bwp_rup.pruefe_beweis`."""

    def __init__(self, klauseln=()):
        self.gruppen = {}
        self.naechste = 1
        for c in klauseln:
            self.hinzu(c)

    def hinzu(self, klausel) -> int:
        nr = self.naechste
        self.naechste += 1
        self.gruppen.setdefault(tuple(sorted(klausel)), []).append((nr, tuple(klausel)))
        return nr

    def loesche(self, klausel):
        """Entfernt die zuletzt hinzugefügte Kopie; Rückgabe die Nummer, None wenn es keine gab."""
        liste = self.gruppen.get(tuple(sorted(klausel)))
        if liste:
            return liste.pop()[0]
        return None

    def loesche_nr(self, nr) -> bool:
        for liste in self.gruppen.values():
            for i, (n, _) in enumerate(liste):
                if n == nr:
                    del liste[i]
                    return True
        return False

    def alle(self) -> list:
        return [x for liste in self.gruppen.values() for x in liste]

    def als_dict(self) -> dict:
        return dict(self.alle())

    def anzahl(self) -> int:
        return sum(len(liste) for liste in self.gruppen.values())


def propagiere_erklaert(db, klausel) -> Erklaerung:
    """Annahme: alle Literale von `klausel` falsch; Einheitspropagation über `db` (Liste von (Nummer, Klausel)) bis zum Widerspruch oder Fixpunkt."""
    annahmen = tuple(-l for l in klausel)
    wert = {}
    schritte = 0
    for l in annahmen:
        if wert.get(abs(l)) == (l < 0):
            return Erklaerung(True, annahmen, (), None, True, schritte)
        wert[abs(l)] = l > 0
    kette = []
    geaendert = True
    while geaendert:
        geaendert = False
        for nr, c in db:
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
                return Erklaerung(True, annahmen, tuple(kette), nr, False, schritte)
            if len(offen) == 1:
                wert[abs(offen[0])] = offen[0] > 0
                kette.append((nr, offen[0]))
                geaendert = True
    return Erklaerung(False, annahmen, tuple(kette), None, False, schritte)


def pruefe_protokoll(klauseln, protokoll) -> Befund:
    """Prüft ein Protokoll Zeile für Zeile; Erfolg nur, wenn die letzte gelesene Zeile die leere Klausel ist und jede Zeile davor RUP."""
    bestand = Bestand(klauseln)
    zeilen = []
    schritte = geprueft = unbekannt = 0
    anzahl = len(protokoll)
    for pos, (art, c) in enumerate(protokoll, 1):
        c = tuple(c)
        if art == "d":
            nr = bestand.loesche(c)
            unbekannt += nr is None
            zeilen.append(Zeile(pos, "d", c, nr, True, 0, nr is None))
            continue
        e = propagiere_erklaert(bestand.alle(), c)
        schritte += e.schritte
        if not e.ok:
            zeilen.append(Zeile(pos, "a", c, None, False, e.schritte, False))
            return Befund(False, geprueft, schritte, pos, "Zeile %d ist durch Einheitspropagation nicht herleitbar" % pos, tuple(zeilen), unbekannt, anzahl - pos)
        geprueft += 1
        nr = bestand.hinzu(c)
        zeilen.append(Zeile(pos, "a", c, nr, True, e.schritte, False))
        if not c:
            return Befund(True, geprueft, schritte, None, "ok", tuple(zeilen), unbekannt, anzahl - pos)
    return Befund(False, geprueft, schritte, None, "das Protokoll endet ohne leere Klausel", tuple(zeilen), unbekannt, 0)


def bestand_vor_zeile(klauseln, protokoll, pos) -> Bestand:
    """Die lebenden Klauseln unmittelbar vor Zeile `pos` (ab 1): Formelklauseln plus alle vorher angenommenen Lemmas minus die gelöschten.
    Es wird nicht geprüft; wie im Kern werden alle vorherigen Zeilen als angenommen gelesen."""
    bestand = Bestand(klauseln)
    for art, c in protokoll[:pos - 1]:
        if art == "d":
            bestand.loesche(c)
        else:
            bestand.hinzu(c)
    return bestand


def erklaere_zeile(klauseln, protokoll, pos) -> dict:
    """Erklärt Zeile `pos` des Protokolls. Rückgabe: {"art", "klausel", "lebende" (Zahl vor der Zeile), "erklaerung" (Erklaerung oder None bei "d"), "geloescht_nr"}."""
    if not 1 <= pos <= len(protokoll):
        raise ValueError(f"Zeile {pos} liegt außerhalb von 1 bis {len(protokoll)}")
    art, c = protokoll[pos - 1]
    c = tuple(c)
    bestand = bestand_vor_zeile(klauseln, protokoll, pos)
    lebende = bestand.anzahl()
    if art == "d":
        return {"art": "d", "klausel": c, "lebende": lebende, "erklaerung": None, "geloescht_nr": bestand.loesche(c), "nr": None, "db": bestand.als_dict()}
    e = propagiere_erklaert(bestand.alle(), c)
    return {"art": "a", "klausel": c, "lebende": lebende, "erklaerung": e, "geloescht_nr": None, "nr": bestand.naechste, "db": bestand.als_dict()}


def hinweise(db, klausel):
    """Hinweisliste einer Zeile: die Nummern der Klauseln, die unter der Annahme „alle Literale falsch“ nacheinander ein Literal erzwingen und zuletzt den
    Widerspruch liefern, **nur** die benötigten (Rückverfolgung vom Widerspruch aus), in der Reihenfolge der Propagation. `db`: Liste von (Nummer, Klausel).
    Rückgabe None, wenn die Klausel nicht RUP ist; eine Tautologie braucht keine Hinweise ([])."""
    e = propagiere_erklaert(db, klausel)
    if not e.ok:
        return None
    if e.tautologie:
        return []
    klauseln = dict(db)
    erzwungen = {abs(lit): (i, nr) for i, (nr, lit) in enumerate(e.kette)}
    benoetigt = set()
    stapel = [abs(l) for l in klauseln[e.widerspruch]]
    gesehen = set()
    while stapel:
        v = stapel.pop()
        if v in gesehen:
            continue
        gesehen.add(v)
        if v in erzwungen:
            _, nr = erzwungen[v]
            benoetigt.add(nr)
            stapel.extend(abs(l) for l in klauseln[nr])
    reihenfolge = sorted(benoetigt, key=lambda nr: next(i for i, (n, _) in enumerate(e.kette) if n == nr))
    return reihenfolge + [e.widerspruch]


class HinweisUrteil(NamedTuple):
    ok: bool
    gelesen: int             # gelesene Hinweisklauseln
    grund: str


def pruefe_hinweise(lebend: dict, klausel, hinweisliste) -> HinweisUrteil:
    """Hinweisprüfer: folgt den Nummern der Reihe nach, ohne zu suchen. `lebend`: {Nummer: Klausel}. Jede Hinweisklausel muss unter der aktuellen Belegung höchstens ein
    offenes Literal haben und kein wahres; ein offenes Literal wird wahr gesetzt, keines ist der Widerspruch und muss der letzte Hinweis sein."""
    wert = {}
    for l in klausel:
        if wert.get(abs(l)) == (l > 0):
            return HinweisUrteil(True, 0, "Tautologie")
        wert[abs(l)] = l < 0
    gelesen = 0
    for h in hinweisliste or ():
        if h not in lebend:
            return HinweisUrteil(False, gelesen, f"Klausel {h} gibt es nicht (gelöscht oder nie vorhanden)")
        gelesen += 1
        offen = []
        for l in lebend[h]:
            x = wert.get(abs(l))
            if x is None:
                offen.append(l)
            elif x == (l > 0):
                return HinweisUrteil(False, gelesen, f"Klausel {h} ist schon erfüllt und erzwingt nichts")
        if not offen:
            if h == hinweisliste[-1]:
                return HinweisUrteil(True, gelesen, "Widerspruch")
            return HinweisUrteil(False, gelesen, f"Klausel {h} ist verletzt, aber nicht der letzte Hinweis")
        if len(offen) > 1:
            return HinweisUrteil(False, gelesen, f"Klausel {h} hat {len(offen)} offene Literale und erzwingt nichts")
        wert[abs(offen[0])] = offen[0] > 0
    return HinweisUrteil(False, gelesen, "die Hinweise enden ohne Widerspruch")


def hinweisprotokoll(klauseln, protokoll) -> list:
    """Wandelt ein Protokoll in Zeilen mit Hinweisen um: ("a", klausel, hinweisliste oder None) bzw. ("d", klauselnummer oder None).
    Die Hinweise stammen aus der Suche (`hinweise`); eine Zeile, die nicht RUP ist, bekommt None. Das Ergebnis ist kein LRAT-Format."""
    bestand = Bestand(klauseln)
    ergebnis = []
    for art, c in protokoll:
        c = tuple(c)
        if art == "d":
            ergebnis.append(("d", bestand.loesche(c)))
            continue
        liste = hinweise(bestand.alle(), c)
        ergebnis.append(("a", c, liste))
        if liste is not None:
            bestand.hinzu(c)
        else:
            break
    return ergebnis


def pruefe_hinweisprotokoll(klauseln, zeilen) -> dict:
    """Prüft ein Protokoll mit Hinweisen. Rückgabe {"ok", "gelesen" (Hinweisklauseln insgesamt), "fehler_zeile", "grund", "je_zeile": [HinweisUrteil oder None für "d"]}."""
    bestand = Bestand(klauseln)
    lebend = bestand.als_dict()
    gelesen = 0
    je_zeile = []
    for pos, z in enumerate(zeilen, 1):
        if z[0] == "d":
            if z[1] in lebend:
                bestand.loesche_nr(z[1])
                del lebend[z[1]]
            je_zeile.append(None)
            continue
        _, c, liste = z
        u = pruefe_hinweise(lebend, c, liste)
        gelesen += u.gelesen
        je_zeile.append(u)
        if not u.ok:
            return {"ok": False, "gelesen": gelesen, "fehler_zeile": pos, "grund": u.grund, "je_zeile": je_zeile}
        nr = bestand.hinzu(c)
        lebend[nr] = tuple(c)
        if not c:
            return {"ok": True, "gelesen": gelesen, "fehler_zeile": None, "grund": "ok", "je_zeile": je_zeile}
    return {"ok": False, "gelesen": gelesen, "fehler_zeile": None, "grund": "das Protokoll endet ohne leere Klausel", "je_zeile": je_zeile}
