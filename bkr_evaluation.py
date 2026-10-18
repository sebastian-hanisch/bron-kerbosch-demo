"""Auswertung: Einstellungen, Analyse der Hauptansicht, Sweeps und Verdikte (alle Zahlen kommen aus diesen Funktionen, nie von Hand)."""

import statistics
from dataclasses import dataclass

import bkr_algorithm as A
import bkr_constants as C
import bkr_scenario as S


@dataclass(frozen=True)
class Settings:
    """Alle Regler der Seitenleiste. Immer mit Schlüsselwörtern bauen (ein eingefügtes Feld verschob früher still Werte)."""
    graph_type: str = C.DEFAULT_TYPE
    n: int = C.DEFAULT_N
    density: int = C.DEFAULT_DENSITY
    seed: int = C.DEFAULT_SEED
    variant: str = C.DEFAULT_VARIANT
    view: str = C.DEFAULT_VIEW


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    graph: S.Graph
    result: A.Result            # die gewählte Variante, mit Schritt-Trace
    runs: dict                  # Variante -> Result (ohne Trace), für den Vergleich der Kennzahlen
    cliques: tuple              # maximale Cliquen (aus der besten vollständig gelaufenen Variante), sortiert
    complete: bool              # False, wenn keine Variante innerhalb des Budgets fertig wurde


def analyse(settings):
    """Graph bauen und alle drei Varianten laufen lassen; die gewählte mit Trace."""
    g = S.build_graph(settings.graph_type, settings.n, settings.density, settings.seed)
    runs = {v: A.bron_kerbosch(g.adj, v, budget=C.CALL_BUDGET) for v in C.VARIANTS}
    chosen = A.bron_kerbosch(g.adj, settings.variant, budget=C.CALL_BUDGET, trace_limit=C.TRACE_LIMIT)
    finished = [r for r in (chosen, *runs.values()) if not r.aborted]
    cliques = tuple(sorted(finished[0].cliques)) if finished else ()
    return Analysis(settings, g, chosen, runs, cliques, bool(finished))


def clique_sizes(cliques):
    """Größenverteilung: {Größe: Anzahl} aufsteigend."""
    out = {}
    for c in cliques:
        out[len(c)] = out.get(len(c), 0) + 1
    return dict(sorted(out.items()))


def saving_factor(naive_calls, pivot_calls):
    """Wie viel mal so viele Aufrufe ohne Pivot gegenüber mit Pivot."""
    return naive_calls / pivot_calls if pivot_calls else float("inf")


# --- Experiment 1: Dichte-Sweep -----------------------------------------------------------------------------------------------------------

def density_sweep(graph_type, n=C.SWEEP_N, densities=C.SWEEP_DENSITIES, seeds=C.SWEEP_SEEDS, budget=C.SWEEP_BUDGET):
    """Je Dichte der Median über die festen Instanzen: Aufrufe der drei Varianten, Auswahlkosten, maximale Cliquen, Degeneracy.
    `aborted[v]` = in wie vielen der Instanzen die Variante das Budget überschritten hat (dann zählt der Lauf mit dem Budget als Untergrenze)."""
    rows = []
    for d in densities:
        per = {v: [] for v in C.VARIANTS}
        select = {v: [] for v in C.VARIANTS}
        aborted = {v: 0 for v in C.VARIANTS}
        counts, degs = [], []
        for seed in seeds:
            g = S.build_graph(graph_type, n, d, seed)
            ref = None
            for v in C.VARIANTS:
                r = A.bron_kerbosch(g.adj, v, budget=budget)
                per[v].append(r.calls)
                select[v].append(r.select_cost)
                aborted[v] += int(r.aborted)
                if not r.aborted and ref is None:
                    ref = r
            counts.append(len(ref.cliques) if ref else 0)
            degs.append(A.degeneracy_order(g.adj)[1])
        rows.append({
            "density": d,
            "calls": {v: statistics.median(per[v]) for v in C.VARIANTS},
            "select": {v: statistics.median(select[v]) for v in C.VARIANTS},
            "aborted": aborted,
            "cliques": statistics.median(counts),
            "degeneracy": statistics.median(degs),
        })
    return rows


def sweep_verdict(rows):
    """Die Aussage zum Dichte-Sweep, aus den Zeilen berechnet: größter Faktor ohne Pivot gegen mit Pivot und kleinster."""
    factors = [(r["density"], saving_factor(r["calls"]["naive"], r["calls"]["pivot"])) for r in rows]
    best = max(factors, key=lambda t: t[1])
    worst = min(factors, key=lambda t: t[1])
    return {"best_density": best[0], "best_factor": best[1], "worst_density": worst[0], "worst_factor": worst[1],
            "any_aborted": any(r["aborted"]["naive"] for r in rows)}


# --- Experiment 2: Moon–Moser ---------------------------------------------------------------------------------------------------------------

