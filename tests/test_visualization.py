"""Figuren: jede lässt sich für jeden Schritt und jede Ansicht bauen, die Zustandsfarben stimmen, alle Achsen sind fest."""

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S
import bkr_visualization as V


def _node_trace(fig):
    return next(t for t in fig.data if t.mode == "markers+text")


def _all_axes_fixed(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_graph_figure_builds_for_every_frame_and_view():
    a = ev.analyse(ev.Settings(n=10))
    for view in C.VIEWS:
        for frame in a.result.trace:
            fig = V.build_graph_figure(a.graph, view, frame=frame)
            assert len(_node_trace(fig).x) == a.graph.n and _all_axes_fixed(fig)


def test_node_colours_follow_r_p_x_and_pivot(mini):
    res = A.bron_kerbosch(mini, "pivot", trace_limit=10)
    g = S.Graph(5, mini, S.circle_positions(list(range(5))), tuple(str(i) for i in range(5)), "random")
    first = res.trace[0]                                  # R = ∅, P = alle, Pivot 2
    colors = list(_node_trace(V.build_graph_figure(g, "compat", frame=first)).marker.color)
    assert colors == [C.COLOR_P] * 5
    outline = list(_node_trace(V.build_graph_figure(g, "compat", frame=first)).marker.line.color)
    assert outline[2] == C.COLOR_PIVOT and outline[0] == "white"
    found = next(f for f in res.trace if f.found and set(f.R) == {0, 1, 2})
    colors = list(_node_trace(V.build_graph_figure(g, "compat", frame=found)).marker.color)
    assert colors[0] == colors[1] == colors[2] == C.COLOR_FOUND and colors[4] == C.COLOR_IDLE
    inner = next(f for f in res.trace if f.R == (2,) and not f.found)
    colors = list(_node_trace(V.build_graph_figure(g, "compat", frame=inner)).marker.color)
    assert colors[2] == C.COLOR_R and colors[0] == colors[1] == colors[3] == C.COLOR_P


def test_conflict_view_draws_the_complement_edges(mini):
    g = S.Graph(5, mini, S.circle_positions(list(range(5))), tuple(str(i) for i in range(5)), "random")
    assert len(V.shown_edges(g, "compat")) == 4
    assert len(V.shown_edges(g, "conflict")) == 10 - 4


def test_final_clique_is_highlighted_without_a_frame(mini):
    g = S.Graph(5, mini, S.circle_positions(list(range(5))), tuple(str(i) for i in range(5)), "random")
    colors = list(_node_trace(V.build_graph_figure(g, "compat", final_clique=(0, 1, 2))).marker.color)
    assert colors[:3] == [C.COLOR_FOUND] * 3 and colors[3] == C.COLOR_IDLE


def test_experiment_figures_build_and_lock_their_axes():
    sweep = ev.density_sweep("random", densities=(10, 90), seeds=(1,))
    for fig in (V.build_sweep_figure(sweep), V.build_moon_moser_figure(ev.moon_moser_rows(ks=(1, 2, 3))),
                V.build_degeneracy_figure(ev.structure_rows(seeds=(1,))), V.build_size_figure({3: 2, 4: 1})):
        assert _all_axes_fixed(fig)


def test_sweep_figure_marks_aborted_medians():
    rows = ev.density_sweep("windows", densities=(90,), seeds=(1, 2), budget=300)
    fig = V.build_sweep_figure(rows)
    assert any(t.marker.symbol == "square-open" for t in fig.data if t.marker is not None and t.marker.symbol)
