"""Beweise schreiben und prüfen – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 6 der Linie „SAT und Constraint Programming“: Ein Löser sagt „unerfüllbar“, schreibt jede gelernte Klausel in ein Protokoll, und ein zweites, einfaches Programm
rechnet jede Zeile durch Einheitspropagation nach. Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import bwp_algorithm as A
import bwp_constants as C
import bwp_evaluation as ev
import bwp_presets as P
import bwp_pruefer as PR
import bwp_scenario as S
from bwp_layout import dunkles_design, kopf_css
from bwp_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from bwp_visualization import build_groesse, build_schritte, build_schritte_je_zeile, build_schubfach

st.set_page_config(page_title="Beweise prüfen – Sebastian Hanisch", layout="wide")

QUELLEN = {C.QUELLE_HAND: "Von Hand (Zeilen A bis E)", C.QUELLE_LOESER: "Vom Löser geschrieben"}
SOL_FORMELN = {"g": "Handbeispiel G (6 Variablen, Wahrheit durch Aufzählung aller Belegungen)", "zufall": "Zufallsformel n = 30 (Wahrheit durch den Löser)"}
HINWEIS_QUELLEN = {"suche": "Hinweise aus der Einheitskette erzeugt", "hand": "Hinweise von Hand geordnet (Handbeispiel)"}
HINWEIS_VARIANTEN = {"normal": "Beweis wie oben", "loeschen": "Klausel 4 = (¬x1 ∨ ¬x3) vor Zeile C löschen", "falsch": "Falscher Hinweis in Zeile C (Klausel 1 statt 4)"}


@st.cache_data(show_spinner=False)
def _lauf(familie, n, h, loeschen, quelle, seed):
    settings = ev.Settings(familie, n, h, loeschen, quelle, seed)
    g = ev.formel_von(settings)
    return g, ev.lauf_von(settings, g)


@st.cache_data(show_spinner=False)
def _zeile(klauseln, protokoll, pos):
    return PR.erklaere_zeile(klauseln, protokoll, pos)


@st.cache_data(show_spinner=False)
def _messreihe_zufall():
    return A.messreihe_zufall()


@st.cache_data(show_spinner=False)
def _messreihe_schubfach():
    return A.messreihe_schubfach()


@st.cache_data(show_spinner=False)
def _tafel_g():
    g = S.formel_g()
    return A.soliditaet(g.n, g.klauseln, A.alle_zweierklauseln(g.n)), len(A.modelle(g.n, g.klauseln))


@st.cache_data(show_spinner=False)
def _soliditaet_reihe():
    return A.soliditaet_reihe()


@st.cache_data(show_spinner=False)
def _sat_zufallsformel(seed):
    """Die erste erfüllbare Zufallsformel (n = 30, m = 100) ab dem Zufalls-Seed."""
    for s in range(seed, seed + C.SUCH_VERSUCHE):
        f = S.zufallsformel(C.SOL_N, s, C.SOL_M)
        if A.solve(f.n, [list(c) for c in f.klauseln], conflict_budget=C.BUDGET).antwort is True:
            return f, s
    return None


@st.cache_data(show_spinner=False)
def _hinweise(quelle, variante):
    return A.hinweis_beispiel(quelle, variante)


def _klausel_tabelle(formel):
    return pd.DataFrame([{"Nr": i + 1, "Klausel": S.klausel_text(c)} for i, c in enumerate(formel.klauseln)])


def _zahl(x, stellen=0):
    return "–" if x is None else ev.de(x, stellen)


def _zufall_tabelle(zeilen):
    return pd.DataFrame([{
        "n": z["n"], "Klauseln": z["klauseln"], "Formeln": z["formeln"], "Konflikte (Median)": _zahl(z["konflikte"], 1), "Zeilen (Median)": _zahl(z["zeilen"], 1),
        "Zeilen je Konflikt": f"{_zahl(z['zeilen_je_konflikt_min'], 2)} bis {_zahl(z['zeilen_je_konflikt_max'], 2)}", "gelernte Literale (Median)": _zahl(z["lemma_literale"], 1),
        "Prüfschritte (Median)": _zahl(z["schritte"], 1), "Prüfschritte je Propagation (Median)": _zahl(z["schritte_je_propagation"], 1),
        "Spanne": f"{_zahl(z['schritte_je_propagation_min'], 1)} bis {_zahl(z['schritte_je_propagation_max'], 1)}", "akzeptiert": f"{z['ok']} von {z['formeln']}",
        "Herkunft": "vorgerechnet, nicht live" if z["vorgerechnet"] else "live gerechnet",
    } for z in zeilen])


def _schubfach_tabelle(zeilen):
    daten = []
    for z in zeilen:
        for art, r in (("ohne Löschen", z["ohne"]), ("mit Löschzeilen", z["mit"])):
            herkunft = "vorgerechnet, nicht live" if z["vorgerechnet"] else "live gerechnet"
            if r is None:
                daten.append({"h": z["h"], "Variante": art, "Konflikte": "nicht entschieden", "Zeilen": None, "Löschzeilen": None, "gelernte Literale": None, "Prüfschritte": None,
                              "höchstens lebende Klauseln": None, "akzeptiert": "–", "Herkunft": herkunft})
                continue
            daten.append({"h": z["h"], "Variante": art, "Konflikte": ev.de(r["konflikte"]), "Zeilen": r["zeilen"], "Löschzeilen": r["loeschzeilen"], "gelernte Literale": r["lemma_literale"],
                          "Prüfschritte": r["schritte"], "höchstens lebende Klauseln": r["max_lebend"], "akzeptiert": "ja" if r["ok"] else "nein", "Herkunft": herkunft})
    return pd.DataFrame(daten)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in bwp_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧾 Beweise schreiben und prüfen")
st.markdown(
    """