def moon_moser_rows(ks=C.MOON_MOSER_KS):
    """Je k: n = 3k, maximale Cliquen, Aufrufe der drei Varianten und die geschlossenen Formeln (4^k ohne Pivot, (3^(k+1) - 1) / 2 mit Pivot)."""
    rows = []
    for k in ks:
        g = S.moon_moser_graph(k)
        runs = {v: A.bron_kerbosch(g.adj, v) for v in C.VARIANTS}
        rows.append({
            "k": k, "n": g.n, "cliques": len(runs["pivot"].cliques), "bound": 3 ** k,
            "calls": {v: runs[v].calls for v in C.VARIANTS},
            "formula_naive": 4 ** k, "formula_pivot": (3 ** (k + 1) - 1) // 2,
        })
    return rows


# --- Experiment 3: Strukturen und Degeneracy -----------------------------------------------------------------------------------------------

STRUCTURES = (
    ("Baum, n = 200", lambda seed: S.tree_graph(200, seed)),
    ("Gitter 15 × 15", lambda seed: S.grid_graph(15)),
    ("skalenfrei, n = 1000, m = 3", lambda seed: S.scale_free_graph(1000, 3, seed)),
    ("skalenfrei, n = 1000, m = 8", lambda seed: S.scale_free_graph(1000, 8, seed)),
    ("Zufall dünn, n = 300, 2 % verträglich", lambda seed: S.random_graph(300, 2, seed)),
    ("Zeitfenster, n = 200, 10 %", lambda seed: S.window_graph(200, 10, seed)),
    ("Zufall dicht, n = 40, 50 %", lambda seed: S.random_graph(40, 50, seed)),
    ("Zufall dicht, n = 40, 80 %", lambda seed: S.random_graph(40, 80, seed)),
)


def structure_rows(seeds=C.SWEEP_SEEDS[:3]):
    """Je Struktur der Median über die festen Instanzen: Aufrufe, Auswahlkosten und Degeneracy. Zeigt, wo die Degeneracy-Außenschleife die Pivot-Auswahl verbilligt und wo nicht."""
    rows = []
    for name, build in STRUCTURES:
        calls = {v: [] for v in C.VARIANTS}
        select = {v: [] for v in C.VARIANTS}
        cliques, degs, aborted = [], [], 0
        for seed in seeds:
            g = build(seed)
            for v in C.VARIANTS:
                r = A.bron_kerbosch(g.adj, v, budget=C.SWEEP_BUDGET * 4)
                calls[v].append(r.calls)
                select[v].append(r.select_cost)
                aborted += int(r.aborted)
            cliques.append(len(A.bron_kerbosch(g.adj, "pivot", budget=C.SWEEP_BUDGET * 4).cliques))
            degs.append(A.degeneracy_order(g.adj)[1])
        rows.append({
            "name": name, "n": build(seeds[0]).n,
            "calls": {v: statistics.median(calls[v]) for v in C.VARIANTS},
            "select": {v: statistics.median(select[v]) for v in C.VARIANTS},
            "cliques": statistics.median(cliques), "degeneracy": statistics.median(degs), "aborted": aborted,
        })
    return rows


def select_cost_change(row):
    """Relative Änderung der Pivot-Auswahlkosten durch die Degeneracy-Außenschleife in Prozent (negativ = billiger)."""
    return 100.0 * (row["select"]["degeneracy"] / row["select"]["pivot"] - 1.0) if row["select"]["pivot"] else 0.0


def calls_change(row):
    """Relative Änderung der Aufrufzahl durch die Degeneracy-Außenschleife in Prozent (positiv = mehr Aufrufe)."""
    return 100.0 * (row["calls"]["degeneracy"] / row["calls"]["pivot"] - 1.0) if row["calls"]["pivot"] else 0.0


# --- Experiment 4: Komplement-Brücke --------------------------------------------------------------------------------------------------------

def complement_check(settings, n=C.CHECK_N):
    """Auf einer kleinen Instanz (n = CHECK_N, Typ, Dichte und Seed wie eingestellt): die Cliquen des Verträglichkeitsgraphen und die maximalen unabhängigen
    Mengen des Konfliktgraphen (per Aufzählen aller Teilmengen, ohne Bron–Kerbosch) sind dieselben Mengen."""
    g = S.build_graph(settings.graph_type, n, settings.density, settings.seed)
    conflict = S.complement(g.adj)
    cliques = set(A.bron_kerbosch(g.adj, "pivot").cliques)
    independent = set(A.brute_force_maximal_independent_sets(conflict))
    conflict_cliques = set(A.bron_kerbosch(conflict, "pivot").cliques)
    independent_of_compat = set(A.brute_force_maximal_independent_sets(g.adj))
    return {"n": n, "cliques": len(cliques), "independent": len(independent), "equal": cliques == independent,
            "conflict_cliques": len(conflict_cliques), "equal_back": conflict_cliques == independent_of_compat}
