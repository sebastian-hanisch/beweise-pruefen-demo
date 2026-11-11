"""Erzeugt `bwp_messreihen.json`: die vorgerechneten Zeilen, die die App zeigt, aber nicht live rechnet.

  * Schubfach h = 7 (4 811 Konflikte ohne Löschen; der einfache Prüfer braucht dafür mehrere Zehnersekunden) mit und ohne Löschzeilen,
  * Beweisgröße gegen Konflikte für Zufalls-3-SAT n = 60, 70 und 80 (je 20 unerfüllbare Formeln, wie die Live-Reihe n = 30 bis 50).

Aufruf (aus dem Repo-Ordner): `_venvs/test/Scripts/python.exe -X utf8 tools/messreihen.py [--ohne-h7-mit]`. `--ohne-h7-mit` lässt die Messung mit Löschzeilen für h = 7
aus (sie hat 94 529 Zeilen und braucht deutlich länger). Gezählt wird nur in Konflikten, Zeilen, Prüfschritten und Propagationen, nie in Sekunden; die Datei ist
vollständig deterministisch (SplitMix64, feste Zufalls-Seeds, ganzzahlige Zähler)."""

import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import bwp_algorithm as A  # noqa: E402
import bwp_constants as C  # noqa: E402
import bwp_scenario as S  # noqa: E402

VORGERECHNET_N = (60, 70, 80)


def main(mit_h7_loeschen: bool = True):
    f7 = S.schubfach(C.SCHUBFACH_VORGERECHNET)
    print(f"Schubfach h = {C.SCHUBFACH_VORGERECHNET} ohne Löschen ...", flush=True)
    ohne = A.messe_formel(f7, False, C.LOESCH_TAKT, C.BUDGET_VORGERECHNET)
    mit = None
    if mit_h7_loeschen:
        print(f"Schubfach h = {C.SCHUBFACH_VORGERECHNET} mit Löschen (Takt {C.LOESCH_TAKT}) ...", flush=True)
        mit = A.messe_formel(f7, True, C.LOESCH_TAKT, C.BUDGET_VORGERECHNET)
    schubfach = [{"h": C.SCHUBFACH_VORGERECHNET, "variablen": f7.n, "klauseln": len(f7.klauseln), "ohne": ohne, "mit": mit, "vorgerechnet": True}]
    zufall = []
    for n in VORGERECHNET_N:
        print(f"Zufalls-3-SAT n = {n} ...", flush=True)
        zeile = A.messreihe_zufall((n,), C.FORMELN_JE_N)[0]
        zeile["vorgerechnet"] = True
        zufall.append(zeile)
    daten = {"erzeugt_mit": "tools/messreihen.py", "loesch_takt": C.LOESCH_TAKT, "budget": C.BUDGET_VORGERECHNET, "formeln_je_n": C.FORMELN_JE_N, "mess_seed_start": C.MESS_SEED_START,
             "schubfach": schubfach, "zufall": zufall}
    (HIER / C.MESSREIHEN_DATEI).write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("geschrieben:", C.MESSREIHEN_DATEI)


if __name__ == "__main__":
    main("--ohne-h7-mit" not in sys.argv)
