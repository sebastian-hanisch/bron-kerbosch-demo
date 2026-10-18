"""Bron–Kerbosch: alle maximalen Cliquen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Wurzel der Härte-und-Struktur-Reihe: ein Verfahren (Bron–Kerbosch, 1973) an einer wachsenden Instanz, dem Verträglichkeitsgraphen einer Sammelladung.

Lauffähig mit: streamlit run app.py
"""

import time

import pandas as pd
import streamlit as st

import bkr_constants as C
import bkr_evaluation as ev
from bkr_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from bkr_visualization import (
    build_degeneracy_figure,
    build_graph_figure,
    build_moon_moser_figure,
    build_size_figure,
    build_sweep_figure,
)

st.set_page_config(page_title="Bron–Kerbosch – Sebastian Hanisch", layout="wide")


def _i(x):
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _f(x, digits=1):
    """Dezimalzahl mit Komma."""
    return f"{x:.{digits}f}".replace(".", ",")


def _s(x, digits=1):
    """Dezimalzahl mit Komma und ausdrücklichem Vorzeichen."""
    return f"{x:+.{digits}f}".replace(".", ",")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _density_sweep(graph_type):
    return ev.density_sweep(graph_type)


@st.cache_data(show_spinner=False)
def _moon_moser():
    return ev.moon_moser_rows()


@st.cache_data(show_spinner=False)
def _structures():
    return ev.structure_rows()


@st.cache_data(show_spinner=False)
def _complement(settings):
    return ev.complement_check(settings)


