"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Formeln der Presets."""

import bwp_constants as C
import bwp_evaluation as ev
import bwp_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert preset["familie"] in C.FAMILIEN and preset["loeschen"] in (C.LOESCHEN_AUS, C.LOESCHEN_AN) and preset["quelle"] in (C.QUELLE_HAND, C.QUELLE_LOESER)
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.H_MIN <= preset["h"] <= C.H_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Handbeispiel PHP(2)"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_jeder_regler_ist_fuer_mindestens_eine_familie_aktiv_und_nur_fuer_bekannte_familien():
    assert set(P.AKTIV_FUER) <= set(P.SETTING_SPECS)
    for familien in P.AKTIV_FUER.values():
        assert familien and set(familien) <= set(C.FAMILIEN)


def test_presets_beschreiben_die_gemeinten_formeln():
    php2 = ev.formel_von(ev.Settings(**C.PRESETS["Handbeispiel PHP(2)"])).formel
    assert (php2.n, len(php2.klauseln)) == (6, 9)
    zufall = ev.formel_von(ev.Settings(**C.PRESETS["Kleine Zufallsformel (n = 20)"]))
    assert zufall.gefunden and (zufall.formel.n, len(zufall.formel.klauseln)) == (20, 85) and zufall.seed_benutzt >= C.DEFAULT_SEED
    g = ev.formel_von(ev.Settings(**C.PRESETS["Erfüllbare Formel G"])).formel
    assert (g.n, len(g.klauseln)) == (6, 7)
    schub = ev.formel_von(ev.Settings(**C.PRESETS["Schubfach h = 5"])).formel
    assert (schub.n, len(schub.klauseln)) == (30, 6 + 5 * 15)          # 6 Tauben-Klauseln und je Loch C(6,2) = 15 Paare


def test_preset_hilfetexte_nennen_die_richtigen_zahlen():
    """Die Zahlen der Hilfetexte stimmen mit den Formeln überein (Klauselzahl, Variablenzahl, Zufalls-Seed)."""
    assert "6 Variablen, 9 Klauseln" in C.PRESET_HELP["Handbeispiel PHP(2)"]
    assert "20 Variablen und 85 Klauseln" in C.PRESET_HELP["Kleine Zufallsformel (n = 20)"] and f"Zufalls-Seed {C.DEFAULT_SEED}" in C.PRESET_HELP["Kleine Zufallsformel (n = 20)"]
    assert "7 Modelle von 64" in C.PRESET_HELP["Erfüllbare Formel G"]
    assert "6 Tauben, 5 Löcher" in C.PRESET_HELP["Schubfach h = 5"]


def test_messreihen_nutzen_feste_formeln():
    assert C.MESS_N == (30, 40, 50) and C.FORMELN_JE_N == 20 and C.MESS_SEED_START == 7000
    assert C.SCHUBFACH_H == (3, 4, 5, 6) and C.SCHUBFACH_VORGERECHNET == 7
    assert C.SOL_SEED_START == 1200 and C.SOL_FORMELN == 25
