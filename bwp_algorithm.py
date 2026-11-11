"""Kern der Demo: Löser mit Protokoll, Prüfer-Anbindung, unabhängige Wahrheit, Solidität, Manipulation und Messreihen.

Der Löser (`bwp_cdcl`) und der Prüfer (`bwp_rup`, `bwp_pruefer`) sind getrennter Code: `solve(..., proof=True)` schreibt jede gelernte Klausel in ein Protokoll, der Prüfer
rechnet jede Zeile durch Einheitspropagation nach. Die **Wahrheit** einer Klausel („folgt sie aus der Formel?“) kommt unabhängig vom Prüfer: durch Aufzählung aller
Belegungen (bis `AUFZAEHLUNG_MAX_N` Variablen) oder durch den Löser auf „Formel plus verneinte Klausel“. Aufwand wird gezählt (Konflikte, Zeilen, Prüfschritte,
Propagationen), nie in Sekunden gemessen."""

from statistics import median
from typing import NamedTuple

import bwp_constants as C
import bwp_pruefer as P
import bwp_scenario as S
from bwp_cdcl import solve
from bwp_instanzen import pruefe_modell
from bwp_rng import SplitMix64
from bwp_rup import ist_rup, pruefe_beweis


# ------------------------------------------------------------------------------------------------------------------------------ Löser mit Protokoll

def loese(formel, loeschen: bool = False, takt: int = C.LOESCH_TAKT, budget: int = C.BUDGET):
    """Der Löser mit Protokoll (`Ergebnis.beweis`); mit `loeschen` kommen Löschzeilen dazu."""
    return solve(formel.n, [list(c) for c in formel.klauseln], proof=True, delete=loeschen, delete_every=takt, conflict_budget=budget)


def naechste_unerfuellbare(n: int, seed: int, versuche: int = C.SUCH_VERSUCHE, budget: int = C.BUDGET):
    """Die erste unerfüllbare Zufallsformel (n Variablen, 4,26 n Klauseln) unter den Zufalls-Seeds seed, seed + 1, ...; Rückgabe (Formel, benutzter Seed) oder None."""
    for s in range(seed, seed + versuche):
        f = S.zufallsformel(n, s)
        if solve(f.n, [list(c) for c in f.klauseln], conflict_budget=budget).antwort is False:
            return f, s
    return None


class Lauf(NamedTuple):
    formel: object
    antwort: object              # True, False oder None (Budget)
    stat: dict
    protokoll: tuple             # ((art, klausel), ...)
    befund: object               # P.Befund bei "unerfüllbar", sonst None
    modell_ok: object            # bei "erfüllbar": das Modell erfüllt alle Klauseln (Zeuge); sonst None


def lauf(formel, loeschen: bool = False, takt: int = C.LOESCH_TAKT, budget: int = C.BUDGET) -> Lauf:
    """Löser und Prüfer in einem Aufruf. Bei „unerfüllbar“ prüft `bwp_pruefer.pruefe_protokoll` das Protokoll, bei „erfüllbar“ wird das Modell gegen die Klauseln gelesen."""
    e = loese(formel, loeschen, takt, budget)
    protokoll = tuple((a, tuple(c)) for a, c in e.beweis)
    if e.antwort is False:
        return Lauf(formel, False, e.stat, protokoll, P.pruefe_protokoll(formel.klauseln, protokoll), None)
    if e.antwort is True:
        return Lauf(formel, True, e.stat, protokoll, None, pruefe_modell(formel.klauseln, e.modell))
    return Lauf(formel, None, e.stat, protokoll, None, None)


def lemma_literale(protokoll) -> int:
    """Summe der Längen aller hinzugefügten Zeilen (die leere Klausel zählt 0)."""
    return sum(len(c) for a, c in protokoll if a == "a")


