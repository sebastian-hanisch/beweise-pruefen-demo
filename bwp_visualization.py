"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Farbe trägt nie allein die Information: Urteile stehen im Hover-Text und in der Legende als Wort."""

import plotly.graph_objects as go

import bwp_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_schritte_je_zeile(befund):
    """Prüfschritte je Protokollzeile; Löschzeilen kosten nichts, eine abgelehnte Zeile ist rot und im Hover-Text als „abgelehnt“ benannt."""
    gruppen = {"akzeptiert": ([], [], [], C.COLOR_OK), "abgelehnt": ([], [], [], C.COLOR_FEHLER), "gelöscht": ([], [], [], C.COLOR_GRAU)}
    for z in befund.zeilen:
        name = "gelöscht" if z.art == "d" else ("akzeptiert" if z.ok else "abgelehnt")
        gruppen[name][0].append(z.pos)
        gruppen[name][1].append(z.schritte)
    fig = go.Figure()
    for name, (xs, ys, _, farbe) in gruppen.items():
        if xs:
            fig.add_trace(go.Bar(x=xs, y=ys, name=name, marker_color=farbe, hovertemplate="Zeile %{x}: %{y} Prüfschritte, " + name + "<extra></extra>"))
    fig.update_xaxes(title_text="Zeile des Protokolls")
    fig.update_yaxes(title_text="Prüfschritte")
    fig.update_layout(barmode="stack")
    return _base(fig)


def _band(fig, xs, tiefste, hoechste, mitte, name, farbe, rgba):
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=list(hoechste) + list(tiefste)[::-1], fill="toself", fillcolor=rgba, line=dict(width=0), hoverinfo="skip", name=f"{name}: Minimum bis Maximum"))
    fig.add_trace(go.Scatter(x=xs, y=list(mitte), mode="lines+markers", line=dict(color=farbe, width=3), name=f"{name}: Median", hovertemplate="n = %{x}: %{y:.1f}<extra></extra>"))


def build_groesse(zeilen):
    """Konflikte und Protokollzeilen (Median mit Spanne) gegen n; die beiden Kurven liegen übereinander, weil eine Zeile je Konflikt geschrieben wird."""
    zs = [z for z in zeilen if z["formeln"]]
    xs = [z["n"] for z in zs]
    fig = go.Figure()
    _band(fig, xs, [z["konflikte_min"] for z in zs], [z["konflikte_max"] for z in zs], [z["konflikte"] for z in zs], "Konflikte", C.COLOR_LINE, "rgba(76,120,168,0.18)")
    fig.add_trace(go.Scatter(x=xs, y=[z["zeilen"] for z in zs], mode="markers", marker=dict(color=C.COLOR_OK, size=11, symbol="diamond-open", line=dict(width=2)), name="Protokollzeilen (Median)",
                             hovertemplate="n = %{x}: %{y:.1f} Zeilen<extra></extra>"))
    fig.update_xaxes(title_text="Variablen n", tickmode="array", tickvals=xs)
    fig.update_yaxes(title_text="Konflikte bzw. Zeilen")
    return _base(fig)


def build_schritte(zeilen):
    """Prüfschritte je Löser-Propagation (Median mit Spanne) gegen n."""
    zs = [z for z in zeilen if z["formeln"]]
    xs = [z["n"] for z in zs]
    fig = go.Figure()
    _band(fig, xs, [z["schritte_je_propagation_min"] for z in zs], [z["schritte_je_propagation_max"] for z in zs], [z["schritte_je_propagation"] for z in zs],
          "Prüfschritte je Propagation", C.COLOR_OK, "rgba(47,107,101,0.18)")
    fig.update_xaxes(title_text="Variablen n", tickmode="array", tickvals=xs)
    fig.update_yaxes(title_text="Prüfschritte je Löser-Propagation")
    return _base(fig)


def build_schubfach(zeilen):
    """Protokollzeilen des Schubfachs je h, ohne und mit Löschzeilen, logarithmische Achse (die Zahlen wachsen um Zehnerpotenzen)."""
    zs = [z for z in zeilen if z["ohne"] is not None]
    xs = [f"h = {z['h']}" for z in zs]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[z["ohne"]["zeilen"] for z in zs], name="ohne Löschen", marker_color=C.COLOR_LINE,
                         text=[f"{z['ohne']['zeilen']:,}".replace(",", ".") for z in zs], textposition="outside", hovertemplate="%{x}: %{y} Zeilen ohne Löschen<extra></extra>"))
    mit = [z for z in zs if z["mit"] is not None]
    if mit:
        fig.add_trace(go.Bar(x=[f"h = {z['h']}" for z in mit], y=[z["mit"]["zeilen"] for z in mit], name="mit Löschzeilen", marker_color=C.COLOR_GRAU,
                             text=[f"{z['mit']['zeilen']:,}".replace(",", ".") for z in mit], textposition="outside", hovertemplate="%{x}: %{y} Zeilen mit Löschzeilen<extra></extra>"))
    fig.update_yaxes(title_text="Protokollzeilen (logarithmisch)", type="log")
    fig.update_layout(barmode="group")
    return _base(fig, height=360)
