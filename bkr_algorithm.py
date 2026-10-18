"""Bron–Kerbosch: alle maximalen Cliquen in drei Varianten (ohne Pivot, Tomita-Pivot, Degeneracy-Außenschleife).

Jede Regel ist eine eigene kleine Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK 1b); `bron_kerbosch` ruft sie nur der Reihe nach auf.
Ein *Aufruf* ist ein Aufruf von `expand(R, P, X)`: R = bisher gewählte Knoten (eine Clique), P = Kandidaten, die R noch erweitern können,
X = Knoten, die R erweitern würden, aber schon abgearbeitet sind (eine Clique mit einem X-Knoten wurde schon gefunden).
Reine Python-Mengen, Nachbarreihenfolge fest aufsteigend, kein Zufall: das Ergebnis ist vollständig deterministisch."""

from dataclasses import dataclass, field

import bkr_constants as C


class BudgetExceeded(Exception):
    """Das Aufrufbudget ist aufgebraucht; der Lauf bricht ab."""


@dataclass(frozen=True)
class Frame:
    """Ein Aufruf für die Schritt-Ansicht."""
    depth: int
    R: tuple
    P: tuple
    X: tuple
    pivot: object          # Pivotknoten oder None
    branch: tuple          # die Kandidaten, auf denen dieser Aufruf verzweigt
    found: bool            # R ist in diesem Aufruf als maximale Clique gemeldet worden


@dataclass
class Result:
    variant: str
    cliques: list                      # sortierte Tupel in der Reihenfolge des Fundes
    calls: int                         # Zahl der expand-Aufrufe
    select_cost: int                   # Kosten der Pivot-Auswahl (Elementarschritte), 0 ohne Pivot
    degeneracy: int
    aborted: bool = False
    trace: list = field(default_factory=list)
    trace_truncated: bool = False


# --- Einheiten -------------------------------------------------------------------------------------------------------------------------------

def choose_pivot_tomita(P, X, adj):
    """Pivot nach Tomita: der Knoten u aus P ∪ X mit den meisten Nachbarn in P (Gleichstand: kleinster Index). Leeres P ∪ X: None."""
    best, best_count = None, -1
    for u in sorted(P | X):
        count = len(P & adj[u])
        if count > best_count:
            best, best_count = u, count
    return best


def pivot_select_cost(P, X, adj):
    """Elementarschritte der Pivot-Auswahl: für jeden Kandidaten u aus P ∪ X der Schnitt P ∩ N(u), gezählt mit min(|P|, |N(u)|)."""
    return sum(min(len(P), len(adj[u])) for u in P | X)


def split_candidates(P, adj, pivot):
    """Die Kandidaten, auf denen verzweigt wird: ohne Pivot alle aus P, mit Pivot nur die aus P ohne Nachbarn von pivot (aufsteigend)."""
    if pivot is None:
        return sorted(P)
    return sorted(P - adj[pivot])


def child_sets(P, X, v, adj):
    """Mengen des Kindaufrufs bei Aufnahme von v: P und X werden auf die Nachbarn von v beschränkt."""
    return P & adj[v], X & adj[v]


def is_maximal(P, X):
    """R ist eine maximale Clique genau dann, wenn weder ein Kandidat (P) noch ein bereits abgearbeiteter Knoten (X) R erweitern kann."""
    return not P and not X


def degeneracy_order(adj):
    """Degeneracy-Ordnung: wiederholt der Knoten mit dem kleinsten Restgrad entfernt (Gleichstand: kleinster Index). Gibt (Ordnung, Degeneracy d) zurück,
    d = der größte Restgrad zum Zeitpunkt des Entfernens."""
    n = len(adj)
    degree = [len(a) for a in adj]
    removed = [False] * n
    order, d = [], 0
    for _ in range(n):
        v = min((x for x in range(n) if not removed[x]), key=lambda x: (degree[x], x))
        d = max(d, degree[v])
        removed[v] = True
        order.append(v)
        for w in adj[v]:
            if not removed[w]:
                degree[w] -= 1
    return order, d