def max_lebend(klauseln, protokoll) -> int:
    """Größte Zahl lebender Klauseln während des Protokolls (alle Zeilen als angenommen gelesen)."""
    bestand = P.Bestand(klauseln)
    hoechst = bestand.anzahl()
    for art, c in protokoll:
        if art == "d":
            bestand.loesche(c)
        else:
            bestand.hinzu(c)
            hoechst = max(hoechst, bestand.anzahl())
    return hoechst


# ------------------------------------------------------------------------------------------------------------------------------ unabhängige Wahrheit

def modelle(n: int, klauseln) -> list:
    """Alle Modelle als Zahlen: Bit i - 1 gesetzt heißt Variable i wahr. Nur bis `AUFZAEHLUNG_MAX_N` Variablen."""
    if n > C.AUFZAEHLUNG_MAX_N:
        raise ValueError(f"Aufzählung nur bis {C.AUFZAEHLUNG_MAX_N} Variablen (n = {n})")
    masken = []
    for c in klauseln:
        pos = sum(1 << (l - 1) for l in c if l > 0)
        neg = sum(1 << (-l - 1) for l in c if l < 0)
        masken.append((pos, neg))
    voll = (1 << n) - 1
    return [m for m in range(1 << n) if all((m & pos) or ((~m & voll) & neg) for pos, neg in masken)]


def folgt_aufzaehlung(n: int, modell_liste, klausel) -> bool:
    """Wahr, wenn jedes Modell die Klausel erfüllt (bei keinem Modell trivial wahr)."""
    pos = sum(1 << (l - 1) for l in klausel if l > 0)
    neg = sum(1 << (-l - 1) for l in klausel if l < 0)
    voll = (1 << n) - 1
    return all((m & pos) or ((~m & voll) & neg) for m in modell_liste)


def folgt_loeser(n: int, klauseln, klausel, budget: int = 100000) -> bool:
    """Wahr, wenn „Formel plus verneinte Klausel“ unerfüllbar ist (der Löser entscheidet); bei erreichtem Budget ValueError."""
    antwort = solve(n, [list(c) for c in klauseln] + [[-l] for l in klausel], conflict_budget=budget).antwort
    if antwort is None:
        raise ValueError("der Löser hat die Wahrheit der Klausel nicht entschieden (Konfliktbudget erreicht)")
    return antwort is False


class Wahrheit:
    """Unabhängige Wahrheit zu einer festen Formel: `weg` ist „aufzaehlung“ (n ≤ 14; die Modelle werden einmal aufgezählt) oder „loeser“."""

    def __init__(self, n: int, klauseln, weg: str = "auto"):
        self.n, self.klauseln = n, [tuple(c) for c in klauseln]
        self.weg = ("aufzaehlung" if n <= C.AUFZAEHLUNG_MAX_N else "loeser") if weg == "auto" else weg
        self.modelle = modelle(n, self.klauseln) if self.weg == "aufzaehlung" else None

    def folgt(self, klausel) -> bool:
        if self.weg == "aufzaehlung":
            return folgt_aufzaehlung(self.n, self.modelle, klausel)
        return folgt_loeser(self.n, self.klauseln, klausel)


def wahrheit(n: int, klauseln, klausel, weg: str = "auto") -> bool:
    """Einzelne Wahrheit: folgt `klausel` aus der Formel? (Für viele Klauseln einer Formel `Wahrheit` benutzen.)"""
    return Wahrheit(n, klauseln, weg).folgt(klausel)


# ------------------------------------------------------------------------------------------------------------------------------ Solidität

class Tafel(NamedTuple):
    akzeptiert_folgt: int
    akzeptiert_folgt_nicht: int      # der Fehlerfall: ein Prüfer, der Falsches annimmt
    abgelehnt_folgt: int             # erlaubt: RUP ist strenger als Folgerung
    abgelehnt_folgt_nicht: int
    beispiele: dict                  # Zelle -> erste Klausel
    fehler: tuple                    # alle Klauseln der Zelle „akzeptiert, folgt nicht“

    @property
    def summe(self) -> int:
        return self.akzeptiert_folgt + self.akzeptiert_folgt_nicht + self.abgelehnt_folgt + self.abgelehnt_folgt_nicht

    def zellen(self) -> tuple:
        return (self.akzeptiert_folgt, self.akzeptiert_folgt_nicht, self.abgelehnt_folgt, self.abgelehnt_folgt_nicht)


