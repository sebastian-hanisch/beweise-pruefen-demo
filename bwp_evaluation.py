"""Kennzahlen, Messreihen und Verdikte. Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; jede Zahl im Text stammt aus der Messung.

Aufwand wird gezählt, nie in Sekunden gemessen: Konflikte, Protokollzeilen, Prüfschritte (geprüfte Klauseln bei der Einheitspropagation des Prüfers), Propagationen des Lösers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import bwp_algorithm as A
import bwp_constants as C
import bwp_scenario as S


@dataclass(frozen=True)
class Settings:
    familie: str = C.FAMILIE_PHP2
    n: int = C.DEFAULT_N
    h: int = C.DEFAULT_H
    loeschen: str = C.LOESCHEN_AUS
    quelle: str = C.QUELLE_HAND
    seed: int = C.DEFAULT_SEED


class Gewaehlt(NamedTuple):
    formel: object
    seed_benutzt: object         # Zufallsformel: der Zufalls-Seed, bei dem die erste unerfüllbare Formel gefunden wurde; sonst None
    gefunden: bool               # False: für diese Einstellung ließ sich keine unerfüllbare Formel finden


def formel_von(settings: Settings) -> Gewaehlt:
    """Die Formel der Einstellung. Zufalls-3-SAT: die erste unerfüllbare Formel unter den Zufalls-Seeds ab dem gewählten."""
    if settings.familie == C.FAMILIE_ZUFALL:
        treffer = A.naechste_unerfuellbare(settings.n, settings.seed)
        if treffer is None:
            return Gewaehlt(S.zufallsformel(settings.n, settings.seed), None, False)
        return Gewaehlt(treffer[0], treffer[1], True)
    return Gewaehlt(S.make_formel(settings.familie, settings.n, settings.h, settings.seed), None, True)


def lauf_von(settings: Settings, g: Gewaehlt):
    """Löser und Prüfer für die Einstellung: beim Handbeispiel mit der Quelle „von Hand“ prüft der Prüfer die fünf Zeilen A bis E, sonst das Protokoll des Lösers."""
    if settings.familie == C.FAMILIE_PHP2 and settings.quelle == C.QUELLE_HAND:
        return A.lauf_mit_protokoll(g.formel, handprotokoll())
    return A.lauf(g.formel, settings.loeschen == C.LOESCHEN_AN)


def de(x: float, stellen: int = 0) -> str:
    """Deutsche Zahlschreibweise: Punkt als Tausendertrenner (ab vier Stellen), Komma als Dezimalzeichen."""
    text = f"{x:,.{stellen}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def antwort_text(antwort) -> str:
    return {True: "erfüllbar", False: "unerfüllbar", None: "nicht entschieden (Budget erreicht)"}[antwort]


def handprotokoll() -> tuple:
    """Der Beweis des Handbeispiels PHP(2) in fünf Zeilen A bis E (letzte Zeile: die leere Klausel)."""
    return tuple(("a", tuple(c)) for c in C.HB_BEWEIS)


def lade_messreihen() -> dict:
    """Die vorgerechneten Zeilen aus `bwp_messreihen.json` (erzeugt mit `tools/messreihen.py`); leer, wenn die Datei fehlt."""
    pfad = Path(__file__).with_name(C.MESSREIHEN_DATEI)
    if not pfad.exists():
        return {"schubfach": [], "zufall": []}
    return json.loads(pfad.read_text(encoding="utf-8"))


def zufall_mit_vorgerechnet(live: list) -> list:
    """Die live gerechneten Zeilen (n = 30 bis 50) und die vorgerechneten (n = 60 bis 80), nach n sortiert; jede Zeile trägt `vorgerechnet`."""
    zeilen = [dict(z, vorgerechnet=False) for z in live] + [dict(z) for z in lade_messreihen()["zufall"]]
    return sorted(zeilen, key=lambda z: z["n"])


def schubfach_mit_vorgerechnet(live: list) -> list:
    zeilen = [dict(z, vorgerechnet=False) for z in live] + [dict(z) for z in lade_messreihen()["schubfach"]]
    return sorted(zeilen, key=lambda z: z["h"])


# ---------------------------------------------------------------------------------------------------------------------------------- Tabellen

def protokoll_tabelle(befund) -> list:
    """Eine Zeile je Protokollzeile bis zur ersten Ablehnung oder zur leeren Klausel; „Urteil“ steht als Wort (Farbe trägt keine Information)."""
    rows = []
    for z in befund.zeilen:
        if z.art == "d":
            urteil = "gelöscht" if not z.unbekannt else "gelöscht (Klausel gab es nicht)"
        else:
            urteil = "akzeptiert" if z.ok else "abgelehnt"
        rows.append({"Zeile": z.pos, "Art": "hinzufügen" if z.art == "a" else "löschen", "Klausel": S.klausel_text(z.klausel), "Länge": len(z.klausel),
                     "Klauselnummer": z.nr if z.nr is not None else None, "Urteil": urteil, "Prüfschritte": z.schritte})
    return rows


def tafel_zeilen(zellen) -> list:
    """Die vier Zellen der Soliditätstafel als Tabellenzeilen: Zeilen = Urteil des Prüfers, Spalten = unabhängige Wahrheit."""
    a, b, c, d = zellen
    return [{"Urteil des Prüfers": "akzeptiert", "folgt aus der Formel": a, "folgt nicht": b},
            {"Urteil des Prüfers": "abgelehnt", "folgt aus der Formel": c, "folgt nicht": d}]


# ---------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_kernfrage(l) -> tuple:
    """Verdikt der Kernfrage zu einem Lauf (`bwp_algorithm.Lauf`): was sagt der Löser, und was sagt der Prüfer dazu?"""
    if l.antwort is None:
        return "warning", (f"Der Löser hat die Formel im Budget von {de(C.BUDGET)} Konflikten nicht entschieden: Es gibt kein vollständiges Protokoll, also nichts zu prüfen.")
    if l.antwort is True:
        if l.modell_ok:
            return "info", (f"Der Löser sagt „erfüllbar“. Dafür braucht es keinen Beweis: Das Modell ist der Zeuge, und die Prüfung liest nur die {len(l.formel.klauseln)} Klauseln "
                            "und fragt je Klausel nach einem wahren Literal; alle bestehen. „Unerfüllbar“ dagegen lässt sich so nicht zeigen.")
        return "error", "Das Modell des Lösers erfüllt nicht alle Klauseln: Das darf nicht vorkommen."
    b = l.befund
    if not b.ok:
        return "error", f"Der Prüfer lehnt das Protokoll ab: {b.grund}."
    loesch = sum(1 for z in b.zeilen if z.art == "d")
    zusatz = f", davon {de(loesch)} Löschzeilen" if loesch else ""
    return "success", (f"Der Löser sagt „unerfüllbar“, und der Prüfer akzeptiert das Protokoll: {de(len(l.protokoll))} Zeilen ({de(b.geprueft)} hinzugefügte Klauseln{zusatz}), "
                       f"{de(b.schritte)} Prüfschritte. Geglaubt wird die Antwort, weil ein zweites, einfaches Programm jede Zeile nachgerechnet hat, nicht weil der Löser sie behauptet.")


def verdict_zeile(info: dict) -> tuple:
    """Verdikt zu einer Zeile des Protokolls (`bwp_pruefer.erklaere_zeile`)."""
    c = info["klausel"]
    db = info["db"]
    if info["art"] == "d":
        if info["geloescht_nr"] is None:
            return "warning", f"Löschzeile für {S.klausel_text(c)}: Eine solche Klausel gab es nicht, die Zeile wird (wie im Kern) ignoriert."
        return "info", (f"Löschzeile: Die Klausel {info['geloescht_nr']} ({S.klausel_text(c)}) wird entfernt; spätere Zeilen dürfen sie nicht mehr benutzen. "
                        f"Davor lebten {de(info['lebende'])} Klauseln.")
    e = info["erklaerung"]
    if e.tautologie:
        return "info", f"Akzeptiert ohne Rechnung: {S.klausel_text(c)} enthält ein Literal und sein Gegenteil und ist immer wahr."
    annahme = ("alle Literale der Zeile falsch (" + ", ".join(f"x{abs(l)} = {'falsch' if l > 0 else 'wahr'}" for l in c) + ")") if c else "nichts (die leere Klausel hat kein Literal)"
    if e.ok:
        return "success", (f"Akzeptiert: Unter der Annahme {annahme} erzwingt die Einheitspropagation {de(len(e.kette))} Literale und verletzt dann die Klausel {e.widerspruch} "
                           f"({S.klausel_text(db[e.widerspruch])}); {de(e.schritte)} Prüfschritte.")
    return "error", (f"Abgelehnt: Unter der Annahme {annahme} erzwingt die Einheitspropagation {de(len(e.kette))} Literale, aber keine Klausel wird verletzt "
                     f"({de(e.schritte)} Prüfschritte). Die Zeile ist damit nicht bewiesen.")


def verdict_groesse(zeilen: list) -> tuple:
    """Verdikt der Beweisgröße: Zeilen und Prüfschritte der größten Zeile der Reihe, mit Spannen und Zahl der akzeptierten Protokolle."""
    if not zeilen or not zeilen[-1]["formeln"]:
        return "warning", "Keine unerfüllbare Formel gefunden: nichts zu messen."
    z = zeilen[-1]
    erste = next(r for r in zeilen if r["formeln"])
    if z["ok"] != z["formeln"]:
        return "error", f"Der Prüfer lehnt {z['formeln'] - z['ok']} von {z['formeln']} Protokollen bei n = {z['n']} ab: Das darf bei einem richtigen Löser nicht vorkommen."
    text = (f"Bei n = {z['n']} Variablen hat das Protokoll im Median {de(z['zeilen'], 1)} Zeilen für {de(z['konflikte'], 1)} Konflikte "
            f"(Zeilen je Konflikt: {de(z['zeilen_je_konflikt_min'], 2)} bis {de(z['zeilen_je_konflikt_max'], 2)}); der Prüfer braucht {de(z['schritte_je_propagation'], 1)} Schritte "
            f"je Löser-Propagation (Spanne {de(z['schritte_je_propagation_min'], 1)} bis {de(z['schritte_je_propagation_max'], 1)}) und akzeptiert alle {z['formeln']} Protokolle.")
    if erste is not z:
        text += (f" Die Prüfschritte je Löser-Propagation liegen bei n = {erste['n']} im Median bei {de(erste['schritte_je_propagation'], 1)}, bei n = {z['n']} "
                 f"bei {de(z['schritte_je_propagation'], 1)}.")
    return "success", text


def verdict_soliditaet(zellen, kandidaten_text: str = "") -> tuple:
    """Verdikt der Soliditätstafel: Erfolg nur, wenn die Zelle „akzeptiert, folgt nicht“ leer ist, sonst Fehleranzeige."""
    a, b, c, d = zellen
    gesamt = a + b + c + d
    if b:
        return "error", f"FEHLER des Prüfers: {de(b)} von {de(gesamt)} Kandidaten wurden akzeptiert, obwohl sie nicht aus der Formel folgen."
    return "success", (f"Der Prüfer hat keine nicht gefolgerte Klausel akzeptiert: 0 von {de(gesamt)} Kandidaten{kandidaten_text}. Er hat {de(a)} gefolgerte Klauseln akzeptiert, "
                       f"{de(c)} gefolgerte abgelehnt (RUP ist strenger als Folgerung) und {de(d)} nicht gefolgerte abgelehnt.")


def verdict_klausel(akzeptiert: bool, folgt: bool) -> tuple:
    """Verdikt zu einer eigenen Klausel: Urteil des Prüfers gegen die unabhängige Wahrheit."""
    if akzeptiert and folgt:
        return "success", "Der Prüfer akzeptiert die Klausel, und sie folgt aus der Formel: richtig."
    if not akzeptiert and not folgt:
        return "success", "Der Prüfer lehnt die Klausel ab, und sie folgt nicht aus der Formel: richtig."
    if not akzeptiert and folgt:
        return "info", ("Der Prüfer lehnt die Klausel ab, obwohl sie aus der Formel folgt: Das ist erlaubt. Einheitspropagation leitet nicht jede Folgerung her "
                        "(RUP ist strenger als Folgerung); ein abgelehntes Lemma braucht dann Zwischenlemmas.")
    return "error", "FEHLER des Prüfers: Er akzeptiert eine Klausel, die nicht aus der Formel folgt."


def verdict_manipulation(befund, beschreibung: str) -> tuple:
    """Verdikt zu einem veränderten Protokoll."""
    if not befund.ok:
        ort = f"in Zeile {befund.fehler_zeile}" if befund.fehler_zeile else "am Ende"
        return "success", f"Veränderung: {beschreibung}. Der Prüfer lehnt das Protokoll ab ({ort}: {befund.grund})."
    return "info", (f"Veränderung: {beschreibung}. Der Prüfer akzeptiert das Protokoll trotzdem: Jede Zeile ist weiter durch Einheitspropagation herleitbar. "
                    "Ob die geänderte Zeile „wahr“ ist, sagt hier nichts, denn in einer unerfüllbaren Formel folgt jede Klausel.")


def verdict_schubfach(zeilen: list) -> tuple:
    """Verdikt der Schubfach-Reihe: Konflikte (gleich Zeilen) ohne Löschen je h, Faktoren je Loch, Wirkung der Löschzeilen am größten h mit beiden Messungen."""
    ok = [z for z in zeilen if z["ohne"] is not None]
    if len(ok) < 2:
        return "warning", "Zu wenige Messungen für einen Vergleich."
    if not all(z["ohne"]["ok"] for z in ok) or not all(z["mit"]["ok"] for z in ok if z["mit"] is not None):
        return "error", "Der Prüfer lehnt ein Protokoll ab: Das darf bei einem richtigen Löser nicht vorkommen."
    faktoren = [b["ohne"]["konflikte"] / a["ohne"]["konflikte"] for a, b in zip(ok, ok[1:])]
    k = ok[0], ok[-1]
    text = (f"Ohne Löschen wächst die Protokollgröße (eine Zeile je Konflikt) von {de(k[0]['ohne']['zeilen'])} Zeilen bei h = {k[0]['h']} auf {de(k[1]['ohne']['zeilen'])} bei h = {k[1]['h']}; "
            f"je zusätzliches Loch um das {de(min(faktoren), 1)}- bis {de(max(faktoren), 1)}-Fache der Konfliktzahl. Der Prüfer akzeptiert alle {len(ok)} Protokolle ohne Löschen.")
    beide = [z for z in ok if z["mit"] is not None and z["mit"]["loeschzeilen"]]
    if beide:
        b = beide[-1]
        text += (f" Mit Löschzeilen (alle {C.LOESCH_TAKT} Konflikte) sucht der Löser bei h = {b['h']} anders: {de(b['mit']['konflikte'])} statt {de(b['ohne']['konflikte'])} Konflikte, "
                 f"{de(b['mit']['zeilen'])} Zeilen, davon {de(b['mit']['loeschzeilen'])} Löschzeilen; der Prüfer hält höchstens {de(b['mit']['max_lebend'])} statt {de(b['ohne']['max_lebend'])} Klauseln "
                 "gleichzeitig am Leben und akzeptiert beide Protokolle.")
    return "success", text


def verdict_hinweise(je_zeile: list) -> tuple:
    """Verdikt des Hinweis-Beispiels: je gelesener Zeile (`hinweise_ok`, `suche_ok`, `gelesen`, `schritte`, `art`, `pos`, `grund`). Beide Prüfer müssen übereinstimmen."""
    if any(z["hinweise_ok"] and not z["suche_ok"] for z in je_zeile):
        return "error", "Der Hinweisprüfer akzeptiert eine Zeile, die die Suche ablehnt: Das darf nicht vorkommen."
    abgelehnt = [z for z in je_zeile if not z["hinweise_ok"] or not z["suche_ok"]]
    if abgelehnt:
        z = abgelehnt[0]
        if not z["suche_ok"]:
            return "success", (f"Beide Prüfer lehnen das Protokoll in Zeile {z['pos']} ab: Der Hinweisprüfer meldet „{z['grund']}“, die Suche findet keinen Widerspruch. "
                               "Die Zeilen danach werden nicht mehr gelesen.")
        return "success", (f"Der Hinweisprüfer lehnt das Protokoll in Zeile {z['pos']} ab („{z['grund']}“), obwohl die Suche die Zeile selbst akzeptieren würde: Ein falscher Hinweis genügt nicht, "
                           "auch wenn die Zeile stimmt. Die Zeilen danach werden nicht mehr gelesen.")
    zeilen_a = [z for z in je_zeile if z["art"] == "a"]
    gelesen = sum(z["gelesen"] for z in zeilen_a)
    schritte = sum(z["schritte"] for z in zeilen_a)
    return "success", (f"Alle {len(zeilen_a)} hinzugefügten Zeilen werden mit Hinweisen und mit der Suche akzeptiert. Der Hinweisprüfer liest zusammen {de(gelesen)} Klauseln, "
                       f"die Suche des einfachen Prüfers braucht {de(schritte)} Prüfschritte. Die Hinweise ersparen die Suche; die Listen hat hier eine Suche erzeugt oder die Handrechnung.")