def outer_split(v, position, adj):
    """Wurzelmengen der Degeneracy-Variante für den Knoten v: P = Nachbarn, die in der Ordnung später kommen, X = Nachbarn, die früher kamen."""
    P = {w for w in adj[v] if position[w] > position[v]}
    X = {w for w in adj[v] if position[w] < position[v]}
    return P, X


# --- Komposition -----------------------------------------------------------------------------------------------------------------------------

def bron_kerbosch(adj, variant="pivot", budget=None, trace_limit=0):
    """Alle maximalen Cliquen von `adj` mit der gewählten Variante ("naive", "pivot", "degeneracy").

    `budget`: höchste Zahl von Aufrufen; danach bricht der Lauf ab (`aborted=True`, bis dahin gefundene Cliquen bleiben erhalten).
    `trace_limit`: so viele Aufrufe werden für die Schritt-Ansicht protokolliert (0 = keine)."""
    if variant not in C.VARIANTS:
        raise ValueError(f"unbekannte Variante: {variant}")
    n = len(adj)
    _, d = degeneracy_order(adj)
    res = Result(variant, [], 0, 0, d)
    if n == 0:
        return res
    use_pivot = variant != "naive"

    def expand(R, P, X, depth):
        res.calls += 1
        if budget is not None and res.calls > budget:
            raise BudgetExceeded
        pivot = None
        if use_pivot and (P or X):
            res.select_cost += pivot_select_cost(P, X, adj)
            pivot = choose_pivot_tomita(P, X, adj)
        found = is_maximal(P, X)
        branch = () if found else tuple(split_candidates(P, adj, pivot if use_pivot else None))
        if trace_limit:
            if len(res.trace) < trace_limit:
                res.trace.append(Frame(depth, tuple(R), tuple(sorted(P)), tuple(sorted(X)), pivot, branch, found))
            else:
                res.trace_truncated = True
        if found:
            res.cliques.append(tuple(sorted(R)))
            return
        for v in branch:
            child_P, child_X = child_sets(P, X, v, adj)
            expand(R + [v], child_P, child_X, depth + 1)
            P = P - {v}
            X = X | {v}

    try:
        if variant == "degeneracy":
            order, _ = degeneracy_order(adj)
            position = {v: i for i, v in enumerate(order)}
            for v in order:
                P, X = outer_split(v, position, adj)
                expand([v], P, X, 0)
        else:
            expand([], set(range(n)), set(), 0)
    except BudgetExceeded:
        res.aborted = True
    return res


# --- Referenz und Hilfen für Gegenproben -----------------------------------------------------------------------------------------------------

def brute_force_maximal_cliques(adj):
    """Alle maximalen Cliquen durch Aufzählen aller Teilmengen (nur für n <= 16; unabhängige Referenz)."""
    n = len(adj)
    nbr = [sum(1 << w for w in adj[v]) for v in range(n)]
    is_clique = {0: True}
    out = []
    for mask in range(1, 1 << n):
        low = mask & -mask
        v = low.bit_length() - 1
        rest = mask ^ low
        is_clique[mask] = is_clique[rest] and (rest & ~nbr[v]) == 0
    for mask, ok in is_clique.items():
        if not ok or mask == 0:
            continue
        common = (1 << n) - 1
        for v in range(n):
            if mask >> v & 1:
                common &= nbr[v]
        if common == 0:                 # kein Knoten außerhalb ist mit allen verträglich
            out.append(tuple(v for v in range(n) if mask >> v & 1))
    return sorted(out)


def brute_force_maximal_independent_sets(adj):
    """Alle maximalen unabhängigen Mengen durch Aufzählen aller Teilmengen (nur für n <= 16): unabhängig von jeder Komplement-Konstruktion."""
    n = len(adj)
    nbr = [sum(1 << w for w in adj[v]) for v in range(n)]
    out = []
    for mask in range(1, 1 << n):
        indep = all((mask & nbr[v]) == 0 for v in range(n) if mask >> v & 1)
        if not indep:
            continue
        closed = mask
        for v in range(n):
            if mask >> v & 1:
                closed |= nbr[v]
        if closed == (1 << n) - 1:      # jeder Knoten ist in der Menge oder hat einen Nachbarn darin: nicht erweiterbar
            out.append(tuple(v for v in range(n) if mask >> v & 1))
    return sorted(out)
