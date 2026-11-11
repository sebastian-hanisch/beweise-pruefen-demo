"""Die kopierten Kern-Module sind unverändert gegenüber der Kern-Version, die im Modulkopf steht (Hash der Datei ohne Kopfzeilen und mit rückübersetzten Importen).

`bwp_rng.py`, `bwp_instanzen.py`, `bwp_cdcl.py` und `bwp_rup.py` sind wörtliche Kopien von `rng.py`, `instanzen.py`, `cdcl.py` und `rup.py` aus `sat-cp-planung/kern/`
(Kopiervorschrift: `tools/kern_kopieren.py`); geändert sind nur die Importe der Geschwistermodule und die zwei Kopfzeilen."""

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODULE = ["rng", "instanzen", "cdcl", "rup"]


def _kern_text(modul: str) -> tuple[str, str]:
    """(Kern-Version aus dem Kopf, Text im Zustand des Kerns)."""
    text = (ROOT / f"bwp_{modul}.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    version = re.match(r"# Herkunft: Kopie von sat-cp-planung/kern/\w+\.py \(Kern-Version ([0-9a-f]{16})", text).group(1)
    zeilen = text.split("\n")
    i = 0
    while zeilen[i].startswith("#"):
        i += 1
    text = "\n".join(zeilen[i:])
    return version, text.replace("from bwp_rng import", "from rng import")


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_der_kern_version(modul):
    version, text = _kern_text(modul)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] == version


def test_kern_version_stimmt_mit_dem_kern_ueberein_falls_vorhanden():
    """Liegt der Kern daneben (Arbeitsbaum des Autors), steht dieselbe Version in `HASHES.txt`; in der CI fehlt der Ordner, dann entfällt der Vergleich."""
    hashes = ROOT.parent / "sat-cp-planung" / "kern" / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("sat-cp-planung/kern nicht vorhanden")
    soll = {name.removesuffix(".py"): h for h, name in (z.split() for z in hashes.read_text(encoding="utf-8").splitlines())}
    for modul in MODULE:
        assert _kern_text(modul)[0] == soll[modul]


def test_kopien_importieren_nichts_aus_dem_kern_oder_anderen_demos():
    for modul in MODULE:
        quelle = (ROOT / f"bwp_{modul}.py").read_text(encoding="utf-8")
        for zeile in quelle.splitlines():
            if zeile.startswith(("import ", "from ")):
                name = zeile.split()[1]
                assert name in {"heapq", "itertools", "dataclasses", "typing", "bwp_rng"}, (modul, zeile)