Ein SAT-Löser, der „**unerfüllbar**“ sagt, hat nichts bewiesen, solange niemand nachrechnet. Schreibt er jede gelernte Klausel in ein **Protokoll** (eine Zeile je Konflikt, zuletzt die **leere Klausel**),
kann ein zweites, viel einfacheres Programm jede Zeile durch **Einheitspropagation** prüfen, ohne dem Löser zu trauen. Die Demo zählt **Protokollzeilen** und **Prüfschritte**, nie Sekunden,
und prüft den Prüfer selbst: **Er hat in den gemessenen Reihen keine Klausel angenommen, die nicht aus der Formel folgt.**

Weiter unten: vier Experimente (**Zeile für Zeile prüfen**, **Beweisgröße**, **Prüfer prüfen**, **Löschzeilen und Schubfach**) und ein Ausblick auf DRAT, LRAT und CP-Beweise, der Abschnitt
**🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Prüfen eines Beweises", expanded=True):
    st.markdown(
        """
1. **Der Löser schreibt mit.** Jeder Konflikt führt zu einer gelernten Klausel; sie kommt als Zeile `a Klausel` ins Protokoll (a wie hinzufügen). Wirft der Löser Klauseln weg, steht eine Zeile `d Klausel`
   (d wie löschen) im Protokoll. Die letzte Zeile ist die **leere Klausel** `()`: Sie hat kein Literal, ist also nie wahr, und ihre Herleitung heißt, dass die Formel keine Lösung hat.
2. **Der Prüfer rechnet jede Zeile nach.** Er nimmt an, dass alle Literale der Zeile **falsch** sind, und wendet nur **Einheitspropagation** auf die Formel und die schon geprüften Zeilen an. Wird dabei eine Klausel
   verletzt, ist die Zeile bewiesen (**RUP**, reverse unit propagation); bleibt alles offen, wird die Zeile abgelehnt. Gilt das für jede Zeile bis zur leeren Klausel, ist der Beweis akzeptiert.
3. **Warum man dem Prüfer glauben darf.** Er ist kurz, zählt statt zu suchen, kennt den Löser nicht (kein Import, Quelltextprüfung in `tests/test_pruefer.py`) und lässt sich gegen eine
   unabhängige Wahrheit prüfen (Reiter „Prüfer prüfen“). Das ist ein Argument aus Kürze und Messung, **kein Korrektheitsbeweis des Prüfers**.

| Begriff | Bedeutung hier |
|---|---|
| **Einheitspropagation** | Ist in einer Klausel kein Literal wahr und genau eines noch frei, muss dieses wahr werden. Das wiederholt der Prüfer, bis nichts mehr erzwungen wird oder eine Klausel nur noch falsche Literale hat. |
| **RUP** | Eine Zeile folgt per Einheitspropagation: Annahme „alle ihre Literale falsch“, danach ein Widerspruch. RUP ist **strenger** als logische Folgerung: Der Prüfer lehnt manche gefolgerte Klausel ab, nimmt aber (in den Messungen) nie eine nicht gefolgerte an. |
| **Löschzeile** | Entfernt eine Klausel aus dem Bestand; spätere Zeilen dürfen sie nicht mehr benutzen. Löschen verkleinert den Bestand und macht jede einzelne Prüfung billiger; die Gesamtzahl der Prüfschritte stieg in den gemessenen Schubfach-Fällen mit Löschzeilen (h = 5 bis 7), weil der Löser mit Löschen mehr Konflikte braucht. |
| **leere Klausel** | `()`: ein Widerspruch ohne Literal. Ihre Herleitung beendet den Beweis. Ein Protokoll ohne sie gilt nicht als Beweis. |
| **Prüfschritt** | Eine angesehene Klausel bei der Propagation des Prüfers (Zähler statt Zeit). |
"""
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Formel**")
    familie = st.selectbox("Aufgabenfamilie", C.FAMILIEN, key="familie_select",
                           help="Welche Formel die Abschnitte „Ergebnis“ und „Zeile für Zeile prüfen“ untersuchen. Die Experimente 2 bis 4 haben feste Formeln.")
    aktiv = lambda key: familie in P.AKTIV_FUER[key]  # noqa: E731
    n = st.slider("Variablen n (Zufalls-3-SAT)", *bounds("n_slider"), key="n_slider", disabled=not aktiv("n_slider"),
                  help="Gilt nur für Zufalls-3-SAT (4,26 Klauseln je Variable); sonst gesperrt. Die App nimmt die erste unerfüllbare Formel ab dem Zufalls-Seed.")
    h = st.slider("Löcher h (Schubfach)", *bounds("h_slider"), key="h_slider", disabled=not aktiv("h_slider"),
                  help="Gilt nur für das Schubfach (h + 1 Tauben, h Löcher); sonst gesperrt. h = 7 steht im Experiment „Löschzeilen und Schubfach“ als vorgerechnete Zeile.")
    seed = st.number_input("Zufalls-Seed der Formel", *bounds("seed_input"), key="seed_input", step=1, disabled=not aktiv("seed_input"),
                           help="Gilt nur für Zufalls-3-SAT: Gesucht wird ab diesem Zufalls-Seed die erste unerfüllbare Formel; Handbeispiel, G und Schubfach sind fest.")
    st.button("🎲 Neue Formel generieren", width="stretch", on_click=randomize_seed, disabled=not aktiv("seed_input"))
    st.markdown("**Protokoll**")
    quelle = st.radio("Beweis des Handbeispiels", list(QUELLEN), format_func=QUELLEN.get, key="quelle_radio", disabled=not aktiv("quelle_radio"),
                      help="Gilt nur für das Handbeispiel PHP(2): Der Prüfer liest den Beweis von Hand (fünf Zeilen A bis E) oder den, den der Löser schreibt (zwei Zeilen).")
    loeschen = st.radio("Löschzeilen", [C.LOESCHEN_AUS, C.LOESCHEN_AN], format_func=lambda x: {"aus": "aus (der Löser behält alle Klauseln)", "an": f"an (alle {C.LOESCH_TAKT} Konflikte)"}[x],
                        key="loeschen_radio", disabled=not aktiv("loeschen_radio"),
                        help="Gilt nur für das Schubfach: Der Löser löscht erst alle 100 Konflikte, und die Zufallsformeln der Messreihe (n bis 50) brauchen höchstens 112. Mit Löschzeilen wirft der Löser gelernte Klauseln weg und schreibt das ins Protokoll; die Suche verläuft dann anders.")

sync_query_params({"familie_select": familie, "n_slider": int(n), "h_slider": int(h), "loeschen_radio": loeschen, "quelle_radio": quelle, "seed_input": int(seed)})

settings = ev.Settings(familie, int(n), int(h), loeschen, quelle, int(seed))
with st.spinner("Rechne die Suche und prüfe das Protokoll …"):
    gewaehlt, lauf = _lauf(settings.familie, settings.n, settings.h, settings.loeschen, settings.quelle, settings.seed)
formel = gewaehlt.formel

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
zusatz = f" Gefunden bei Zufalls-Seed {gewaehlt.seed_benutzt}." if gewaehlt.seed_benutzt is not None else ""
if not gewaehlt.gefunden:
    zusatz = f" Unter den nächsten {C.SUCH_VERSUCHE} Zufalls-Seeds ließ sich keine unerfüllbare Formel dieser Größe entscheiden; gezeigt wird die Formel zum gewählten Zufalls-Seed."
st.caption(f"Formel: {formel.name}; {formel.n} Variablen, {len(formel.klauseln)} Klauseln.{zusatz}")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Antwort des Lösers", ev.antwort_text(lauf.antwort))
if lauf.befund is not None:
    m2.metric("Urteil des Prüfers", "akzeptiert" if lauf.befund.ok else "abgelehnt")
    m3.metric("Protokollzeilen", ev.de(len(lauf.protokoll)), delta=f"{ev.de(lauf.stat['konflikte'])} Konflikte des Lösers", delta_color="off")
    m4.metric("Prüfschritte", ev.de(lauf.befund.schritte), delta="geprüfte Klauseln, keine Sekunden", delta_color="off")
else:
    m2.metric("Urteil des Prüfers", "Modell geprüft" if lauf.modell_ok else ("Modell abgelehnt" if lauf.antwort is True else "kein Protokoll"))
    m3.metric("Protokollzeilen", "–", delta="keines nötig" if lauf.antwort is True else "nicht entschieden", delta_color="off")
    m4.metric("Prüfschritte", "–", delta=f"{ev.de(lauf.stat['konflikte'])} Konflikte des Lösers", delta_color="off")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Warum soll man „unerfüllbar“ glauben?")
kind, text = ev.verdict_kernfrage(lauf)
getattr(st, kind)(text)

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 · Zeile für Zeile prüfen", "2 · Beweisgröße", "3 · Prüfer prüfen", "4 · Löschzeilen und Schubfach", "Ausblick: DRAT, LRAT, CP-Beweise"])

# --- Experiment 1: Zeile für Zeile prüfen -----------------------------------------------------------------------------------------------------

with tab1:
    st.subheader("🔬 Experiment: Den Beweis Zeile für Zeile prüfen")
    st.caption("Der Prüfer nimmt je Zeile an, dass alle Literale falsch sind, und propagiert Einheiten. Die Kette zeigt, welche Klausel welches Literal erzwingt und welche Klausel zuletzt verletzt wird. "
               "Klauselnummern: die Formelklauseln haben die Nummern 1 bis m, jede angenommene Zeile des Protokolls die nächste.")
    if lauf.befund is None:
        st.info("Zu dieser Formel gibt es kein Protokoll: Sie ist erfüllbar oder wurde nicht entschieden. Wählen Sie das Handbeispiel PHP(2), eine Zufallsformel oder das Schubfach. "
                "Die erfüllbare Formel G gehört in den Reiter „Prüfer prüfen“.")
    else:
        with st.expander(f"Klauseln der Formel ({len(formel.klauseln)})"):
            st.dataframe(_klausel_tabelle(formel), hide_index=True, width="stretch")
        laenge = len(lauf.protokoll)
        if st.session_state.get("zeile_nr", 1) > laenge:
            st.session_state["zeile_nr"] = laenge
        pos = int(st.number_input("Zeile des Protokolls", min_value=1, max_value=laenge, value=1, step=1, key="zeile_nr",
                                  help=f"Das Protokoll hat {laenge} Zeilen; die letzte ist die leere Klausel."))
        info = _zeile(formel.klauseln, lauf.protokoll, pos)
        art_text = "hinzufügen" if info["art"] == "a" else "löschen"
        st.markdown(f"**Zeile {pos} von {laenge}** ({art_text}): `{S.klausel_text(info['klausel'])}`")
        kind, text = ev.verdict_zeile(info)
        getattr(st, kind)(text)
        e = info["erklaerung"]
        if e is not None and not e.tautologie:
            kette = [{"Schritt": i + 1, "erzwingende Klausel": f"{nr}: {S.klausel_text(info['db'][nr])}", "erzwungenes Literal": S.lit_text(lit)} for i, (nr, lit) in enumerate(e.kette)]
            if e.widerspruch is not None:
                kette.append({"Schritt": len(e.kette) + 1, "erzwingende Klausel": f"{e.widerspruch}: {S.klausel_text(info['db'][e.widerspruch])}", "erzwungenes Literal": "Widerspruch: alle Literale falsch"})
            st.markdown("Angenommen wahr: " + (", ".join(S.lit_text(l) for l in e.annahmen) or "nichts") + ".")
            if kette:
                st.dataframe(pd.DataFrame(kette), hide_index=True, width="stretch")
        st.plotly_chart(build_schritte_je_zeile(lauf.befund), width="stretch", key="schritte_chart")
        st.caption("Prüfschritte je Zeile des Protokolls; Löschzeilen kosten keine Prüfschritte.")
        with st.expander("Alle Zeilen als Tabelle"):
            st.dataframe(pd.DataFrame(ev.protokoll_tabelle(lauf.befund)), hide_index=True, width="stretch")

# --- Experiment 2: Beweisgröße ---------------------------------------------------------------------------------------------------------------

with tab2:
    st.subheader("🔬 Experiment: Wie groß wird der Beweis?")
    st.caption(f"Je n die ersten {C.FORMELN_JE_N} unerfüllbaren Zufalls-3-SAT-Formeln ab Zufalls-Seed {C.MESS_SEED_START} (4,26 Klauseln je Variable, SplitMix64), ohne Löschzeilen. "
               "Gemessen werden Protokollzeilen, gelernte Literale und Prüfschritte; die Zeilen für n = 60 bis 80 sind vorgerechnet (`bwp_messreihen.json`).")
    if st.button("▶️ Messreihe rechnen", key="groesse_knopf"):
        with st.spinner("Rechne die Messreihe (n = 30, 40, 50 mit je 20 unerfüllbaren Formeln; wenige Sekunden) …"):
            st.session_state["groesse"] = _messreihe_zufall()
    live = st.session_state.get("groesse")
    if live:
        zeilen = ev.zufall_mit_vorgerechnet(live)
        st.dataframe(_zufall_tabelle(zeilen), hide_index=True, width="stretch")
        sp1, sp2 = st.columns(2)
        sp1.plotly_chart(build_groesse(zeilen), width="stretch", key="groesse_chart")
        sp2.plotly_chart(build_schritte(zeilen), width="stretch", key="schritte_prop_chart")
        kind, text = ev.verdict_groesse(zeilen)
        getattr(st, kind)(text)
        st.caption("Eine Zeile je Konflikt ist keine Annahme, sondern die Arbeitsweise des Lösers: Er schreibt jede gelernte Klausel auf, auch Einheitsklauseln.")
    else:
        st.info("Noch nicht gerechnet: „Messreihe rechnen“ startet die Reihe für n = 30, 40 und 50.")

# --- Experiment 3: Prüfer prüfen ---------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("🔬 Experiment: Den Prüfer prüfen")
    st.markdown(
        "**Warum an einer erfüllbaren Formel?** An einer unerfüllbaren Formel folgt jede Klausel, ein Manipulationstest wäre leer: Selbst eine falsch geschriebene Zeile „stimmt“ dort semantisch. "
        "Ob der Prüfer Falsches annimmt, zeigt sich erst an einer **erfüllbaren** Formel, deren Wahrheit unabhängig vom Prüfer bekannt ist: Eine Klausel folgt genau dann, wenn „Formel plus verneinte Klausel“ "
        "unerfüllbar ist, also durch Aufzählung aller Belegungen (bis 14 Variablen) oder durch den Löser."
    )
    st.markdown("#### a) Eine eigene Klausel an einer erfüllbaren Formel")
    sol_art = st.radio("Erfüllbare Formel", list(SOL_FORMELN), format_func=SOL_FORMELN.get, key="sol_formel", horizontal=True)
    if sol_art == "g":
        sol_formel = S.formel_g()
    else:
        treffer = _sat_zufallsformel(int(seed))
        sol_formel = treffer[0] if treffer else S.formel_g()
    st.caption(f"Formel: {sol_formel.name}; {sol_formel.n} Variablen, {len(sol_formel.klauseln)} Klauseln."
               + (" Die erste erfüllbare Zufallsformel ab dem Zufalls-Seed der Seitenleiste." if sol_art == "zufall" else ""))
    with st.expander(f"Klauseln der Formel ({len(sol_formel.klauseln)})"):
        st.dataframe(_klausel_tabelle(sol_formel), hide_index=True, width="stretch")
    text_in = st.text_input("Klausel (Literale als Zahlen: 1 heißt x1, -4 heißt ¬x4)", value="-1 -4", key="sol_klausel",
                            help="Zum Beispiel „-1 -4“ für (¬x1 ∨ ¬x4): Diese Klausel gehört zum Beweis von PHP(2), folgt aber aus G nicht.")
    klausel, fehler = S.parse_klausel(text_in, sol_formel.n)
    if fehler:
        st.warning(f"Eingabe nicht lesbar: {fehler}.")
    else:
        akz = bool(A.ist_rup([list(c) for c in sol_formel.klauseln], list(klausel)))
        fo = A.wahrheit(sol_formel.n, sol_formel.klauseln, klausel)
        weg = "Aufzählung aller Belegungen" if sol_formel.n <= C.AUFZAEHLUNG_MAX_N else "Löser auf „Formel plus verneinte Klausel“"
        c1, c2 = st.columns(2)
        c1.metric("Urteil des Prüfers", "akzeptiert" if akz else "abgelehnt")
        c2.metric("Wahrheit (unabhängig)", "folgt" if fo else "folgt nicht", delta=weg, delta_color="off")
        kind, text = ev.verdict_klausel(akz, fo)
        getattr(st, kind)(text)
        if not fo:
            modell = A.gegenbeispiel(sol_formel.n, sol_formel.klauseln, klausel)
            if modell:
                wahr = ", ".join(f"x{v}" for v, w in sorted(modell.items()) if w)
                st.caption(f"Ein Modell der Formel, das die Klausel verletzt (wahr sind: {wahr or 'keine Variable'}): Es belegt, dass die Klausel nicht folgt.")
    st.markdown("#### b) Die Vierfeldertafel")
    tafel_g, modelle_g = _tafel_g()
    st.markdown(f"**Handbeispiel G:** alle {tafel_g.summe} Klauseln aus zwei Literalen über verschiedenen Variablen; G hat {modelle_g} Modelle von 64 (Aufzählung).")
    st.dataframe(pd.DataFrame(ev.tafel_zeilen(tafel_g.zellen())), hide_index=True, width="stretch")
    kind, text = ev.verdict_soliditaet(tafel_g.zellen())
    getattr(st, kind)(text)
    st.markdown(f"**Zufallsformeln:** n = {C.SOL_N}, m = {C.SOL_M}, {C.SOL_FORMELN} feste Formeln (Zufalls-Seeds {C.SOL_SEED_START} bis {C.SOL_SEED_START + C.SOL_FORMELN - 1}), nur die erfüllbaren zählen; "
                f"je Formel bis zu {C.SOL_KANDIDATEN} Kandidatenklauseln (zufällige 2- und 3-Klauseln oder Resolventen zweier Formelklauseln), Wahrheit durch den Löser.")
    if st.button("▶️ Zufallsformeln prüfen", key="sol_knopf"):
        with st.spinner("Prüfe die Kandidatenklauseln und bestimme ihre Wahrheit mit dem Löser (wenige Sekunden) …"):
            st.session_state["sol_reihe"] = _soliditaet_reihe()
    reihe = st.session_state.get("sol_reihe")
    if reihe:
        art = reihe["nach_art"]
        zeilen = [{"Kandidaten": "zufällige 2- und 3-Klauseln", "akzeptiert, folgt": art["zufällig"][0], "akzeptiert, folgt nicht": art["zufällig"][1], "abgelehnt, folgt": art["zufällig"][2], "abgelehnt, folgt nicht": art["zufällig"][3]},
                  {"Kandidaten": "Resolventen zweier Formelklauseln", "akzeptiert, folgt": art["Resolvente"][0], "akzeptiert, folgt nicht": art["Resolvente"][1], "abgelehnt, folgt": art["Resolvente"][2], "abgelehnt, folgt nicht": art["Resolvente"][3]},
                  {"Kandidaten": "zusammen", "akzeptiert, folgt": reihe["gesamt"][0], "akzeptiert, folgt nicht": reihe["gesamt"][1], "abgelehnt, folgt": reihe["gesamt"][2], "abgelehnt, folgt nicht": reihe["gesamt"][3]}]
        st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")
        kind, text = ev.verdict_soliditaet(reihe["gesamt"], f" ({reihe['erfuellbar']} erfüllbare Formeln)")
        getattr(st, kind)(text)
    else:
        st.info("Noch nicht gerechnet: „Zufallsformeln prüfen“ startet die Reihe.")
    st.markdown("#### c) Ein Protokoll manipulieren")
    if lauf.befund is None or not lauf.befund.ok:
        st.info("Dafür braucht es ein akzeptiertes Protokoll: Wählen Sie in der Seitenleiste das Handbeispiel PHP(2), eine Zufallsformel oder das Schubfach.")
    else:
        c1, c2 = st.columns(2)
        man_art = c1.selectbox("Veränderung", list(C.MANIPULATIONEN), format_func=C.MANIPULATION_NAMEN.get, key="man_art")
        man_seed = int(c2.number_input("Zufalls-Seed der Veränderung", min_value=0, max_value=C.SEED_MAX, value=1, step=1, key="man_seed", help="Wählt, welche Zeile verändert wird."))
        neu, beschreibung, _ = A.manipuliere(lauf.protokoll, man_art, man_seed)
        urteil = PR.pruefe_protokoll(formel.klauseln, neu)
        kind, text = ev.verdict_manipulation(urteil, beschreibung)
        getattr(st, kind)(text)
        st.caption("Die Wahrheit der geänderten Zeile ist hier ohne Aussage (die Formel ist unerfüllbar, jede Klausel folgt); das Urteil „abgelehnt“ heißt nur, dass Einheitspropagation sie nicht herleitet.")

# --- Experiment 4: Löschzeilen und Schubfach --------------------------------------------------------------------------------------------------

with tab4:
    st.subheader("🔬 Experiment: Protokoll mit Löschzeilen und das Schubfach")
    st.caption(f"Schubfach h + 1 Tauben, h Löcher, ohne und mit Löschzeilen (der Löser wirft alle {C.LOESCH_TAKT} Konflikte die schlechtere Hälfte der gelernten Klauseln weg und schreibt das als Zeile ins Protokoll). "
               f"h = {C.SCHUBFACH_VORGERECHNET} ist vorgerechnet (`bwp_messreihen.json`, Konfliktbudget {ev.de(C.BUDGET_VORGERECHNET)}), nicht live.")
    if st.button("▶️ Messreihe rechnen", key="schub_knopf"):
        with st.spinner("Rechne das Schubfach für h = 3 bis 6 mit beiden Varianten und prüfe die Protokolle (einige Sekunden) …"):
            st.session_state["schubfach"] = _messreihe_schubfach()
    live = st.session_state.get("schubfach")
    if live:
        zeilen = ev.schubfach_mit_vorgerechnet(live)
        st.dataframe(_schubfach_tabelle(zeilen), hide_index=True, width="stretch")
        st.plotly_chart(build_schubfach(zeilen), width="stretch", key="schub_chart")
        kind, text = ev.verdict_schubfach(zeilen)
        getattr(st, kind)(text)
        st.caption("Das Wachstum ist eine eigene Messung an dieser einen Formelfamilie. Die theoretische Untergrenze für Resolutionsbeweise des Schubfachs stammt von Haken (1985, Theoretical Computer Science 39; "
                   "hier nur zitiert, die Primärquelle ist nicht gelesen). In „Symmetrie brechen“ (Stück 9 der Linie) verkürzt eine Symmetriebrechung dieselbe Formel stark; DRAT und LRAT stehen im Ausblick.")
    else:
        st.info("Noch nicht gerechnet: „Messreihe rechnen“ startet die Reihe für h = 3 bis 6.")

# --- Ausblick ----------------------------------------------------------------------------------------------------------------------------------

with tab5:
    st.subheader("🔭 Ausblick: DRAT, LRAT und CP-Beweise")
    st.markdown(
        """
Dieser Reiter erklärt nur; er enthält **keine Messwerte der Demo**. Die Aussagen sind Zitate aus den gelesenen Quellen (Leseprotokoll der Linie), keine eigene Messung.

- **DRAT** ist das in der Praxis übliche Beweisformat (im Schur-Papier von Heule, AAAI 2018, erklärt; das Originalpapier zu DRAT-trim ist nicht gelesen). Es erlaubt zusätzlich zu RUP „RAT“-Klauseln.
  Die UNSAT-Wertung des SAT-Wettbewerbs 2025 verlangt Beweise (Folien „Certified results of unsatisfiability using proof logging“); als Prüfer werden dort cake_lpr, GRAT und VeriPB/CakePB genannt (die Wettbewerbsseiten nennen außerdem dpr-trim).
- **LRAT** ergänzt Hinweise, die die Prüfung einfach und schnell machen. Ein zertifizierter Prüfer (ACL2) ist laut Cruz-Filipe, Heule, Hunt, Kaufmann und Schneider-Kamp (CADE 2017) „fast so schnell“ wie
  der nicht zertifizierte; als Beispiel steht dort ein Beweis mit 68 667 Klauseln, der in unter 9 Sekunden geprüft wird.
- **Größenordnung:** Der Beweis zu Schur Five (S(5) = 160, Heule, AAAI 2018) ist rund zwei Petabyte groß (laut Papier) und wurde mit einem formal verifizierten Prüfer zertifiziert. Die Demo bildet das nicht nach.
- **CP-Beweise:** Flippo u. a. (CP 2024, nur Abstract gelesen): Bisher habe kein praktisch einsetzbarer CP-Löser Beweise ohne starken Leistungsverlust erzeugt; ihr dreistufiges Verfahren habe einen Mehraufwand beim
  Protokollieren „oft unter 10 %“. Pumpkin (README 0.5.0) liefert Bescheinigungen für Unerfüllbarkeit und Optimalität mit einem formal verifizierten Prüfer im Format DRCP (nicht VeriPB).
- **Was die Demo davon nicht hat:** Das Format hier ist ein **RUP-Protokoll mit Löschzeilen**, kein DRAT und kein LRAT; über die genannten Prüfer sagt die Demo nichts, was über diese Zitate hinausgeht.
"""
    )
    st.markdown("#### Hinweise statt Suche (LRAT-Idee am Handbeispiel)")
    st.caption("In LRAT trägt jede Zeile **Hinweise**: die Nummern der Klauseln, die nacheinander ein Literal erzwingen und zuletzt den Widerspruch liefern. Der Prüfer liest sie der Reihe nach und sucht nicht. "
               "Die Syntax hier ist frei gewählt und **kein LRAT-Format**; Klauselnummern: Formel 1 bis 9, die Zeilen A bis E sind 10 bis 14.")
    c1, c2 = st.columns(2)
    h_quelle = c1.radio("Hinweise", list(HINWEIS_QUELLEN), format_func=HINWEIS_QUELLEN.get, key="hinweis_quelle")
    h_variante = c2.radio("Variante", list(HINWEIS_VARIANTEN), format_func=HINWEIS_VARIANTEN.get, key="hinweis_variante")
    bsp = _hinweise(h_quelle, h_variante)
    daten = []
    for z in bsp["je_zeile"]:
        if z["art"] == "d":
            daten.append({"Zeile": z["pos"], "Inhalt": f"Löschzeile: Klausel {z['nummer']}", "Hinweise": "–", "Hinweisprüfer": "gelöscht", "gelesen": 0, "Suche (RUP)": "gelöscht", "Prüfschritte": 0})
            continue
        name = (C.HB_NAMEN[(z["pos"] - 1) - (1 if h_variante == "loeschen" and z["pos"] > 3 else 0)]) if z["klausel"] is not None else ""
        daten.append({"Zeile": z["pos"], "Inhalt": f"{name}: {S.klausel_text(z['klausel'])}", "Hinweise": ", ".join(str(x) for x in z["hinweise"]) if z["hinweise"] is not None else "–",
                      "Hinweisprüfer": "akzeptiert" if z["hinweise_ok"] else f"abgelehnt: {z['grund']}", "gelesen": z["gelesen"],
                      "Suche (RUP)": "akzeptiert" if z["suche_ok"] else "abgelehnt", "Prüfschritte": z["schritte"]})
    st.dataframe(pd.DataFrame(daten), hide_index=True, width="stretch")
    kind, text = ev.verdict_hinweise(bsp["je_zeile"])
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Das Format ist ein RUP-Protokoll mit Löschzeilen.** | Es ist kein DRAT und kein LRAT. Verfahren, die neue Variablen einführen oder RAT-Schritte brauchen (Symmetriebrechung mit Hilfsvariablen, Variablenelimination, Variablenaddition), lassen sich damit nicht belegen. |
| **Der Prüfer ist einfach, nicht verifiziert.** | Das Vertrauen beruht auf seiner Kürze, auf der Trennung vom Löser im Quelltext und auf der Solidität an den gemessenen Formeln; ein Korrektheitsbeweis des Prüfers ist es nicht. |
| **Die Solidität ist an einer Familie gemessen.** | Gemessen sind Zufalls-3-SAT mit n = 30 (zwei Kandidatenarten) und das Handbeispiel G (alle Zweierklauseln); für andere Familien und Kandidaten sagt die Messung nichts. |
| **Prüfschritte sind ein Maß für die Arbeit, keine Zeit.** | Die Demo zählt geprüfte Klauseln; was ein Prüfschritt kostet, hängt von Sprache und Datenstruktur ab. Der Prüfer zählt statt zu beobachten und ist deshalb mit Absicht langsam. |
| **Die Beweisgröße ist bis n = 80 (Zufall) und h = 7 (Schubfach) gemessen.** | Für größere Formeln ist der einfache Prüfer in dieser Demo zu langsam; Beweise im Petabyte-Bereich (Schur Five) liegen weit außerhalb. |
| **Ein akzeptierter Beweis gilt nur für die vorliegende Formel.** | Wurde sie vorher erweitert (Symmetriebrechung) oder vereinfacht (Vorverarbeitung), beweist das Protokoll „unerfüllbar“ für diese Formel, nicht für die ursprüngliche. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Formel $F$ in konjunktiver Normalform, eine Menge von Klauseln; jede Klausel ist eine Menge von Literalen. Gesucht ist kein Modell, sondern ein **Beweis der Unerfüllbarkeit**,
den ein einfaches Programm Zeile für Zeile nachrechnen kann.

| Symbol | Bedeutung |
|---|---|
| $F$ | Formel, Menge von Klauseln |
| $C$, $\ell$ | Klausel (Menge von Literalen) bzw. ein Literal ($x$ oder $\neg x$) |
| $\neg C$ | die Einheitsklauseln $\neg \ell$ für jedes Literal $\ell \in C$: „alle Literale von $C$ sind falsch“ |
| $\bot$ | die leere Klausel, nie wahr |
| $\mathrm{UP}(F)$ | Ergebnis der Einheitspropagation auf $F$: erzwungene Literale, oder ein Widerspruch |
| $F \vdash_1 C$ | $C$ ist durch Einheitspropagation herleitbar (RUP) |
| $F \models C$ | $C$ folgt logisch aus $F$ |

**Einheitspropagation.** Ist in einer Klausel $D \in F$ jedes Literal bis auf $\ell$ falsch und $\ell$ noch frei, wird $\ell$ wahr gesetzt. Das wiederholt sich, bis nichts mehr erzwungen wird oder eine Klausel nur noch falsche Literale hat (Widerspruch).

**RUP.** Eine Klausel $C$ ist aus $F$ durch Einheitspropagation herleitbar, wenn die Propagation auf $F$ zusammen mit $\neg C$ zu einem Widerspruch führt:

$$F \vdash_1 C \quad :\Longleftrightarrow \quad \mathrm{UP}(F \wedge \neg C) \ \text{endet in einem Widerspruch}.$$

**Solidität und ihre Grenze.** Was der Prüfer akzeptiert, folgt aus der Formel; die Umkehrung gilt nicht, weil die Propagation weniger kann als logisches Schließen:

$$F \vdash_1 C \ \Longrightarrow \ F \models C, \qquad F \models C \ \not\Longrightarrow \ F \vdash_1 C.$$

Die Demo misst beide Richtungen (Reiter „Prüfer prüfen“): akzeptiert und nicht gefolgert kommt in den gemessenen Reihen nicht vor, gefolgert und abgelehnt kommt vor.

**Protokoll.** Ein Protokoll ist eine Folge von Zeilen $(a, C_i)$ (hinzufügen) und $(d, D_j)$ (löschen). Mit $F_0 = F$ gilt für jede Zeile $(a, C_i)$, dass $F_{i-1} \vdash_1 C_i$, und der Bestand wird fortgeschrieben:

$$F_i = F_{i-1} \cup \{C_i\} \quad \text{bei } (a, C_i), \qquad F_i = F_{i-1} \setminus \{D_i\} \quad \text{bei } (d, D_i).$$

Der Beweis ist **akzeptiert**, wenn alle Zeilen bis zur Zeile mit $C_k = \bot$ so geprüft sind. Wegen der Solidität folgt dann $F \models \bot$, die Formel ist unerfüllbar (genauer: für die vorliegende Formel $F$).

**Prüfschritte.** Der Prüfer geht bei jeder Propagation in Durchläufen über alle lebenden Klauseln; jede angesehene Klausel zählt einen Prüfschritt. Er benutzt keine beobachteten Literale, deshalb ist die Zahl je Propagation des Lösers
größer als eins (Messwerte: Experiment „Beweisgröße“).

**Quellen.** RUP und die Aussage „RUP ist strenger als Folgerung“ sind Standardwissen und hier eigene Messung (kein Zitat). LRAT: Cruz-Filipe, Heule, Hunt, Kaufmann, Schneider-Kamp, *Efficient Certified RAT Verification*,
CADE-26 (2017). Schur Five: Heule, AAAI 2018 (arXiv 2017). CP-Beweise: Flippo u. a., CP 2024 (Abstract). Alle Zahlen der Experimente sind eigene Messungen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
