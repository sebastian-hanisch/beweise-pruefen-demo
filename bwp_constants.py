"""Konstanten: Regler-Grenzen, Familien der Formeln, feste Zufalls-Seeds, Farben und Presets."""

FAMILIE_PHP2 = "Handbeispiel PHP(2)"
FAMILIE_G = "Erfüllbare Formel G"
FAMILIE_ZUFALL = "Zufalls-3-SAT (unerfüllbar)"
FAMILIE_SCHUBFACH = "Schubfach"
FAMILIEN = (FAMILIE_PHP2, FAMILIE_ZUFALL, FAMILIE_G, FAMILIE_SCHUBFACH)

N_MIN, N_MAX, DEFAULT_N = 10, 50, 20            # Variablen der Zufallsformel (Familie Zufalls-3-SAT)
H_MIN, H_MAX, DEFAULT_H = 3, 6, 5               # Schubfach: h + 1 Tauben, h Löcher; h = 7 nur vorgerechnet
SEED_MAX, DEFAULT_SEED = 999999, 7000
DICHTE = 4.26                                   # Klauseln je Variable der Zufallsformeln (Schwelle der Erfüllbarkeit, gerundet auf ganze Klauselzahlen)
SUCH_VERSUCHE = 500                             # so viele Zufalls-Seeds ab dem gewählten werden nach der ersten unerfüllbaren Formel durchsucht
BUDGET = 20000                                  # Konfliktbudget jeder Suche; ein Lauf, der es erreicht, gilt als nicht entschieden
LOESCH_TAKT = 100                               # alle so viele Konflikte fällt die schlechtere Hälfte der gelernten Klauseln weg (nur mit „Löschen an“)
LOESCHEN_AUS, LOESCHEN_AN = "aus", "an"
QUELLE_HAND, QUELLE_LOESER = "hand", "loeser"   # Protokoll des Handbeispiels: von Hand (Zeilen A bis E) oder vom Löser geschrieben

# Messreihe 1 (Beweisgröße gegen Konflikte): je n die ersten FORMELN_JE_N unerfüllbaren Formeln ab Zufalls-Seed MESS_SEED_START
MESS_N = (30, 40, 50)
FORMELN_JE_N = 20
MESS_SEED_START = 7000
MESS_SUCH_MAX = 400                             # höchstens so viele Seeds je n werden durchsucht

# Messreihe 2 (Schubfach)
SCHUBFACH_H = (3, 4, 5, 6)
SCHUBFACH_VORGERECHNET = 7                      # h = 7 steht vorgerechnet in bwp_messreihen.json (tools/messreihen.py)
BUDGET_VORGERECHNET = 100000                    # Konfliktbudget der vorgerechneten Läufe (h = 7 mit Löschzeilen braucht mehr als das Live-Budget BUDGET)
MESSREIHEN_DATEI = "bwp_messreihen.json"

# Solidität an erfüllbaren Formeln (Zufalls-3-SAT, n = 30, m = 100)
SOL_N, SOL_M = 30, 100
SOL_FORMELN = 25                                # Zufalls-Seeds SOL_SEED_START bis SOL_SEED_START + 24; nur die erfüllbaren zählen
SOL_SEED_START = 1200
SOL_KANDIDATEN = 60                             # Kandidatenklauseln je Formel
SOL_RNG_SEED = 11                               # Zufalls-Seed des Kandidatenstroms
AUFZAEHLUNG_MAX_N = 14                          # bis zu dieser Variablenzahl wird die Wahrheit durch Aufzählung aller Belegungen bestimmt, darüber durch den Löser

# Handbeispiel (von Hand nachgerechnet): Beweis von PHP(2) in fünf Zeilen A bis E, dazu die Hinweislisten von Hand (Klauselnummern: Formel 1 bis 9, Lemmas A bis E = 10 bis 14)
HB_BEWEIS = ((-1, -4), (-2, -3), (-1,), (-2,), ())
HB_NAMEN = "ABCDE"
HB_HINWEISE_VON_HAND = ((4, 5, 7, 9, 3), (7, 8, 4, 6, 3), (10, 2, 4), (11, 2, 7), (12, 13, 1))

MANIPULATIONEN = ("kuerzen", "tauschen", "vertauschen", "loeschen")
MANIPULATION_NAMEN = {
    "kuerzen": "Ein Literal einer Zeile streichen",
    "tauschen": "Ein Literal einer Zeile umkehren (x statt ¬x)",
    "vertauschen": "Zwei Zeilen vertauschen",
    "loeschen": "Eine Zeile weglassen",
}

COLOR_OK = "#2F6B65"
COLOR_FEHLER = "#c0504d"
COLOR_LINE = "#4c78a8"
COLOR_GRAU = "#9a9a9a"

PRESETS = {
    "Handbeispiel PHP(2)": {"familie": FAMILIE_PHP2, "n": DEFAULT_N, "h": DEFAULT_H, "loeschen": LOESCHEN_AUS, "quelle": QUELLE_HAND, "seed": DEFAULT_SEED},
    "Kleine Zufallsformel (n = 20)": {"familie": FAMILIE_ZUFALL, "n": 20, "h": DEFAULT_H, "loeschen": LOESCHEN_AUS, "quelle": QUELLE_HAND, "seed": DEFAULT_SEED},
    "Erfüllbare Formel G": {"familie": FAMILIE_G, "n": DEFAULT_N, "h": DEFAULT_H, "loeschen": LOESCHEN_AUS, "quelle": QUELLE_HAND, "seed": DEFAULT_SEED},
    "Schubfach h = 5": {"familie": FAMILIE_SCHUBFACH, "n": DEFAULT_N, "h": 5, "loeschen": LOESCHEN_AUS, "quelle": QUELLE_HAND, "seed": DEFAULT_SEED},
}
PRESET_HELP = {
    "Handbeispiel PHP(2)": "3 Tauben, 2 Löcher, 6 Variablen, 9 Klauseln: unerfüllbar. Der Beweis hat fünf Zeilen (A bis E), die letzte ist die leere Klausel; jede Zeile lässt sich von Hand nachrechnen.",
    "Kleine Zufallsformel (n = 20)": "Die erste unerfüllbare Zufalls-3-SAT-Formel mit 20 Variablen und 85 Klauseln ab Zufalls-Seed 7000; der Löser schreibt eine Zeile je Konflikt.",
    "Erfüllbare Formel G": "PHP(2) ohne zwei Taubenklauseln: erfüllbar (7 Modelle von 64). Hier ist die Wahrheit jeder Klausel durch Aufzählung der Modelle bekannt: der Ort, an dem man den Prüfer prüft.",
    "Schubfach h = 5": "6 Tauben, 5 Löcher: unerfüllbar, mit einem langen Protokoll. Der einfache Prüfer arbeitet es Zeile für Zeile ab.",
}
