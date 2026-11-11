"""Kopiert die Kern-Module rng, instanzen, cdcl und rup aus `sat-cp-planung/kern/` nach `bwp_<modul>.py` (wörtlich, nur die Importe der
Geschwistermodule auf `bwp_` umgestellt, dazu zwei Kopfzeilen mit Herkunft und Kern-Version).

Aufruf (aus dem Repo-Ordner): `python tools/kern_kopieren.py`. Danach prüft `tests/test_copies.py`, dass jede Kopie nach Rückübersetzung der Importe
und ohne Kopfzeilen dem Kern-Hash aus `HASHES.txt` entspricht. Die Kopien nicht von Hand ändern."""

import hashlib
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
KERN = HIER.parent / "sat-cp-planung" / "kern"
MODULE = ("rng", "instanzen", "cdcl", "rup")
ERSETZUNGEN = {"from rng import": "from bwp_rng import"}
DATUM = "2026-11-10"


def kopiere():
    hashes = {}
    for zeile in (KERN / "HASHES.txt").read_text(encoding="utf-8").splitlines():
        h, name = zeile.split()
        hashes[name] = h
    for modul in MODULE:
        text = (KERN / f"{modul}.py").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        gelesen = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        assert gelesen == hashes[f"{modul}.py"], f"{modul}.py weicht von HASHES.txt ab"
        for alt, neu in ERSETZUNGEN.items():
            text = text.replace(alt, neu)
        kopf = (f"# Herkunft: Kopie von sat-cp-planung/kern/{modul}.py (Kern-Version {gelesen}, Datei HASHES.txt vom {DATUM}), "
                "nur Importe auf bwp_ umgestellt.\n"
                "# Nicht von Hand ändern: tests/test_copies.py vergleicht diese Datei mit dem Kern-Hash.\n")
        (HIER / f"bwp_{modul}.py").write_text(kopf + text, encoding="utf-8", newline="\n")
        print(f"bwp_{modul}.py  Kern-Version {gelesen}")


if __name__ == "__main__":
    kopiere()