def soliditaet(n: int, klauseln, kandidaten, weg: str = "auto", pruefer=ist_rup) -> Tafel:
    """Vierfeldertafel: Urteil des Prüfers (RUP gegen die Formel) gegen die unabhängige Wahrheit. `pruefer` ist austauschbar (ein absichtlich fehlerhafter Prüfer in den Tests)."""
    w = Wahrheit(n, klauseln, weg)
    zaehler = {(True, True): 0, (True, False): 0, (False, True): 0, (False, False): 0}
    beispiele, fehler = {}, []
    for c in kandidaten:
        akz, fo = bool(pruefer([list(x) for x in klauseln], list(c))), w.folgt(c)
        zaehler[(akz, fo)] += 1
        beispiele.setdefault((akz, fo), tuple(c))
        if akz and not fo:
            fehler.append(tuple(c))
    return Tafel(zaehler[(True, True)], zaehler[(True, False)], zaehler[(False, True)], zaehler[(False, False)], beispiele, tuple(fehler))


def alle_zweierklauseln(n: int) -> list:
    """Alle Klauseln aus zwei Literalen über verschiedenen Variablen (C(n, 2) mal 4 Vorzeichen), in fester Reihenfolge."""
    return [(sa * a, sb * b) for a in range(1, n + 1) for b in range(a + 1, n + 1) for sa in (1, -1) for sb in (1, -1)]


def zufallskandidaten(n: int, klauseln, anzahl: int, seed: int) -> list:
    """Kandidatenklauseln: je Zug eine Münze entscheidet zwischen einer zufälligen 2- oder 3-Klausel (meist nicht gefolgert) und der Resolvente zweier Formelklauseln
    (immer gefolgert); Resolventen mit Tautologie oder ohne Pivot werden übersprungen, deshalb kann die Liste kürzer als `anzahl` sein. Rückgabe [(Art, Klausel)]."""
    rng = SplitMix64(seed)
    ergebnis = []
    for _ in range(anzahl):
        if rng.coin():
            vs = rng.sample(range(1, n + 1), 2 + rng.below(2))
            ergebnis.append(("zufällig", tuple(v if rng.coin() else -v for v in vs)))
        else:
            c1, c2 = rng.sample(list(klauseln), 2)
            pivots = [l for l in c1 if -l in c2]
            if not pivots:
                continue
            p = pivots[0]
            c = list(dict.fromkeys([l for l in c1 if l != p] + [l for l in c2 if l != -p]))
            if any(-l in c for l in c):
                continue
            ergebnis.append(("Resolvente", tuple(c)))
    return ergebnis


