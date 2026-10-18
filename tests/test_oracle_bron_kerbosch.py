"""Orakel-Test bron-kerbosch-demo: alle drei Varianten gegen networkx.find_cliques und gegen Brute Force.

Orakel 1: `networkx.find_cliques` (ein anderer Rechenweg, eigene Pivot-Implementierung der Bibliothek). Orakel 2: Aufzählen aller Teilmengen für n <= 16
(`brute_force_maximal_cliques`, ohne jede Rekursion). Verglichen werden MENGEN von Cliquen, nie die Reihenfolge; jede Clique genau einmal.
Dazu: Familien mit bekanntem Wert (Moon–Moser, Baum, vollständiger Graph) und die Komplement-Identität gegen Brute Force über unabhängige Mengen."""

import pytest

import bkr_algorithm as A
import bkr_scenario as S

nx = pytest.importorskip("networkx")

VARIANTS = ("naive", "pivot", "degeneracy")


def _nx_cliques(adj):
    G = nx.Graph()
    G.add_nodes_from(range(len(adj)))
    G.add_edges_from((u, v) for u in range(len(adj)) for v in adj[u] if u < v)
    return {tuple(sorted(c)) for c in nx.find_cliques(G)}


def _instances():
    """>= 300 feste Instanzen: Zufallsgraphen über Größe und Dichte, Zeitfenster, Klassenregeln, Sonderfälle."""
    out = []
    for seed in range(150):
        out.append(("random", S.random_graph(2 + seed % 15, 5 + 10 * (seed % 10), seed).adj))
    for seed in range(60):
        out.append(("windows", S.window_graph(3 + seed % 14, 10 + 10 * (seed % 8), seed).adj))
    for seed in range(60):
        out.append(("classes", S.class_graph(3 + seed % 14, 10 + 10 * (seed % 8), seed).adj))
    for n in range(1, 10):
        out.append(("empty", S.adjacency_from_edges(n, [])))
        out.append(("complete", S.adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n)])))
        out.append(("path", S.adjacency_from_edges(n, [(i, i + 1) for i in range(n - 1)])))
        out.append(("star", S.adjacency_from_edges(n, [(0, i) for i in range(1, n)])))
    for n in range(3, 10):
        out.append(("cycle", S.adjacency_from_edges(n, [(i, (i + 1) % n) for i in range(n)])))
    out.append(("two components", S.adjacency_from_edges(7, [(0, 1), (1, 2), (0, 2), (4, 5), (5, 6)])))
    return out


INSTANCES = _instances()


def test_there_are_at_least_300_instances():
    assert len(INSTANCES) >= 300


def test_all_variants_equal_networkx_on_every_instance():
    for name, adj in INSTANCES:
        ref = _nx_cliques(adj)
        for variant in VARIANTS:
            res = A.bron_kerbosch(adj, variant)
            assert set(res.cliques) == ref and len(res.cliques) == len(ref), (name, len(adj), variant)


def test_all_variants_equal_brute_force_on_small_instances():
    checked = 0
    for name, adj in INSTANCES:
        if len(adj) > 12:
            continue
        ref = set(A.brute_force_maximal_cliques(adj))
        for variant in VARIANTS:
            assert set(A.bron_kerbosch(adj, variant).cliques) == ref, (name, variant)
        checked += 1
    assert checked >= 200


def test_every_reported_clique_is_a_clique_and_maximal():
    for name, adj in INSTANCES[:120]:
        res = A.bron_kerbosch(adj, "pivot")
        for c in res.cliques:
            assert all(v in adj[u] for i, u in enumerate(c) for v in c[i + 1:]), (name, c)
            outside = [w for w in range(len(adj)) if w not in c and all(w in adj[u] for u in c)]
            assert not outside, (name, c)


@pytest.mark.parametrize("k", range(1, 7))
def test_moon_moser_has_exactly_three_to_the_k_maximal_cliques(k):
    g = S.moon_moser_graph(k)
    assert len(_nx_cliques(g.adj)) == 3 ** k
    for variant in VARIANTS:
        assert len(A.bron_kerbosch(g.adj, variant).cliques) == 3 ** k


def test_tree_cliques_are_exactly_the_edges():
    g = S.tree_graph(60, 3)
    for variant in VARIANTS:
        assert set(A.bron_kerbosch(g.adj, variant).cliques) == {tuple(e) for e in g.edges()}


def test_complete_graph_has_one_clique():
    n = 7
    adj = S.adjacency_from_edges(n, [(i, j) for i in range(n) for j in range(i + 1, n)])
    for variant in VARIANTS:
        assert A.bron_kerbosch(adj, variant).cliques == [tuple(range(n))]


@pytest.mark.parametrize("seed", range(25))
def test_cliques_of_g_are_the_maximal_independent_sets_of_the_complement(seed):
    g = S.random_graph(4 + seed % 9, 20 + 12 * (seed % 6), seed)
    cliques = set(A.bron_kerbosch(g.adj, "pivot").cliques)
    independent_sets_of_complement = set(A.brute_force_maximal_independent_sets(S.complement(g.adj)))
    assert cliques == independent_sets_of_complement
    # und umgekehrt: Cliquen des Komplements sind die maximalen unabhängigen Mengen von G
    assert set(A.bron_kerbosch(S.complement(g.adj), "pivot").cliques) == set(A.brute_force_maximal_independent_sets(g.adj))
