"""Plotly-Figuren: Graph mit Zustand eines Aufrufs, Dichte-Sweep, Moon–Moser, Degeneracy-Vergleich, Cliquengrößen. Alle Achsen fest (fixedrange)."""

import plotly.graph_objects as go

import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S

_FONT = dict(size=13)


def _fix(fig, height=480, **layout):
    layout.setdefault("margin", dict(l=40, r=20, t=30, b=40))
    fig.update_layout(height=height, font=_FONT, **layout)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _edge_trace(pos, edges, color, width):
    xs, ys = [], []
    for u, v in edges:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), hoverinfo="skip", showlegend=False)


def shown_edges(graph, view):
    """Kanten der Anzeige: Verträglichkeitsgraph oder Konfliktgraph (Komplement)."""
    if view == "conflict":
        comp = S.complement(graph.adj)
        return [(u, v) for u in range(graph.n) for v in sorted(comp[u]) if u < v]
    return graph.edges()


def build_graph_figure(graph, view="compat", frame=None, final_clique=None):
    """Der Graph auf dem Kreis. Mit `frame` (ein Aufruf): R grün, P blau, X grau, Pivot gold, bei gemeldeter Clique rot. Ohne Frame: optional `final_clique` hervorgehoben."""
    pos = graph.positions
    edges = shown_edges(graph, view)
    fig = go.Figure()
    fig.add_trace(_edge_trace(pos, edges, C.COLOR_EDGE, 1))
    colors = [C.COLOR_IDLE] * graph.n
    sizes = [20] * graph.n
    outline = [dict(color="white", width=1)] * graph.n
    r_nodes = set()
    if frame is not None:
        r_nodes = set(frame.R)
        for v in frame.X:
            colors[v] = C.COLOR_X
        for v in frame.P:
            colors[v] = C.COLOR_P
        for v in frame.R:
            colors[v] = C.COLOR_FOUND if frame.found else C.COLOR_R
            sizes[v] = 26
        if frame.pivot is not None:
            outline[frame.pivot] = dict(color=C.COLOR_PIVOT, width=5)
    elif final_clique:
        r_nodes = set(final_clique)
        for v in final_clique:
            colors[v] = C.COLOR_FOUND
            sizes[v] = 26
    if r_nodes and view == "compat":
        inside = [(u, v) for u, v in edges if u in r_nodes and v in r_nodes]
        fig.add_trace(_edge_trace(pos, inside, C.COLOR_FOUND if (frame is None or frame.found) else C.COLOR_R, 4))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pos], y=[p[1] for p in pos], mode="markers+text", text=[str(i + 1) for i in range(graph.n)],
        textposition="middle center", textfont=dict(color=["#333333" if c == C.COLOR_IDLE else "white" for c in colors], size=10),
        marker=dict(color=colors, size=sizes, line=dict(color=[o["color"] for o in outline], width=[o["width"] for o in outline])),
        hovertext=list(graph.labels), hoverinfo="text", showlegend=False))
    for name, color in (("R: gewählt", C.COLOR_R), ("P: noch möglich", C.COLOR_P), ("X: abgearbeitet", C.COLOR_X), ("Fuhre gefunden", C.COLOR_FOUND)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color=color, size=12), name=name))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(color="white", size=12, line=dict(color=C.COLOR_PIVOT, width=4)), name="Pivot"))
    # Ecken-Marker erzwingen den Rand und mit scaleanchor den gleichen Maßstab (DEMO-PLAYBOOK §3: scaleanchor nur mit autorange)
    fig.add_trace(go.Scatter(x=[-1.25, 1.25], y=[-1.25, 1.25], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return _fix(fig, 520, legend=dict(orientation="h", y=-0.02, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=10, b=40))


def build_sweep_figure(rows):
    """Aufrufe über der Dichte, logarithmisch, drei Linien; ein offenes Quadrat markiert Mediane, bei denen mindestens ein Lauf das Budget erreicht hat (dann nur Untergrenze)."""
    fig = go.Figure()
    xs = [r["density"] for r in rows]
    for v, name in C.VARIANTS.items():
        ys = [max(r["calls"][v], 1) for r in rows]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=name, line=dict(color=C.COLOR_LINE[v], width=3), marker=dict(size=8),
                                 hovertemplate="Dichte %{x} %%: %{y:,.0f} Aufrufe<extra>" + name + "</extra>"))
        cut = [(r["density"], max(r["calls"][v], 1)) for r in rows if r["aborted"][v]]
        if cut:
            fig.add_trace(go.Scatter(x=[c[0] for c in cut], y=[c[1] for c in cut], mode="markers", showlegend=False,
                                     marker=dict(symbol="square-open", size=14, color=C.COLOR_LINE[v], line=dict(width=2)),
                                     hovertemplate="mindestens ein Lauf abgebrochen: Untergrenze<extra></extra>"))
    fig.update_xaxes(title="Anteil verträglicher Paare (%)", dtick=10)
    fig.update_yaxes(title="Aufrufe (Median, logarithmisch)", type="log")
    return _fix(fig, 420, legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"))


def build_moon_moser_figure(rows):
    """Maximale Cliquen (= 3^k) und Aufrufe über k: gemessene Punkte, die geschlossenen Formeln als Linien."""
    fig = go.Figure()
    ks = [r["k"] for r in rows]
    fig.add_trace(go.Scatter(x=ks, y=[r["cliques"] for r in rows], mode="lines+markers", name="maximale Cliquen (3^k)", line=dict(color="#888888", dash="dot")))
    fig.add_trace(go.Scatter(x=ks, y=[r["formula_naive"] for r in rows], mode="lines", name="Formel ohne Pivot: 4^k", line=dict(color=C.COLOR_LINE["naive"], width=1)))
    fig.add_trace(go.Scatter(x=ks, y=[r["calls"]["naive"] for r in rows], mode="markers", name="gemessen ohne Pivot", marker=dict(color=C.COLOR_LINE["naive"], size=10)))
    fig.add_trace(go.Scatter(x=ks, y=[r["formula_pivot"] for r in rows], mode="lines", name="Formel mit Pivot: (3^(k+1) − 1)/2", line=dict(color=C.COLOR_LINE["pivot"], width=1)))
    fig.add_trace(go.Scatter(x=ks, y=[r["calls"]["pivot"] for r in rows], mode="markers", name="gemessen mit Pivot", marker=dict(color=C.COLOR_LINE["pivot"], size=10)))
    fig.update_xaxes(title="k (n = 3k Knoten)", dtick=1)
    fig.update_yaxes(title="Anzahl (logarithmisch)", type="log")
    return _fix(fig, 400, legend=dict(orientation="h", y=1.22, x=0.5, xanchor="center"))


def build_degeneracy_figure(rows):
    """Je Struktur die Änderung durch die Degeneracy-Außenschleife gegenüber dem Pivot global, in Prozent: Auswahlkosten und Aufrufe."""
    names = [f"{r['name']} (d = {r['degeneracy']:.0f})" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=[ev.select_cost_change(r) for r in rows], orientation="h", name="Auswahlkosten", marker_color="#4c78a8",
                         hovertemplate="%{x:+.1f} %%<extra>Auswahlkosten</extra>"))
    fig.add_trace(go.Bar(y=names, x=[ev.calls_change(r) for r in rows], orientation="h", name="Aufrufe", marker_color="#e0a030",
                         hovertemplate="%{x:+.1f} %%<extra>Aufrufe</extra>"))
    fig.update_xaxes(title="Änderung gegenüber Pivot global (%)", zeroline=True)
    fig.update_yaxes(autorange="reversed")
    return _fix(fig, 460, barmode="group", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"), margin=dict(l=240, r=20, t=30, b=50))


def build_size_figure(sizes):
    """Größenverteilung der maximalen Cliquen."""
    fig = go.Figure(go.Bar(x=[str(k) for k in sizes], y=list(sizes.values()), marker_color=C.COLOR_R,
                           hovertemplate="%{y} Fuhren mit %{x} Sendungen<extra></extra>"))
    fig.update_xaxes(title="Größe der maximalen Clique (Sendungen je Fuhre)", type="category")
    fig.update_yaxes(title="Anzahl")
    return _fix(fig, 280)