def soliditaet_reihe(formeln: int = C.SOL_FORMELN, n: int = C.SOL_N, m: int = C.SOL_M, seed_start: int = C.SOL_SEED_START,
                     kandidaten_je_formel: int = C.SOL_KANDIDATEN, rng_seed: int = C.SOL_RNG_SEED, weg: str = "loeser", pruefer=ist_rup) -> dict:
    """Solidität an den erfüllbaren unter `formeln` festen Zufallsformeln (n Variablen, m Klauseln); Wahrheit durch den Löser (n > 14) oder Aufzählung.
    Rückgabe: Tafeln je Art („zufällig“, „Resolvente“) und gesamt, Zahl der Formeln, Zahl der Kandidaten, Liste der Fehlerklauseln."""
    nach_art = {"zufällig": [0, 0, 0, 0], "Resolvente": [0, 0, 0, 0]}
    erfuellbar = kandidaten = 0
    fehler = []
    for k in range(formeln):
        f = S.zufallsformel(n, seed_start + k, m)
        if solve(f.n, [list(c) for c in f.klauseln], conflict_budget=C.BUDGET).antwort is not True:
            continue
        erfuellbar += 1
        # ein eigener Kandidatenstrom je Formel: der Zufalls-Seed der Reihe plus Formelnummer
        liste = zufallskandidaten(n, f.klauseln, kandidaten_je_formel, rng_seed + k)
        w = Wahrheit(n, f.klauseln, weg)
        for art, c in liste:
            akz, fo = bool(pruefer([list(x) for x in f.klauseln], list(c))), w.folgt(c)
            idx = 0 if (akz and fo) else 1 if akz else 2 if fo else 3
            nach_art[art][idx] += 1
            kandidaten += 1
            if akz and not fo:
                fehler.append((seed_start + k, tuple(c)))
    gesamt = [a + b for a, b in zip(nach_art["zufällig"], nach_art["Resolvente"])]
    return {"formeln": formeln, "erfuellbar": erfuellbar, "kandidaten": kandidaten, "nach_art": nach_art, "gesamt": gesamt, "fehler": fehler}


# ------------------------------------------------------------------------------------------------------------------------------ Manipulation

def manipuliere(protokoll, art: str, seed: int):
    """Verändert ein Protokoll an einer Stelle, die der Zufalls-Seed wählt. Rückgabe (neues Protokoll, Beschreibung als Text, betroffene Zeile ab 1 oder None).
    kuerzen: ein Literal einer Zeile mit mindestens zwei Literalen streichen; tauschen: ein Literal einer nichtleeren Zeile umkehren; vertauschen: zwei aufeinanderfolgende
    hinzugefügte Zeilen vertauschen; loeschen: eine hinzugefügte Zeile vor der leeren Klausel weglassen. Gibt es keine passende Zeile, bleibt das Protokoll unverändert."""
    rng = SplitMix64(seed)
    neu = [(a, tuple(c)) for a, c in protokoll]
    adds = [i for i, (a, c) in enumerate(neu) if a == "a"]
    if art == "kuerzen":
        kand = [i for i in adds if len(neu[i][1]) >= 2]
    elif art == "tauschen":
        kand = [i for i in adds if len(neu[i][1]) >= 1]
    elif art == "vertauschen":
        kand = [i for i in range(len(neu) - 1) if neu[i][0] == "a" and neu[i + 1][0] == "a" and neu[i][1] != neu[i + 1][1]]
    elif art == "loeschen":
        kand = [i for i in adds if len(neu[i][1]) >= 1]
    else:
        raise ValueError(f"unbekannte Manipulation: {art}")
    if not kand:
        return neu, "keine passende Zeile: das Protokoll bleibt unverändert", None
    i = kand[rng.below(len(kand))]
    if art in ("kuerzen", "tauschen"):
        c = list(neu[i][1])
        j = rng.below(len(c))
        alt = S.lit_text(c[j])
        if art == "kuerzen":
            del c[j]
            text = f"Zeile {i + 1}: das Literal {alt} gestrichen"
        else:
            c[j] = -c[j]
            text = f"Zeile {i + 1}: das Literal {alt} durch {S.lit_text(c[j])} ersetzt"
        neu[i] = ("a", tuple(c))
    elif art == "vertauschen":
        neu[i], neu[i + 1] = neu[i + 1], neu[i]
        text = f"Zeile {i + 1} und {i + 2} vertauscht"
    else:
        text = f"Zeile {i + 1} ({S.klausel_text(neu[i][1])}) weggelassen"
        del neu[i]
    return neu, text, i + 1


# ------------------------------------------------------------------------------------------------------------------------------ Messreihen