st.title("🧩 Bron–Kerbosch: alle maximalen Cliquen")
st.markdown(
    """
Eine Sammelladung ist ein **Graph**: Sendungen sind Knoten, eine Kante heißt „dürfen zusammen verladen werden“. Eine **maximale Clique** ist eine **Fuhre**, der man keine weitere Sendung mehr hinzufügen kann. Der **Bron–Kerbosch-Algorithmus** (1973) zählt alle diese Fuhren auf, ohne eine zu übersehen und ohne eine zweimal zu melden.

Das ist das erste Stück der **Härte-und-Struktur-Reihe**: Cliquen, unabhängige Mengen und Überdeckungen sind auf allgemeinen Graphen schwer, auf Graphen mit Struktur leicht. Hier die Wurzel: das Aufzählen. Anders als die Fall-Demos zeigt diese Demo ein Verfahren an einem wachsenden Beispiel. Weiter unten: die vier Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Bron–Kerbosch", expanded=True):
    st.markdown(
        """
Der Algorithmus baut Fuhren Sendung für Sendung auf und führt dabei drei Mengen mit: **R** (die bisher gewählten Sendungen, immer paarweise verträglich), **P** (Sendungen, die R noch erweitern könnten) und **X** (Sendungen, die R erweitern würden, deren Fuhren aber schon gemeldet wurden).

1. **Wähle** eine Sendung *v* aus P und rufe dich mit *R + v* auf; in P und X bleiben dabei nur die Sendungen, die mit *v* verträglich sind.
2. **Melde R**, wenn P und X beide leer sind: Dann kann niemand mehr dazu (P leer) und keine Fuhre wurde verdoppelt (X leer).
3. **Verschiebe v** nach dem Aufruf von P nach X: Alle Fuhren, die *v* enthalten, sind gemeldet.

**Warum das funktioniert:** Jede maximale Clique entsteht auf genau einem Weg durch diese Aufrufe. Wie viele Aufrufe es sind, hängt aber stark davon ab, **auf welchen Sendungen verzweigt wird**; darum die drei Varianten:

| Variante | Verzweigt auf | Idee |
|---|---|---|
| **ohne Pivot** | allen Sendungen aus P | die Grundform von 1973 |
| **Tomita-Pivot** | nur P ohne die Nachbarn eines Pivots *u* | Jede maximale Clique enthält *u* oder einen Nicht-Nachbarn von *u*; als *u* dient die Sendung mit den meisten Nachbarn in P |
| **Degeneracy-Ordnung** | die Wurzel nimmt die Sendungen einzeln in einer Reihenfolge, die immer die mit dem wenigsten Restnachbarn zuerst entfernt | In der Wurzel enthält P höchstens *d* Sendungen (die Degeneracy des Graphen); darunter wieder der Pivot |
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Graph**")
    graph_type = st.selectbox("Regelart", list(C.GRAPH_TYPES), format_func=C.GRAPH_TYPES.get, key="type_select",
                              help="Zufallsregeln: jedes Paar unabhängig verträglich. Zeitfenster: verträglich, wenn die Fenster überlappen. Klassenregeln: sechs Klassen, ein Klassenpaar ist verträglich oder nicht.")
    n = st.slider("Sendungen n", *bounds("n_slider"), key="n_slider", help="Knotenzahl des Graphen.")
    density = st.slider("Anteil verträglicher Paare (%)", *bounds("density_slider"), key="density_slider",
                        help="Zufallsregeln: Wahrscheinlichkeit je Paar. Zeitfenster: die Fensterlänge wird so gewählt, dass zwei Fenster mit dieser Wahrscheinlichkeit überlappen. Klassenregeln: Wahrscheinlichkeit je Klassenpaar.")
    seed = st.number_input("Zufalls-Seed des Graphen", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Graphen erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Verfahren**")
    variant = st.radio("Variante in der Schritt-Ansicht", list(C.VARIANTS), format_func=C.VARIANTS.get, key="variant_radio",
                       help="Welche Variante die Schritt-Ansicht zeigt. Die Kennzahlen darunter vergleichen immer alle drei.")
    st.markdown("**Anzeige**")
    view = st.radio("Der Graph als", list(C.VIEWS), format_func=C.VIEWS.get, key="view_radio",
                    help="Derselbe Graph oder sein Komplement. Eine Fuhre ist im Verträglichkeitsgraphen eine Clique, im Konfliktgraphen eine unabhängige Menge.")

sync_query_params({"type_select": graph_type, "n_slider": int(n), "density_slider": int(density), "seed_input": int(seed), "variant_radio": variant, "view_radio": view})

settings = ev.Settings(graph_type=graph_type, n=int(n), density=int(density), seed=int(seed), variant=variant, view=view)
with st.spinner("Rechne..."):
    a = _analysis(settings)
g, res = a.graph, a.result
noun = "Clique" if view == "compat" else "unabhängige Menge"

# --- Die Fuhren ----------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Die Fuhren: Schritt für Schritt")
n_cliques = len(a.cliques)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Maximale Fuhren", _i(n_cliques) if a.complete else "unbekannt", help="Zahl der maximalen Cliquen des Verträglichkeitsgraphen = der maximalen unabhängigen Mengen des Konfliktgraphen.")
calls_txt = (">" if res.aborted else "") + _i(res.calls)
pivot_calls = a.runs["pivot"].calls
m2.metric(f"Aufrufe ({C.VARIANTS[variant]})", calls_txt, delta=(f"Faktor {_f(res.calls / pivot_calls, 1)} gegenüber dem Pivot" if variant != "pivot" and pivot_calls else "Referenz"), delta_color="off",
          help="Aufrufe von expand(R, P, X). Ein Aufruf ist ein Elementarschritt, keine Laufzeit.")
m3.metric("Kosten der Pivot-Auswahl", _i(a.runs[variant].select_cost) if variant != "naive" else "–", help="Elementarschritte, um den Pivot zu wählen: je Kandidat der Schnitt mit P, gezählt mit min(|P|, Grad).")
m4.metric("Degeneracy d", _i(res.degeneracy), help="Wie dünn der Graph im schlimmsten Teil ist: Entfernt man immer den Knoten mit dem wenigsten Restnachbarn, ist der größte Restgrad d.")
if res.aborted:
    st.warning(f"Die Variante „{C.VARIANTS[variant]}“ ist nach {_i(C.CALL_BUDGET)} Aufrufen abgebrochen (Rechengrenze der Demo). Die Schritt-Ansicht zeigt nur die ersten Aufrufe; die Fuhren stammen aus einer Variante, die fertig wurde.")

trace = res.trace
n_frames = len(trace)
owner = (settings.graph_type, settings.n, settings.density, settings.seed, settings.variant)
if st.session_state.get("step_owner") != owner:
    st.session_state["bkr_step"] = 0
    st.session_state["step_owner"] = owner
if n_frames > 1:
    st.session_state["bkr_step"] = min(int(st.session_state.get("bkr_step", 0)), n_frames - 1)
step_col, play_col = st.columns([5, 2])
with step_col:
    if n_frames > 1:
        step = st.slider("Aufruf", 0, n_frames - 1, key="bkr_step", help="Welchen Aufruf von expand(R, P, X) die Ansicht zeigt, in der Reihenfolge der Rekursion (Tiefensuche).")
    else:
        step = 0
        st.caption("Dieser Graph braucht nur einen Aufruf.")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch", disabled=n_frames <= 1)
view_slot = st.empty()


def _describe(k):
    f = trace[k]
    names = lambda items: "{" + ", ".join(str(v + 1) for v in items) + "}" if items else "∅"  # noqa: E731
    parts = [f"**Aufruf {k + 1} von {_i(res.calls) if not res.aborted else _i(len(trace))}** (Tiefe {f.depth}): R = {names(f.R)}, P = {names(f.P)}, X = {names(f.X)}."]
    if f.found:
        parts.append(f"**P und X sind leer: R ist eine maximale Fuhre** ({len(f.R)} Sendungen) und wird gemeldet.")
    elif f.pivot is not None:
        skipped = len(f.P) - len(f.branch)
        parts.append(f"Pivot: Sendung {f.pivot + 1}. Verzweigt wird auf {names(f.branch)}; {skipped} Kandidaten aus P sind Nachbarn des Pivots und entfallen hier.")
    elif f.branch:
        parts.append(f"Verzweigt wird auf allen Kandidaten aus P: {names(f.branch)}.")
    else:
        parts.append("Kein Kandidat in P, aber X ist nicht leer: Diese Auswahl wäre eine Fuhre, die schon gemeldet wurde, also Sackgasse.")
    return " ".join(parts)


def _render(k):
    with view_slot.container():
        fig = build_graph_figure(g, view, frame=trace[k])
        st.plotly_chart(fig, width="stretch", key=f"graph_{k}")
        st.markdown(_describe(k))


if auto_play:
    for k in range(n_frames):
        _render(k)
        time.sleep(min(0.6, 12.0 / max(n_frames, 1)))
else:
    _render(step)
if res.trace_truncated:
    st.caption(f"Die Schritt-Ansicht zeigt die ersten {_i(C.TRACE_LIMIT)} Aufrufe; die Zahlen oben gelten für den ganzen Lauf.")
st.caption("Grün: R. Blau: P. Grau: X. Gold umrandet: der Pivot. Rot: eine gefundene maximale Fuhre. "
           + ("Im Konfliktgraphen steht eine Kante für „darf nicht zusammen“; eine Fuhre ist dort eine Menge ohne Kante untereinander." if view == "conflict" else "Im Verträglichkeitsgraphen steht eine Kante für „darf zusammen“; eine Fuhre ist eine Menge, in der alle Paare verbunden sind."))

if a.complete and a.cliques:
    with st.expander(f"Alle {_i(n_cliques)} maximalen Fuhren ({noun}n)"):
        sizes = ev.clique_sizes(a.cliques)
        st.plotly_chart(build_size_figure(sizes), width="stretch", key="size_chart")
        shown = a.cliques[:200]
        st.dataframe(pd.DataFrame({"Größe": [len(c) for c in shown], "Sendungen": [", ".join(str(v + 1) for v in c) for c in shown]}), hide_index=True, width="stretch")
        if n_cliques > len(shown):
            st.caption(f"Die ersten {len(shown)} von {_i(n_cliques)}, lexikografisch sortiert.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel Arbeit spart der Pivot bei genau diesem Graphen?")
naive, piv, deg = a.runs["naive"], a.runs["pivot"], a.runs["degeneracy"]
if naive.aborted:
    st.success(f"Ohne Pivot bricht der Lauf nach {_i(C.CALL_BUDGET)} Aufrufen ab, mit dem Pivot sind es **{_i(piv.calls)}**: mindestens **Faktor {_i(C.CALL_BUDGET // max(piv.calls, 1))}** weniger Aufrufe.")
else:
    factor = ev.saving_factor(naive.calls, piv.calls)
    if factor >= 10:
        st.success(f"Ohne Pivot **{_i(naive.calls)}** Aufrufe, mit dem Pivot **{_i(piv.calls)}**: **Faktor {_f(factor, 1)}** weniger. Hier sucht der Grundalgorithmus fast nur Sackgassen.")
    elif factor >= 1.5:
        st.info(f"Ohne Pivot {_i(naive.calls)} Aufrufe, mit dem Pivot {_i(piv.calls)}: Faktor {_f(factor, 1)} weniger. Der Pivot hilft spürbar, aber nicht dramatisch.")
    else:
        st.warning(f"Ohne Pivot {_i(naive.calls)} Aufrufe, mit dem Pivot {_i(piv.calls)}: nur Faktor {_f(factor, 2)} weniger. In diesem dünnen Graphen gibt es kaum Sackgassen, die der Pivot ersparen könnte.")
dc = 100.0 * (deg.calls / piv.calls - 1.0) if piv.calls else 0.0
ds = 100.0 * (deg.select_cost / piv.select_cost - 1.0) if piv.select_cost else 0.0
st.caption(f"Die Degeneracy-Außenschleife braucht {_i(deg.calls)} Aufrufe ({_s(dc, 1)} % gegenüber dem Pivot global) und {_i(deg.select_cost)} Elementarschritte für die Pivot-Auswahl ({_s(ds, 1)} % gegenüber {_i(piv.select_cost)}).")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Wie viel spart der Pivot — und wann?")
st.caption(f"Median über {len(C.SWEEP_SEEDS)} feste Graphen mit n = {C.SWEEP_N} Sendungen und der Regelart „{C.GRAPH_TYPES[graph_type]}“ aus der Seitenleiste (n und Seed der Seitenleiste gelten hier nicht); jeder Lauf ist auf {_i(C.SWEEP_BUDGET)} Aufrufe begrenzt, offene Quadrate markieren Mediane, bei denen mindestens ein Lauf diese Grenze erreicht hat.")
with st.spinner(f"Rechne den Sweep (bis zu {len(C.SWEEP_DENSITIES) * len(C.SWEEP_SEEDS) * 3} Läufe)..."):
    sweep = _density_sweep(graph_type)
st.plotly_chart(build_sweep_figure(sweep), width="stretch", key="sweep_chart")
vd = ev.sweep_verdict(sweep)
cut = "mindestens " if vd["any_aborted"] else ""
st.info(
    f"Bei {vd['worst_density']} % verträglichen Paaren spart der Pivot am wenigsten: Faktor {_f(vd['worst_factor'], 1)} weniger Aufrufe. "
    f"Bei {vd['best_density']} % am meisten: {cut}Faktor {_f(vd['best_factor'], 0)} weniger. Je dichter und je strukturierter der Graph, desto mehr Sackgassen ersetzt der Pivot durch einen einzigen Schritt."
)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Der schlimmste Fall (Moon–Moser)")
st.caption("Ein Graph aus k Dreiergruppen, in dem Sendungen aus verschiedenen Gruppen immer verträglich sind und innerhalb einer Gruppe nie: Man wählt aus jeder Gruppe genau eine Sendung, also gibt es 3^k maximale Fuhren, und mehr kann kein Graph mit 3k Knoten haben.")
mm = _moon_moser()
st.plotly_chart(build_moon_moser_figure(mm), width="stretch", key="moon_chart")
exact = all(r["calls"]["naive"] == r["formula_naive"] and r["calls"]["pivot"] == r["formula_pivot"] and r["cliques"] == r["bound"] for r in mm)
last = mm[-1]
if exact:
    st.success(f"Für k = {mm[0]['k']} bis {last['k']} stimmt jede Messung exakt: **3^k** Fuhren, **4^k** Aufrufe ohne Pivot, **(3^(k+1) − 1)/2** mit Pivot. Bei k = {last['k']} ({last['n']} Sendungen): {_i(last['cliques'])} Fuhren, {_i(last['calls']['naive'])} Aufrufe ohne und {_i(last['calls']['pivot'])} mit Pivot.")
else:
    st.warning("Die gemessenen Aufrufe weichen von den Formeln ab (nur für diese k geprüft); die Tabelle unten zeigt die Messung.")
st.caption("Auch der Pivot kann die Zahl der Fuhren nicht senken: Er sorgt nur dafür, dass der Aufwand proportional zur Zahl der Fuhren bleibt (hier: Aufrufe ≈ 1,5-mal so viele wie Fuhren), statt ein Vielfaches davon zu betragen.")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Wann lohnt die Degeneracy-Ordnung?")
st.caption("Median über 3 feste Graphen je Struktur. Verglichen wird der Pivot im ganzen Graphen mit der Degeneracy-Außenschleife (Eppstein, Löffler und Strash 2010): Aufrufe und Kosten der Pivot-Auswahl.")
with st.spinner("Rechne die Strukturen..."):
    rows3 = _structures()
st.plotly_chart(build_degeneracy_figure(rows3), width="stretch", key="degeneracy_chart")
cheaper = [r for r in rows3 if ev.select_cost_change(r) < 0]
dearer = [r for r in rows3 if ev.select_cost_change(r) > 0]
fewer_calls = [r for r in rows3 if ev.calls_change(r) < 0]
best = min(rows3, key=ev.select_cost_change)
worst = max(rows3, key=ev.select_cost_change)
st.info(
    f"Die Degeneracy-Außenschleife macht die Pivot-Auswahl in {len(cheaper)} von {len(rows3)} Strukturen billiger (am meisten bei „{best['name']}“: {_s(ev.select_cost_change(best), 0)} %) "
    f"und in {len(dearer)} teurer (am meisten bei „{worst['name']}“: +{_f(ev.select_cost_change(worst), 0)} %). "
    + (f"Die Zahl der Aufrufe senkt sie nur in {len(fewer_calls)} von {len(rows3)} Strukturen, und dort um höchstens {_f(abs(min(ev.calls_change(r) for r in fewer_calls)), 1)} %: " if fewer_calls
       else "Die Zahl der Aufrufe senkt sie in keiner Struktur: ")
    + "Ihr Vorteil ist nicht, weniger Aufrufe zu machen, sondern in jedem Aufruf nur noch wenige Kandidaten prüfen zu müssen, und das zahlt sich erst bei großen, dünnen Graphen aus."
)
table3 = pd.DataFrame({
    "Struktur": [r["name"] for r in rows3], "Fuhren": [r["cliques"] for r in rows3], "Degeneracy d": [r["degeneracy"] for r in rows3],
    "Aufrufe ohne Pivot": [(">" if r["aborted"] else "") + _i(r["calls"]["naive"]) for r in rows3],
    "Aufrufe Pivot": [r["calls"]["pivot"] for r in rows3], "Aufrufe Degeneracy": [r["calls"]["degeneracy"] for r in rows3],
    "Auswahlkosten Pivot": [r["select"]["pivot"] for r in rows3], "Auswahlkosten Degeneracy": [r["select"]["degeneracy"] for r in rows3],
})
with st.expander("Tabelle zu Experiment 3"):
    st.dataframe(table3, hide_index=True, width="stretch")
    st.caption("„>“: mindestens ein Lauf ohne Pivot hat die Grenze von " + _i(C.SWEEP_BUDGET * 4) + " Aufrufen erreicht; der Median ist dann nur eine Untergrenze.")

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Cliquen sind unabhängige Mengen des Komplements")
cc = _complement(settings)
st.caption(f"Ein kleiner Graph mit n = {cc['n']} Sendungen (Regelart, Anteil und Seed aus der Seitenleiste). Links Bron–Kerbosch auf dem Verträglichkeitsgraphen, rechts ein Brute-Force-Aufzählen aller Teilmengen im Konfliktgraphen; es kommt kein Bron–Kerbosch vor.")
c1, c2 = st.columns(2)
c1.metric("Maximale Cliquen (Bron–Kerbosch)", cc["cliques"])
c2.metric("Maximale unabhängige Mengen des Konfliktgraphen (Brute Force)", cc["independent"])
if cc["equal"] and cc["equal_back"]:
    st.success(f"Es sind **dieselben {cc['cliques']} Mengen**. Umgekehrt sind die {cc['conflict_cliques']} maximalen Cliquen des Konfliktgraphen genau die maximalen unabhängigen Mengen des Verträglichkeitsgraphen. Ein Verfahren für Cliquen löst also auch „größte konfliktfreie Auswahl“, und umgekehrt.")
else:
    st.error("Die beiden Mengen sind nicht gleich: Das darf nicht passieren, bitte melden.")
st.caption("Genau diese Brücke nutzt die Reihe weiter: Eine Knotenüberdeckung ist das Komplement einer unabhängigen Menge (Stück 3), und eine Färbung des Konfliktgraphen zerlegt die Sendungen in konfliktfreie Fahrzeugladungen (graph-coloring-demo).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Alle Fuhren sind gesucht** | Gebraucht wird oft nur die **größte** Fuhre. Aufzählen kostet dann so viel wie die Zahl aller maximalen Cliquen, und die wächst bis 3^(n/3). | Stück 2: größte Clique mit Schranken |
| **Aufrufe zählen** | Aufrufe und Auswahlkosten sind Elementarschritte, keine Laufzeit. Reale Implementierungen nutzen Bitmengen oder Adjazenzlisten, und die Kosten je Aufruf unterscheiden sich. | – |
| **Kleine Graphen** | Bis n = 40 zeigt die Demo, wie die Varianten sich verhalten, nicht, was auf Graphen mit Millionen Kanten passiert; dort macht die Degeneracy-Außenschleife den Unterschied. | – |
| **Nur paarweise Regeln** | Ein Graph kann nur „A und B nie zusammen“ ausdrücken. Regeln wie „A, B und C nie alle drei, aber je zwei sind erlaubt“ brauchen einen Hypergraphen. | – |
| **Synthetische Graphen** | Die Graphen sind erzeugt, keine echten Sendungsdaten. Die Muster (dicht gegen dünn, strukturiert gegen zufällig) gelten für die Graphklassen, nicht für ein bestimmtes Lager. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben ein ungerichteter Graph $G = (V, E)$ mit $n = |V|$. Eine **Clique** ist eine Knotenmenge $C \subseteq V$, in der je zwei Knoten durch eine Kante verbunden sind. Sie ist **maximal**, wenn jeder Knoten außerhalb von $C$ mindestens einen Knoten in $C$ nicht als Nachbarn hat. Gesucht sind alle maximalen Cliquen.

**Rekursion.** $\mathrm{BK}(R, P, X)$ mit $R$ = Clique im Aufbau, $P$ = Knoten, die zu allen Knoten in $R$ verträglich sind und $R$ erweitern dürfen, $X$ = Knoten, die ebenso verträglich sind, aber schon abgearbeitet wurden. Aufruf zu Beginn: $\mathrm{BK}(\emptyset, V, \emptyset)$.

Meldung:

$$P = \emptyset \ \text{und}\ X = \emptyset \ \Longrightarrow\ R \ \text{ist eine maximale Clique}$$

Verzweigung über eine Kandidatenmenge $B$ ($B = P$ ohne Pivot):

$$\mathrm{BK}(R \cup \{v\},\ P \cap N(v),\ X \cap N(v)) \quad \text{für } v \in B,\ \text{danach } P \leftarrow P \setminus \{v\},\ X \leftarrow X \cup \{v\}$$

**Pivot.** Wähle $u \in P \cup X$ mit den meisten Nachbarn in $P$ und setze $B = P \setminus N(u)$:

$$u = \arg\max_{w \in P \cup X} \ |P \cap N(w)|$$

Das ist erlaubt, weil jede maximale Clique, die $R$ enthält, entweder $u$ selbst oder einen Nicht-Nachbarn von $u$ enthält (sonst ließe sie sich um $u$ erweitern). Tomita, Tanaka und Takahashi (2006) zeigen, dass diese Wahl die Laufzeit im schlimmsten Fall auf

$$O\!\left(3^{n/3}\right)$$

begrenzt. Das ist optimal, weil ein Graph höchstens

$$3^{n/3} \ \text{maximale Cliquen hat (Moon und Moser 1965, } n \text{ durch 3 teilbar)}$$

und der Graph mit $k$ Dreiergruppen diese Zahl erreicht.

**Degeneracy.** Entfernt man wiederholt einen Knoten mit minimalem Restgrad, ist die **Degeneracy** $d$ der größte dabei auftretende Restgrad. In der Wurzel besteht $P$ für jeden Knoten $v$ nur aus seinen späteren Nachbarn, also $|P| \le d$. Eppstein, Löffler und Strash (2010) erhalten so

$$O\!\left(d\, n\, 3^{d/3}\right)$$

und gewinnen auf Graphen mit kleinem $d$ und großem $n$.

**Gemessene Formeln (Moon–Moser-Graph mit $k$ Dreiergruppen, $n = 3k$).** Ohne Pivot und mit Pivot wurden für $k = 1, \dots, 7$ genau diese Aufrufzahlen gemessen (Experiment 2):

$$\#\text{Aufrufe ohne Pivot} = 4^k$$

$$\#\text{Aufrufe mit Pivot} = \frac{3^{k+1} - 1}{2}$$

Das sind Messungen für die getesteten $k$, kein hier geführter Beweis.

**Annahmen.**

| Annahme | Inhalt | Wer setzt an |
|---|---|---|
| Paarweise Verträglichkeit | Eine Fuhre ist genau dann zulässig, wenn alle Paare verträglich sind | Hypergraph (nicht in der Reihe) |
| Alle Fuhren | Gesucht sind alle maximalen, nicht die größte | Stück 2 |
| Aufrufe als Aufwand | Elementarschritte statt Laufzeit | – |

**Literatur.**
- Bron, C., & Kerbosch, J. (1973). *Algorithm 457: finding all cliques of an undirected graph.* Communications of the ACM 16(9), 575–577.
- Moon, J. W., & Moser, L. (1965). *On cliques in graphs.* Israel Journal of Mathematics 3, 23–28.
- Tomita, E., Tanaka, A., & Takahashi, H. (2006). *The worst-case time complexity for generating all maximal cliques and computational experiments.* Theoretical Computer Science 363(1), 28–42.
- Eppstein, D., Löffler, M., & Strash, D. (2010). *Listing all maximal cliques in sparse graphs in near-optimal time.* ISAAC 2010, LNCS 6506, 403–414.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
