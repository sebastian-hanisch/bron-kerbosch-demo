"""Jede Zahl aus README und App wird hier nachgerechnet (DEMO-PLAYBOOK §4: erst messen, dann Text schreiben).
Alle Zählwerte sind ganzzahlig und plattformunabhängig exakt; Prozentwerte mit enger Toleranz (Rundung)."""

import math

import pytest

import bkr_algorithm as A
import bkr_constants as C
import bkr_evaluation as ev
import bkr_scenario as S


def _analysis(preset):
    p = C.PRESETS[preset]
    return ev.analyse(ev.Settings(graph_type=p["type"], n=p["n"], density=p["density"], seed=p["seed"], variant=p["variant"], view=p["view"]))


# --- Standardfall: 14 Sendungen, 50 %, Seed 35 -------------------------------------------------------------------------------------------------

def test_default_case_numbers():
    a = ev.analyse(ev.Settings())
    assert len(a.cliques) == 23 and ev.clique_sizes(a.cliques) == {3: 19, 4: 4}
    assert (a.runs["naive"].calls, a.runs["pivot"].calls, a.runs["degeneracy"].calls) == (96, 44, 56)
    assert (a.runs["pivot"].select_cost, a.runs["degeneracy"].select_cost) == (336, 345)
    assert a.result.degeneracy == 5


# --- Presets ----------------------------------------------------------------------------------------------------------------------------------

def test_preset_numbers():
    a = _analysis("Lehrbeispiel (klein)")
    assert len(a.cliques) == 6 and (a.runs["naive"].calls, a.runs["pivot"].calls) == (43, 16)
    a = _analysis("Dicht: der Pivot rettet")
    assert len(a.cliques) == 104 and (a.runs["naive"].calls, a.runs["pivot"].calls, a.runs["degeneracy"].calls) == (20720, 255, 336)
    assert math.isclose(ev.saving_factor(20720, 255), 81.25, abs_tol=0.01)
    a = _analysis("Dünn: der Pivot egal")
    assert len(a.cliques) == 41 and (a.runs["naive"].calls, a.runs["pivot"].calls) == (88, 72)
    a = _analysis("Zeitfenster")
    assert len(a.cliques) == 8 and (a.runs["naive"].calls, a.runs["pivot"].calls) == (524, 47)
    a = _analysis("Klassenregeln")
    assert len(a.cliques) == 11 and (a.runs["naive"].calls, a.runs["pivot"].calls) == (101696, 42)


# --- Experiment 1: Dichte-Sweep ---------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def sweep_random():
    return ev.density_sweep("random")


def test_random_sweep_numbers(sweep_random):
    by = {r["density"]: r for r in sweep_random}
    assert (by[10]["calls"]["naive"], by[10]["calls"]["pivot"]) == (41, 35)
    assert (by[90]["calls"]["naive"], by[90]["calls"]["pivot"], by[90]["calls"]["degeneracy"]) == (34688, 165, 217)
    assert not any(r["aborted"]["naive"] for r in sweep_random)
    v = ev.sweep_verdict(sweep_random)
    assert (v["worst_density"], v["best_density"]) == (10, 90)
    assert math.isclose(v["worst_factor"], 41 / 35) and math.isclose(v["best_factor"], 34688 / 165)


def test_window_and_class_sweeps_hit_the_budget_without_pivot_at_90_percent():
    for gt, pivot_calls, aborted in (("windows", 24, 5), ("classes", 25, 4)):       # aborted: von 5 festen Instanzen
        rows = ev.density_sweep(gt, densities=(90,))
        assert rows[0]["aborted"]["naive"] == aborted and rows[0]["calls"]["naive"] == C.SWEEP_BUDGET + 1
        assert rows[0]["calls"]["pivot"] == pivot_calls and rows[0]["aborted"]["pivot"] == 0


def test_the_pivot_never_needs_more_calls_than_no_pivot_in_the_random_sweep(sweep_random):
    assert all(r["calls"]["pivot"] <= r["calls"]["naive"] for r in sweep_random)


# --- Experiment 2: Moon–Moser -----------------------------------------------------------------------------------------------------------------

def test_moon_moser_formulas_hold_for_k_1_to_7():
    rows = ev.moon_moser_rows()
    assert [r["k"] for r in rows] == [1, 2, 3, 4, 5, 6, 7]
    for r in rows:
        k = r["k"]
        assert r["n"] == 3 * k and r["cliques"] == 3 ** k
        assert r["calls"]["naive"] == 4 ** k and r["calls"]["pivot"] == (3 ** (k + 1) - 1) // 2
    last = rows[-1]
    assert (last["cliques"], last["calls"]["naive"], last["calls"]["pivot"]) == (2187, 16384, 3280)