def messe_formel(formel, loeschen: bool = False, takt: int = C.LOESCH_TAKT, budget: int = C.BUDGET):
    """Löser, Prüfer (`bwp_rup.pruefe_beweis`, die Kopie des Kerns) und Zähler einer unerfüllbaren Formel; None, wenn die Formel nicht als unerfüllbar entschieden wird."""
    e = loese(formel, loeschen, takt, budget)
    if e.antwort is not False:
        return None
    ok, geprueft, schritte = pruefe_beweis([list(c) for c in formel.klauseln], e.beweis)
    zeilen = len(e.beweis)
    return {
        "konflikte": e.stat["konflikte"], "zeilen": zeilen, "loeschzeilen": sum(1 for a, _ in e.beweis if a == "d"), "lemma_literale": lemma_literale(e.beweis),
        "schritte": schritte, "propagationen": e.stat["propagationen"], "ok": bool(ok), "geprueft": geprueft, "max_lebend": max_lebend(formel.klauseln, e.beweis),
    }


def messreihe_zufall(n_liste=C.MESS_N, formeln_je_n: int = C.FORMELN_JE_N, seed_start: int = C.MESS_SEED_START, such_max: int = C.MESS_SUCH_MAX,
                     loeschen: bool = False) -> list:
    """Beweisgröße gegen Konflikte: je n die ersten `formeln_je_n` unerfüllbaren Zufallsformeln ab `seed_start` (m = 4,26 n). Eine Zeile je n mit Medianen und Spannen."""
    zeilen = []
    for n in n_liste:
        werte, versuche = [], 0
        for s in range(seed_start, seed_start + such_max):
            if len(werte) >= formeln_je_n:
                break
            versuche += 1
            r = messe_formel(S.zufallsformel(n, s), loeschen)
            if r is not None:
                r["seed"] = s
                werte.append(r)
        zeilen.append(zeile_zufall(n, werte, versuche))
    return zeilen


def zeile_zufall(n: int, werte: list, versuche: int) -> dict:
    """Aggregiert die Einzelmessungen (Liste von `messe_formel`-Ergebnissen) zu einer Zeile der Reihe."""
    def med(key):
        return median(w[key] for w in werte) if werte else None

    je_konflikt = [w["zeilen"] / w["konflikte"] for w in werte if w["konflikte"]]
    je_prop = [w["schritte"] / w["propagationen"] for w in werte if w["propagationen"]]
    return {
        "n": n, "klauseln": S.klauselzahl(n), "formeln": len(werte), "versuche": versuche, "alle_ok": all(w["ok"] for w in werte) if werte else False,
        "ok": sum(1 for w in werte if w["ok"]),
        "konflikte": med("konflikte"), "konflikte_min": min((w["konflikte"] for w in werte), default=None), "konflikte_max": max((w["konflikte"] for w in werte), default=None),
        "zeilen": med("zeilen"), "lemma_literale": med("lemma_literale"), "schritte": med("schritte"),
        "zeilen_je_konflikt": median(je_konflikt) if je_konflikt else None,
        "zeilen_je_konflikt_min": min(je_konflikt, default=None), "zeilen_je_konflikt_max": max(je_konflikt, default=None),
        "schritte_je_propagation": median(je_prop) if je_prop else None,
        "schritte_je_propagation_min": min(je_prop, default=None), "schritte_je_propagation_max": max(je_prop, default=None),
        "seeds": [w["seed"] for w in werte] if werte and "seed" in werte[0] else [],
    }


def messreihe_schubfach(h_liste=C.SCHUBFACH_H) -> list:
    """Beweisgröße des Schubfachs mit und ohne Löschzeilen (Löschtakt `LOESCH_TAKT`); eine Zeile je h mit zwei Messungen."""
    zeilen = []
    for h in h_liste:
        f = S.schubfach(h)
        ohne, mit = messe_formel(f, False), messe_formel(f, True)
        zeilen.append({"h": h, "variablen": f.n, "klauseln": len(f.klauseln), "ohne": ohne, "mit": mit, "vorgerechnet": False})
    return zeilen


