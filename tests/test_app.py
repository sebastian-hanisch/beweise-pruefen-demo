"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden wirksamen Button (Presets, Zufalls-Seed, die drei Messknöpfe),
fährt jeden wirksamen Regler an seine Grenzen und prüft, dass kein Python-Fehler auftritt - insbesondere `StreamlitDuplicateElementId` (mehrere st.plotly_chart ohne eindeutiges key=)
und `StreamlitAPIException` bei Reglern und Zeilenwahl. Gesperrte Regler lassen sich auch im AppTest nicht ändern; sie werden mit dem Preset ihrer Familie freigeschaltet
(siehe tests/test_layout.py)."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import bwp_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
MESSKNOEPFE = ("groesse_knopf", "sol_knopf", "schub_knopf")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _preset(at, familie):
    name = next(n for n, p in C.PRESETS.items() if p["familie"] == familie)
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at):
    return " ".join(e.value for kind in (at.success, at.info, at.warning, at.error) for e in kind)


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    knoepfe = [(index, b.label) for index, b in enumerate(_fresh_app().button) if not b.disabled]     # der Zufalls-Seed-Knopf ist beim Handbeispiel gesperrt
    assert len(knoepfe) >= len(C.PRESETS) + len(MESSKNOEPFE), "Presets und Messknöpfe fehlen"
    for index, label in knoepfe:
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_zufalls_seed_knopf_ist_fuer_zufallsformeln_wirksam():
    at = _preset(_fresh_app(), C.FAMILIE_ZUFALL)
    assert not at.sidebar.button[-1].disabled
    alt = at.sidebar.number_input(key="seed_input").value
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception and at.sidebar.number_input(key="seed_input").value != alt


@pytest.mark.parametrize("familie", [C.FAMILIE_ZUFALL, C.FAMILIE_SCHUBFACH])
def test_every_active_slider_at_its_min_and_max_does_not_raise(familie):
    probe = _preset(_fresh_app(), familie)
    aktiv = [s.key for s in probe.sidebar.slider if not s.disabled]
    assert aktiv, "kein wirksamer Regler"
    for key in aktiv:
        for edge in ("min", "max"):
            at = _preset(_fresh_app(), familie)
            slider = at.sidebar.slider(key=key)
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (familie, key, edge, [str(e) for e in at.exception])


def test_seed_und_loeschzeilen_und_quelle_aendern_die_ergebnisse():
    at = _preset(_fresh_app(), C.FAMILIE_SCHUBFACH)
    assert [m.value for m in at.metric][:4] == ["unerfüllbar", "akzeptiert", "159", "64.154"]
    at.sidebar.radio(key="loeschen_radio").set_value(C.LOESCHEN_AN).run(timeout=TIMEOUT)
    assert [m.value for m in at.metric][:4] == ["unerfüllbar", "akzeptiert", "212", "64.896"]
    at = _preset(_fresh_app(), C.FAMILIE_PHP2)
    at.sidebar.radio(key="quelle_radio").set_value(C.QUELLE_LOESER).run(timeout=TIMEOUT)
    assert [m.value for m in at.metric][:4] == ["unerfüllbar", "akzeptiert", "2", "44"]
    at = _preset(_fresh_app(), C.FAMILIE_ZUFALL)
    assert [m.value for m in at.metric][:4] == ["unerfüllbar", "akzeptiert", "22", "5.404"]
    at.sidebar.number_input(key="seed_input").set_value(C.SEED_MAX).run(timeout=TIMEOUT)
    assert not at.exception and at.metric[0].value in ("unerfüllbar", "erfüllbar")


def test_erfuellbare_formel_g_hat_kein_protokoll_und_der_zeugenhinweis_steht_da():
    at = _preset(_fresh_app(), C.FAMILIE_G)
    assert [m.value for m in at.metric][:4] == ["erfüllbar", "Modell geprüft", "–", "–"]
    assert "Das Modell ist der Zeuge" in _texte(at) and "kein Protokoll" in _texte(at)


def test_die_zeilenwahl_zeigt_die_erklaerung_und_bleibt_beim_formelwechsel_gueltig():
    at = _fresh_app()
    at.number_input(key="zeile_nr").set_value(1).run(timeout=TIMEOUT)
    assert "Klausel 3 (x5 ∨ x6)" in _texte(at) and "12 Prüfschritte" in _texte(at)
    at.number_input(key="zeile_nr").set_value(5).run(timeout=TIMEOUT)
    assert "nichts (die leere Klausel hat kein Literal)" in _texte(at)
    at = _preset(_fresh_app(), C.FAMILIE_SCHUBFACH)
    at.number_input(key="zeile_nr").set_value(150).run(timeout=TIMEOUT)
    assert not at.exception
    _preset(at, C.FAMILIE_PHP2)                                                    # der Zustand 150 liegt über dem Maximum des Handbeispiels: wird begrenzt
    assert not at.exception and at.number_input(key="zeile_nr").value <= 5


def test_die_messknoepfe_rechnen_und_zeigen_ein_verdikt():
    at = _fresh_app()
    for key in MESSKNOEPFE:
        at.button(key=key).click().run(timeout=TIMEOUT)
        assert not at.exception, (key, [str(e) for e in at.exception])
    texte = _texte(at)
    assert "Bei n = 80 Variablen hat das Protokoll im Median 201,5 Zeilen für 201,5 Konflikte" in texte                     # Beweisgröße (mit den vorgerechneten Zeilen)
    assert "0 von 857 Kandidaten (25 erfüllbare Formeln)" in texte                                                        # Zufallsformeln der Solidität
    assert "von 7 Zeilen bei h = 3 auf 4.811 bei h = 7" in texte and "höchstens 454 statt 5.015" in texte                    # Schubfach


def test_pruefer_pruefen_eigene_klausel_und_manipulation():
    at = _fresh_app()
    assert "Der Prüfer lehnt die Klausel ab, und sie folgt nicht aus der Formel: richtig." in _texte(at)           # Voreinstellung „-1 -4“ an G
    at.text_input(key="sol_klausel").set_value("1 2").run(timeout=TIMEOUT)
    assert "Der Prüfer akzeptiert die Klausel, und sie folgt aus der Formel: richtig." in _texte(at)
    at.text_input(key="sol_klausel").set_value("9").run(timeout=TIMEOUT)
    assert not at.exception and any("Eingabe nicht lesbar" in w.value for w in at.warning)
    at.radio(key="sol_formel").set_value("zufall").run(timeout=TIMEOUT)
    at.text_input(key="sol_klausel").set_value("1 2").run(timeout=TIMEOUT)
    assert not at.exception
    for art in C.MANIPULATIONEN:
        at.selectbox(key="man_art").set_value(art).run(timeout=TIMEOUT)
        assert not at.exception and "Veränderung:" in _texte(at), art


def test_ausblick_hinweise_alle_quellen_und_varianten():
    at = _fresh_app()
    for quelle in ("suche", "hand"):
        for variante in ("normal", "loeschen", "falsch"):
            at.radio(key="hinweis_quelle").set_value(quelle).run(timeout=TIMEOUT)
            at.radio(key="hinweis_variante").set_value(variante).run(timeout=TIMEOUT)
            assert not at.exception, (quelle, variante)
    assert "Der Hinweisprüfer lehnt das Protokoll in Zeile 3 ab" in _texte(at)
