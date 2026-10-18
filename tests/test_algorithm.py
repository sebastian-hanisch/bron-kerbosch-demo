"""Kern gegen Handrechnung (Mini-Instanz) und Brute Force: jede Einheit einzeln, dann die Komposition."""

import pytest

import bkr_algorithm as A
import bkr_scenario as S

CLIQUES_MINI = {(0, 1, 2), (2, 3), (4,)}


# --- Einheiten ------------------------------------------------------------------------------------------------------------------------------

def test_choose_pivot_tomita_picks_most_neighbours_in_p_with_smallest_index_on_ties(mini):
    assert A.choose_pivot_tomita({0, 1, 2, 3, 4}, set(), mini) == 2          # 2 hat 3 Nachbarn in P
    assert A.choose_pivot_tomita({0, 1, 3}, set(), mini) == 0                # 0 und 1 haben je 1 Nachbarn in P: kleinster Index
    assert A.choose_pivot_tomita({2}, {0}, mini) == 0                        # Pivot darf aus X kommen (0 hat Nachbar 2 in P)
    assert A.choose_pivot_tomita(set(), set(), mini) is None


def test_pivot_select_cost_counts_min_of_p_and_degree(mini):
    assert A.pivot_select_cost({0, 1, 2, 3, 4}, set(), mini) == 8            # min(5,2)+min(5,2)+min(5,3)+min(5,1)+min(5,0)
    assert A.pivot_select_cost({0, 1, 3}, set(), mini) == 5                  # 2 + 2 + 1


def test_split_candidates_without_pivot_takes_all_with_pivot_skips_its_neighbours(mini):
    assert A.split_candidates({0, 1, 2, 3, 4}, mini, None) == [0, 1, 2, 3, 4]
    assert A.split_candidates({0, 1, 2, 3, 4}, mini, 2) == [2, 4]            # 0, 1, 3 sind Nachbarn von 2
    assert A.split_candidates(set(), mini, None) == []


def test_child_sets_restrict_p_and_x_to_neighbours(mini):
    assert A.child_sets({0, 1, 3, 4}, {2}, 2, mini) == ({0, 1, 3}, set())      # X = {2} ∩ N(2) = ∅: 2 ist kein Nachbar von sich selbst
    assert A.child_sets({1, 2}, {0}, 1, mini) == ({2}, {0})


def test_is_maximal_needs_both_sets_empty():
    assert A.is_maximal(set(), set())
    assert not A.is_maximal({1}, set())
    assert not A.is_maximal(set(), {1})


def test_degeneracy_order_peels_smallest_degree_first(mini):
    order, d = A.degeneracy_order(mini)
    assert order == [4, 3, 0, 1, 2] and d == 2


def test_degeneracy_of_known_families():
    assert A.degeneracy_order(S.tree_graph(30, 1).adj)[1] == 1
    assert A.degeneracy_order(S.grid_graph(5).adj)[1] == 2
    assert A.degeneracy_order(S.adjacency_from_edges(6, [(i, j) for i in range(6) for j in range(i + 1, 6)]))[1] == 5
    assert A.degeneracy_order(S.adjacency_from_edges(4, []))[1] == 0


def test_outer_split_separates_later_and_earlier_neighbours(mini):
    order, _ = A.degeneracy_order(mini)
    position = {v: i for i, v in enumerate(order)}
    assert A.outer_split(1, position, mini) == ({2}, {0})
    assert A.outer_split(4, position, mini) == (set(), set())


# --- Komposition auf der Mini-Instanz -------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("variant", ["naive", "pivot", "degeneracy"])
def test_mini_cliques(mini, variant):
    res = A.bron_kerbosch(mini, variant)
    assert set(res.cliques) == CLIQUES_MINI and len(res.cliques) == 3


def test_mini_call_counts_by_hand(mini):
    assert A.bron_kerbosch(mini, "naive").calls == 11
    assert A.bron_kerbosch(mini, "pivot").calls == 6
    assert A.bron_kerbosch(mini, "degeneracy").calls == 8


def test_mini_select_cost_by_hand(mini):
    assert A.bron_kerbosch(mini, "naive").select_cost == 0
    assert A.bron_kerbosch(mini, "pivot").select_cost == 14


def test_mini_discovery_order_with_pivot(mini):
    assert A.bron_kerbosch(mini, "pivot").cliques == [(0, 1, 2), (2, 3), (4,)]


def test_mini_trace_matches_call_count_and_first_frames(mini):
    res = A.bron_kerbosch(mini, "pivot", trace_limit=100)
    assert len(res.trace) == res.calls == 6 and not res.trace_truncated
    first = res.trace[0]
    assert (first.R, first.P, first.X, first.pivot, first.branch, first.found) == ((), (0, 1, 2, 3, 4), (), 2, (2, 4), False)
    assert [f.found for f in res.trace].count(True) == 3


