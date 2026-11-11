"""Szenario: die Formeln der Demo (Handbeispiel PHP(2), erfüllbare Formel G, Zufalls-3-SAT, Schubfach) und die Schreibweise der Literale und Klauseln.

Eine Formel ist `Formel(n, klauseln, name)`: n Variablen 1..n, Klauseln als Tupel von Literalen (+v wahr, -v falsch). Alle Zufallsformeln laufen über den ganzzahligen
SplitMix64 (`bwp_rng`, über `bwp_instanzen`), nie über Python-`random` oder `hash()`."""

from typing import NamedTuple

import bwp_constants as C
import bwp_instanzen as I


class Formel(NamedTuple):
    n: int
    klauseln: tuple
    name: str


def klauselzahl(n: int, dichte: float = C.DICHTE) -> int:
    """Zahl der Klauseln einer Zufalls-3-SAT-Formel mit Dichte m/n (gerundet)."""
    return int(round(dichte * n))


def php2() -> Formel:
    """Das Handbeispiel: 3 Tauben, 2 Löcher; x1 = (Taube 1, Loch 1), x2 = (1, 2), x3 = (2, 1), x4 = (2, 2), x5 = (3, 1), x6 = (3, 2)."""
    inst = I.pigeonhole(2)
    return Formel(inst.n, tuple(inst.klauseln), "Handbeispiel PHP(2): 3 Tauben, 2 Löcher")


def formel_g() -> Formel:
    """G = PHP(2) ohne die Klauseln (x3 x4) und (x5 x6): erfüllbar, 7 Modelle von 64 (von Hand nachgerechnet)."""
    f = php2()
    return Formel(f.n, tuple(c for c in f.klauseln if c not in ((3, 4), (5, 6))), "Erfüllbare Formel G: PHP(2) ohne die Klauseln (x3 ∨ x4) und (x5 ∨ x6)")


def zufallsformel(n: int, seed: int, m: int | None = None) -> Formel:
    """Zufalls-3-SAT mit n Variablen und m (Standard: 4,26 n, gerundet) Klauseln, deterministisch aus (n, m, seed)."""
    m = klauselzahl(n) if m is None else m
    inst = I.rand3(n, m, seed)
    return Formel(inst.n, tuple(inst.klauseln), f"Zufalls-3-SAT n = {n}, m = {m}, Zufalls-Seed {seed}")


def schubfach(h: int) -> Formel:
    inst = I.pigeonhole(h)
    return Formel(inst.n, tuple(inst.klauseln), f"Schubfach h = {h} ({h + 1} Tauben, {h} Löcher)")


def make_formel(familie: str, n: int = C.DEFAULT_N, h: int = C.DEFAULT_H, seed: int = C.DEFAULT_SEED) -> Formel:
    """Formel ohne Suche (die erste unerfüllbare Zufallsformel ab einem Zufalls-Seed findet `bwp_algorithm.naechste_unerfuellbare`)."""
    if familie == C.FAMILIE_PHP2:
        return php2()
    if familie == C.FAMILIE_G:
        return formel_g()
    if familie == C.FAMILIE_ZUFALL:
        return zufallsformel(n, seed)
    if familie == C.FAMILIE_SCHUBFACH:
        return schubfach(h)
    raise ValueError(f"unbekannte Familie: {familie}")


def lit_text(lit: int) -> str:
    """x3 bzw. ¬x3."""
    return f"x{lit}" if lit > 0 else f"¬x{-lit}"


def klausel_text(klausel) -> str:
    """Klausel als Text; die leere Klausel heißt „()“, ein Widerspruch ohne Literal."""
    return " ∨ ".join(lit_text(l) for l in klausel) if len(klausel) else "()"


def parse_klausel(text: str, n: int):
    """Liest eine Klausel aus Zahlen (+v wahr, -v falsch), getrennt durch Leerzeichen oder Komma, z. B. „-1 -4“. Rückgabe (Klausel, Fehlertext oder None)."""
    teile = text.replace(",", " ").replace("¬", "-").replace("x", "").replace("X", "").split()
    klausel = []
    for t in teile:
        try:
            l = int(t)
        except ValueError:
            return None, f"„{t}“ ist keine Zahl"
        if l == 0 or abs(l) > n:
            return None, f"Variable {abs(l)} gibt es nicht (erlaubt: 1 bis {n})"
        klausel.append(l)
    return tuple(klausel), None
