"""Zweig-Tests (Nullspalten-Lehre): jede Variante weicht auf mindestens einer Instanz von ihrer Nachbarvariante ab,
jede Regel ist wirksam, und die Rechengrenzen greifen wirklich."""

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S


def test_pivot_differs_from_no_pivot_on_a_dense_graph():
    g = S.random_graph(14, 80, 1)
    assert A.bron_kerbosch(g.adj, "pivot").calls < A.bron_kerbosch(g.adj, "naive").calls


def test_degeneracy_differs_from_global_pivot_on_a_graph_with_many_vertices():
    g = S.random_graph(30, 30, 1)
    assert A.bron_kerbosch(g.adj, "degeneracy").calls != A.bron_kerbosch(g.adj, "pivot").calls


def test_degeneracy_variant_has_cheaper_pivot_selection_on_sparse_and_dearer_on_dense_graphs():
    sparse = S.scale_free_graph(300, 3, 1)
    dense = S.random_graph(30, 70, 1)
    assert A.bron_kerbosch(sparse.adj, "degeneracy").select_cost < A.bron_kerbosch(sparse.adj, "pivot").select_cost
    assert A.bron_kerbosch(dense.adj, "degeneracy").select_cost > A.bron_kerbosch(dense.adj, "pivot").select_cost


def _calls_with_chooser(chooser, seed):
    """Aufrufzahl der Pivot-Variante mit einer ausgetauschten Pivotwahl (die Wahl ist eine eigene Einheit)."""
    saved = A.choose_pivot_tomita
    A.choose_pivot_tomita = chooser
    try:
        return A.bron_kerbosch(S.random_graph(12, 50, seed).adj, "pivot").calls
    finally:
        A.choose_pivot_tomita = saved


def test_pivot_tie_break_rule_is_effective():
    """Der Gleichstand der Pivotwahl (kleinster Index) entscheidet auf mindestens einer Instanz über die Aufrufzahl."""
    original = A.choose_pivot_tomita

    def largest_index_pivot(P, X, adj_):
        best, cnt = None, -1
        for u in sorted(P | X, reverse=True):
            c = len(P & adj_[u])
            if c > cnt:
                best, cnt = u, c
        return best

    assert any(_calls_with_chooser(largest_index_pivot, s) != _calls_with_chooser(original, s) for s in range(15))


def test_a_bad_pivot_costs_more_than_tomitas():
    """Ein Pivot mit den WENIGSTEN Nachbarn in P ist zulässig, aber schlechter: die Wahl ist also wirksam, nicht beliebig."""
    g = S.random_graph(16, 70, 2)
    good = A.bron_kerbosch(g.adj, "pivot").calls

    def worst_pivot(P, X, adj_):
        return min(sorted(P | X), key=lambda u: len(P & adj_[u])) if (P or X) else None

    original = A.choose_pivot_tomita
    try:
        A.choose_pivot_tomita = worst_pivot
        res = A.bron_kerbosch(g.adj, "pivot")
    finally:
        A.choose_pivot_tomita = original
    assert res.calls > good
    assert set(res.cliques) == set(A.bron_kerbosch(g.adj, "naive").cliques)      # trotzdem vollständig und korrekt


def test_the_call_budget_aborts_the_naive_variant_on_a_dense_window_graph_but_not_the_pivot():
    g = S.window_graph(C.N_MAX, C.DENSITY_MAX, 1)
    naive = A.bron_kerbosch(g.adj, "naive", budget=C.CALL_BUDGET)
    assert naive.aborted and naive.calls == C.CALL_BUDGET + 1
    assert not A.bron_kerbosch(g.adj, "pivot", budget=C.CALL_BUDGET).aborted


def test_analysis_takes_cliques_from_a_finished_variant_when_the_chosen_one_aborted():
    a = ev.analyse(ev.Settings(graph_type="windows", n=C.N_MAX, density=C.DENSITY_MAX, variant="naive"))
    assert a.result.aborted and a.complete and len(a.cliques) == len(a.runs["pivot"].cliques)


def test_trace_limit_applies_in_the_analysis():
    a = ev.analyse(ev.Settings(graph_type="windows", n=C.N_MAX, density=C.DENSITY_MAX, variant="naive"))
    assert len(a.result.trace) == C.TRACE_LIMIT and a.result.trace_truncated


def test_sweep_marks_aborted_runs_and_uses_the_budget_as_a_lower_bound():
    rows = ev.density_sweep("windows", seeds=(1, 2), densities=(90,), budget=500)
    assert rows[0]["aborted"]["naive"] == 2 and rows[0]["calls"]["naive"] == 501
    assert rows[0]["aborted"]["pivot"] == 0


def test_every_variant_runs_on_every_graph_type_at_the_slider_edges_within_the_budget():
    for gt in C.GRAPH_TYPES:
        for n in (C.N_MIN, C.N_MAX):
            for d in (C.DENSITY_MIN, C.DENSITY_MAX):
                a = ev.analyse(ev.Settings(graph_type=gt, n=n, density=d))
                assert a.complete and not a.runs["pivot"].aborted and not a.runs["degeneracy"].aborted, (gt, n, d)
