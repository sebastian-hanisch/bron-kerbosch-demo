"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 40, 14
DENSITY_MIN, DENSITY_MAX, DEFAULT_DENSITY = 5, 95, 50   # Anteil verträglicher Paare in Prozent
SEED_MAX, DEFAULT_SEED = 999999, 35
SWEEP_SEEDS = tuple(range(100000, 100005))              # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund

# Graphtypen der Hauptansicht (alle nehmen dieselbe Dichte-Angabe: Anteil verträglicher Paare)
GRAPH_TYPES = {
    "random": "Zufallsregeln",
    "windows": "Zeitfenster",
    "classes": "Klassenregeln",
}
DEFAULT_TYPE = "random"
N_CLASSES = 6                                           # Zahl der Sendungsklassen bei den Klassenregeln

# Verfahren
VARIANTS = {
    "naive": "ohne Pivot",
    "pivot": "Tomita-Pivot",
    "degeneracy": "Degeneracy-Ordnung",
}
DEFAULT_VARIANT = "pivot"

# Anzeige: dieselbe Instanz als Verträglichkeits- oder Konfliktgraph
VIEWS = {"compat": "Verträglichkeit (Kante = darf zusammen)", "conflict": "Konflikt (Kante = darf nicht zusammen)"}
DEFAULT_VIEW = "compat"

# Rechengrenzen: ein Aufruf ist ein Aufruf von expand(R, P, X). Wird das Budget überschritten, bricht der Lauf ab und meldet es.
CALL_BUDGET = 200_000        # Hauptansicht, je Verfahren
SWEEP_BUDGET = 60_000        # Sweeps und Vergleichstabellen, je Lauf
TRACE_LIMIT = 400            # so viele Aufrufe zeigt die Schritt-Ansicht höchstens
SWEEP_N = 20                 # feste Knotenzahl der Dichte-Sweeps (unabhängig vom Regler n)
SWEEP_DENSITIES = (10, 20, 30, 40, 50, 60, 70, 80, 90)
MOON_MOSER_KS = (1, 2, 3, 4, 5, 6, 7)
CHECK_N = 14                 # Knotenzahl der Komplement-Gegenprobe (Brute Force über alle Teilmengen)

# Farben
COLOR_R = "#2F6B65"          # bereits gewählte Sendungen (R)
COLOR_P = "#4c78a8"          # noch mögliche Kandidaten (P)
COLOR_X = "#8c8c8c"          # ausgeschlossen, schon abgearbeitet (X)
COLOR_PIVOT = "#e0a030"      # Pivot
COLOR_IDLE = "#d9d9d9"       # nicht beteiligt
COLOR_EDGE = "rgba(150,150,150,0.35)"
COLOR_FOUND = "#c0504d"      # gefundene maximale Clique
COLOR_LINE = {"naive": "#c0504d", "pivot": "#2F6B65", "degeneracy": "#4c78a8"}

PRESETS = {
    "Standardfall (14 Sendungen)": {"type": DEFAULT_TYPE, "n": DEFAULT_N, "density": DEFAULT_DENSITY, "seed": DEFAULT_SEED, "variant": DEFAULT_VARIANT, "view": DEFAULT_VIEW},
    "Lehrbeispiel (klein)": {"type": "random", "n": 8, "density": 50, "seed": 7, "variant": "pivot", "view": "compat"},
    "Dicht: der Pivot rettet": {"type": "random", "n": 20, "density": 85, "seed": DEFAULT_SEED, "variant": "naive", "view": "compat"},
    "Dünn: der Pivot egal": {"type": "random", "n": 30, "density": 10, "seed": DEFAULT_SEED, "variant": "pivot", "view": "compat"},
    "Zeitfenster": {"type": "windows", "n": 24, "density": 30, "seed": DEFAULT_SEED, "variant": "pivot", "view": "compat"},
    "Klassenregeln": {"type": "classes", "n": 24, "density": 50, "seed": DEFAULT_SEED, "variant": "pivot", "view": "conflict"},
}
PRESET_HELP = {
    "Standardfall (14 Sendungen)": "Die Voreinstellung: 14 Sendungen, jedes zweite Paar verträglich, Tomita-Pivot. Alle Kennzahlen der README zum Standardfall gelten hier.",
    "Lehrbeispiel (klein)": "8 Sendungen, jedes zweite Paar verträglich: wenige Schritte, gut zum Durchklicken.",
    "Dicht: der Pivot rettet": "20 Sendungen, 85 % der Paare verträglich, aber ohne Pivot: so viele Aufrufe wie nie nötig. Mit dem Pivot-Umschalter vergleichen.",
    "Dünn: der Pivot egal": "30 Sendungen, nur jedes zehnte Paar verträglich: der Pivot spart kaum etwas.",
    "Zeitfenster": "Verträglich heißt: Die Zeitfenster überlappen (ein Intervallgraph). Jede maximale Clique ist die Menge der Fenster, die zu einem Zeitpunkt zugleich offen sind.",
    "Klassenregeln": "Sechs Sendungsklassen, verträglich ist ein Klassenpaar oder nicht. Konfliktansicht: die Fuhren sind die maximalen unabhängigen Mengen.",
}