def gegenbeispiel(n: int, klauseln, klausel, budget: int = 100000):
    """Ein Modell der Formel, das `klausel` verletzt (Beleg dafür, dass sie nicht folgt); None, wenn die Klausel folgt oder der Löser nichts entscheidet."""
    e = solve(n, [list(c) for c in klauseln] + [[-l] for l in klausel], conflict_budget=budget)
    return e.modell if e.antwort is True else None


# ------------------------------------------------------------------------------------------------------------------------------ Hinweise (Ausblick)

def hinweis_beispiel(quelle: str = "suche", variante: str = "normal") -> dict:
    """Das Handbeispiel PHP(2) (Beweis A bis E) mit Hinweisen statt Suche. `quelle`: „suche“ (Hinweise aus der Einheitskette erzeugt) oder „hand“ (von Hand geordnete Listen).
    `variante`: „normal“, „loeschen“ (die Klausel 4 = (¬x1 ∨ ¬x3) wird vor Zeile C gelöscht) oder „falsch“ (in Zeile C steht Klausel 1 statt 4 unter den Hinweisen).
    Rückgabe: {"zeilen": [Zeilen mit Hinweisen], "hinweis": Urteil des Hinweisprüfers (dict), "suche": Befund der Suche, "je_zeile": [dict je gelesener Zeile]}."""
    f = S.php2()
    protokoll = [("a", tuple(c)) for c in C.HB_BEWEIS]
    if quelle == "hand":
        zeilen = [("a", c, list(h)) for (_, c), h in zip(protokoll, C.HB_HINWEISE_VON_HAND)]
    elif quelle == "suche":
        zeilen = P.hinweisprotokoll(f.klauseln, protokoll)
    else:
        raise ValueError(f"unbekannte Quelle: {quelle}")
    suche_protokoll = list(protokoll)
    if variante == "loeschen":
        zeilen.insert(2, ("d", 4))
        suche_protokoll.insert(2, ("d", tuple(f.klauseln[3])))
    elif variante == "falsch":
        a, c, h = zeilen[2]
        zeilen[2] = (a, c, [1 if x == 4 else x for x in h])
    elif variante != "normal":
        raise ValueError(f"unbekannte Variante: {variante}")
    hb = P.pruefe_hinweisprotokoll(f.klauseln, zeilen)
    sb = P.pruefe_protokoll(f.klauseln, suche_protokoll)
    je_zeile = []
    for i, z in enumerate(zeilen):
        if i >= len(hb["je_zeile"]):
            break
        u = hb["je_zeile"][i]
        s = sb.zeilen[i] if i < len(sb.zeilen) else None
        je_zeile.append({"pos": i + 1, "art": z[0], "klausel": tuple(z[1]) if z[0] == "a" else None, "nummer": z[1] if z[0] == "d" else None,
                         "hinweise": z[2] if z[0] == "a" else None,
                         "hinweise_ok": True if u is None else u.ok, "gelesen": 0 if u is None else u.gelesen, "grund": "" if u is None else u.grund,
                         "suche_ok": True if s is None else s.ok, "schritte": 0 if s is None else s.schritte})
    return {"zeilen": zeilen, "hinweis": hb, "suche": sb, "je_zeile": je_zeile}


def lauf_mit_protokoll(formel, protokoll, budget: int = C.BUDGET) -> Lauf:
    """Wie `lauf`, aber der Prüfer liest ein vorgegebenes Protokoll (zum Beispiel den Handbeweis A bis E) statt dem des Lösers; Antwort und Zähler stammen vom Löser."""
    e = loese(formel, False, C.LOESCH_TAKT, budget)
    protokoll = tuple((a, tuple(c)) for a, c in protokoll)
    return Lauf(formel, e.antwort, e.stat, protokoll, P.pruefe_protokoll(formel.klauseln, protokoll) if e.antwort is False else None, None)