def test_pivot_calls_are_about_one_and_a_half_times_the_cliques_on_moon_moser():
    for r in ev.moon_moser_rows():
        assert 1.3 <= r["calls"]["pivot"] / r["cliques"] <= 1.67


# --- Experiment 3: Strukturen -----------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def structures():
    return {r["name"]: r for r in ev.structure_rows()}


def test_structure_table_numbers(structures):
    s = structures
    tree, grid = s["Baum, n = 200"], s["Gitter 15 × 15"]
    assert (tree["cliques"], tree["degeneracy"]) == (199, 1) and (grid["cliques"], grid["degeneracy"]) == (420, 2)
    assert (tree["select"]["pivot"], tree["select"]["degeneracy"]) == (890, 397)
    assert (grid["select"]["pivot"], grid["select"]["degeneracy"]) == (2434, 1594)
    dense80 = s["Zufall dicht, n = 40, 80 %"]
    assert (dense80["cliques"], dense80["degeneracy"]) == (3151, 26)
    assert (dense80["calls"]["pivot"], dense80["calls"]["degeneracy"]) == (7364, 7897)
    assert dense80["aborted"] == 3 and dense80["calls"]["naive"] == 4 * C.SWEEP_BUDGET + 1


def test_degeneracy_selection_cost_changes_in_percent(structures):
    expected = {"Baum, n = 200": -55.4, "Gitter 15 × 15": -34.5, "skalenfrei, n = 1000, m = 3": -27.7, "skalenfrei, n = 1000, m = 8": -12.1,
                "Zufall dünn, n = 300, 2 % verträglich": -26.7, "Zeitfenster, n = 200, 10 %": 9.5, "Zufall dicht, n = 40, 50 %": 22.3, "Zufall dicht, n = 40, 80 %": 30.8}
    assert set(structures) == set(expected)
    for name, value in expected.items():
        assert math.isclose(ev.select_cost_change(structures[name]), value, abs_tol=0.05), name
    cheaper = [n for n, r in structures.items() if ev.select_cost_change(r) < 0]
    dearer = [n for n, r in structures.items() if ev.select_cost_change(r) > 0]
    assert (len(cheaper), len(dearer)) == (5, 3)


def test_degeneracy_reduces_the_call_count_in_only_one_structure_and_by_at_most_a_quarter_percent(structures):
    fewer = {n: ev.calls_change(r) for n, r in structures.items() if ev.calls_change(r) < 0}
    assert list(fewer) == ["skalenfrei, n = 1000, m = 8"]
    assert math.isclose(fewer["skalenfrei, n = 1000, m = 8"], -0.2, abs_tol=0.05)
    more = [ev.calls_change(r) for r in structures.values() if ev.calls_change(r) > 0]
    assert len(more) == 7 and math.isclose(min(more), 0.5, abs_tol=0.05) and math.isclose(max(more), 9.8, abs_tol=0.05)


def test_pivot_barely_helps_on_a_tree_and_a_grid(structures):
    tree, grid = structures["Baum, n = 200"], structures["Gitter 15 × 15"]
    assert (tree["calls"]["naive"], tree["calls"]["pivot"]) == (400, 391)
    assert (grid["calls"]["naive"], grid["calls"]["pivot"]) == (646, 642)


# --- Experiment 4: Komplement -----------------------------------------------------------------------------------------------------------------

def test_complement_bridge_on_the_default_small_instance():
    cc = ev.complement_check(ev.Settings())
    assert cc["n"] == 14 and cc["cliques"] == cc["independent"] == 23 and cc["equal"]
    assert cc["conflict_cliques"] == 25 and cc["equal_back"]


# --- Rechengrenzen -----------------------------------------------------------------------------------------------------------------------------

def test_budgets_and_limits_as_documented():
    assert (C.CALL_BUDGET, C.SWEEP_BUDGET, C.TRACE_LIMIT, C.SWEEP_N, C.CHECK_N) == (200_000, 60_000, 400, 20, 14)
    assert (C.N_MIN, C.N_MAX, C.DENSITY_MIN, C.DENSITY_MAX) == (6, 40, 5, 95)
    assert A.bron_kerbosch(S.random_graph(40, 95, 35).adj, "naive", budget=C.CALL_BUDGET).aborted