def test_trace_is_truncated_and_flagged(mini):
    res = A.bron_kerbosch(mini, "naive", trace_limit=4)
    assert len(res.trace) == 4 and res.trace_truncated and res.calls == 11


def test_budget_aborts_and_reports(mini):
    res = A.bron_kerbosch(mini, "naive", budget=5)
    assert res.aborted and res.calls == 6          # der sechste Aufruf überschreitet das Budget
    assert not A.bron_kerbosch(mini, "naive", budget=11).aborted


def test_empty_graph_and_single_vertex():
    assert A.bron_kerbosch(S.adjacency_from_edges(0, []), "pivot").cliques == []
    for variant in ("naive", "pivot", "degeneracy"):
        assert A.bron_kerbosch(S.adjacency_from_edges(1, []), variant).cliques == [(0,)]
        assert A.bron_kerbosch(S.adjacency_from_edges(3, []), variant).cliques == [(0,), (1,), (2,)]


def test_unknown_variant_raises(mini):
    with pytest.raises(ValueError):
        A.bron_kerbosch(mini, "magic")


# --- Brute Force als Referenz ---------------------------------------------------------------------------------------------------------------

def test_brute_force_on_mini(mini):
    assert set(A.brute_force_maximal_cliques(mini)) == CLIQUES_MINI


def test_brute_force_independent_sets_on_mini_by_hand(mini):
    # Konfliktgraph = mini: unabhängig und maximal sind {0,3,4}, {1,3,4}, {2,4}
    assert A.brute_force_maximal_independent_sets(mini) == [(0, 3, 4), (1, 3, 4), (2, 4)]


@pytest.mark.parametrize("seed", range(40))
def test_all_variants_equal_brute_force_on_random_graphs(seed):
    n = 3 + seed % 10
    g = S.random_graph(n, 20 + 15 * (seed % 5), seed)
    ref = set(A.brute_force_maximal_cliques(g.adj))
    for variant in ("naive", "pivot", "degeneracy"):
        res = A.bron_kerbosch(g.adj, variant)
        assert set(res.cliques) == ref and len(res.cliques) == len(ref), (variant, seed)


# --- Trace-Einzelheiten (aus der Mutationsprüfung: Tiefe und Reihenfolge von P und X waren ungeprüft) ---------------------------------------

def test_trace_depths_on_mini_by_hand(mini):
    res = A.bron_kerbosch(mini, "pivot", trace_limit=20)
    assert [f.depth for f in res.trace] == [0, 1, 2, 3, 2, 1]        # R = [], [2], [2,0], [2,0,1], [2,3], [4]
    assert [len(f.R) for f in res.trace] == [0, 1, 2, 3, 2, 1]


def test_degeneracy_trace_depths_start_at_zero_for_every_root(mini):
    res = A.bron_kerbosch(mini, "degeneracy", trace_limit=20)
    roots = [f for f in res.trace if f.depth == 0]
    assert [f.R for f in roots] == [(4,), (3,), (0,), (1,), (2,)]     # Reihenfolge der Degeneracy-Ordnung [4, 3, 0, 1, 2]
    assert [f.depth for f in res.trace] == [0, 0, 1, 0, 1, 2, 0, 0]


def test_trace_sets_p_and_x_are_sorted_ascending_and_x_is_filled_along_the_way():
    g = S.random_graph(12, 60, 4)
    res = A.bron_kerbosch(g.adj, "naive", trace_limit=500)
    assert any(len(f.X) >= 2 for f in res.trace)
    for f in res.trace:
        assert list(f.P) == sorted(f.P) and list(f.X) == sorted(f.X)
        assert not set(f.P) & set(f.X) and not set(f.R) & (set(f.P) | set(f.X))


def test_branch_candidates_in_the_trace_are_ascending(mini):
    for variant in ("naive", "pivot", "degeneracy"):
        for f in A.bron_kerbosch(mini, variant, trace_limit=20).trace:
            assert list(f.branch) == sorted(f.branch)


def test_brute_force_returns_sorted_results_and_handles_the_empty_graph(mini):
    assert A.brute_force_maximal_cliques(mini) == [(0, 1, 2), (2, 3), (4,)]
    assert A.brute_force_maximal_cliques(S.adjacency_from_edges(0, [])) == []
    assert A.brute_force_maximal_independent_sets(S.adjacency_from_edges(0, [])) == []
    assert A.brute_force_maximal_cliques(S.adjacency_from_edges(3, [])) == [(0,), (1,), (2,)]
