# Bron–Kerbosch: alle maximalen Cliquen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-bron-kerbosch-demo.streamlit.app/)** -->

Erstes Stück der **Härte-und-Struktur-Reihe** der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, ihre **Wurzel**. Die Reihe fragt, welche Struktur ein auf Graphen schweres Problem leicht macht (Cliquen, unabhängige Mengen, Überdeckungen, Baumweite). Dieses Stück beginnt mit dem Aufzählen: **alle maximalen Cliquen** eines Graphen, mit dem Algorithmus von Bron und Kerbosch (1973) in drei Varianten (ohne Pivot, Tomita-Pivot, Degeneracy-Ordnung). Anders als die Fall-Demos zeigt die Demo ein Verfahren an einem wachsenden Beispiel: dem **Verträglichkeitsgraphen einer Sammelladung** (Sendungen als Knoten, eine Kante heißt „dürfen zusammen verladen werden“; eine maximale Clique ist eine Fuhre, der man keine Sendung mehr hinzufügen kann).

```
Bron–Kerbosch: alle maximalen Cliquen (Wurzel)                          [DIESES STÜCK]
 ├─ Größte Clique: Färbungsschranke und Kernzahl
 ├─ Knotenüberdeckung: Approximation, Kernbildung, Verzweigen
 ├─ Chordale und perfekte Graphen
 │    └─ Baumweite ─ Dynamische Programmierung auf der Baumzerlegung
 ├─ Kantenclique-Überdeckung und Kernbildung
 └─ Unabhängige Menge im großen Maßstab: Reduktionen und Lokalsuche
```

## Warum dieses Problem

Wer eine Sammelladung plant, fragt zuerst, welche Sendungen sich überhaupt zusammen verladen lassen. Ist „verträglich“ eine Eigenschaft von Paaren, ist jede zulässige Fuhre eine **Clique** im Verträglichkeitsgraphen, und die Fuhren, die sich nicht mehr erweitern lassen, sind die **maximalen Cliquen**. Ihre Zahl kann bei n Sendungen bis 3^(n/3) betragen. Die Kernfrage der Demo: **Wie viel Arbeit kostet das Aufzählen, und was spart der Pivot dabei?** Der Pivot ersetzt Verzweigungen, die nur in Sackgassen führen, durch einen einzigen Schritt, aber wie viel er spart, hängt stark vom Graphen ab.

Abgrenzung: `graph-coloring-demo` nutzt die größte Clique nur als untere Schranke für die Färbung (Branch-and-Bound ohne Aufzählung, ohne Pivot); dieses Stück zählt dagegen alle maximalen Cliquen auf. Auch `constraint-programming-demo` kennt Paarunverträglichkeiten, aber als Nebenbedingung neben einer Kapazität, nicht als Graphthema.

## Modell

Ungerichteter Graph G = (V, E); Kante = zwei Sendungen dürfen zusammen verladen werden. Der **Konfliktgraph** ist das Komplement. Eine Fuhre ist im Verträglichkeitsgraphen eine Clique, im Konfliktgraphen eine unabhängige Menge: **maximale Cliquen von G = maximale unabhängige Mengen des Komplements**, das zeigt Experiment 4 live. Graphtypen: **Zufallsregeln** (jedes Paar unabhängig verträglich), **Zeitfenster** (verträglich, wenn die Fenster überlappen: ein Intervallgraph; die Fensterlänge l wird so gewählt, dass zwei Fenster mit der eingestellten Wahrscheinlichkeit überlappen: 1 − (1 − l)² = d), **Klassenregeln** (sechs Sendungsklassen, ein Klassenpaar ist verträglich oder nicht). Alle Graphen sind synthetisch. Der Zufall kommt aus `random.Random(seed)`; kein Zufall in den Algorithmen. Formeln und Literatur stehen im 📐-Expander der App.

## Methodik

`expand(R, P, X)` baut Cliquen auf: **R** = bisher gewählt, **P** = Kandidaten, **X** = bereits abgearbeitete Knoten; R wird gemeldet, wenn P und X leer sind. Ein **Aufruf** ist ein Aufruf von `expand`; die Demo zählt Aufrufe und **Auswahlkosten** (Elementarschritte der Pivot-Wahl), keine Laufzeit.

| Variante | Verzweigt auf |
|---|---|
| **ohne Pivot** | allen Kandidaten aus P (Grundform von 1973) |
| **Tomita-Pivot** | nur P ohne die Nachbarn des Pivots u, gewählt mit den meisten Nachbarn in P (Tomita, Tanaka, Takahashi 2006) |
| **Degeneracy-Ordnung** | die Wurzel nimmt die Knoten in Degeneracy-Reihenfolge einzeln (P = spätere, X = frühere Nachbarn), darunter wieder der Pivot (Eppstein, Löffler, Strash 2010) |

Die App zeigt die Rekursion Schritt für Schritt (die ersten 400 Aufrufe, Abspielen mit ▶️), vergleicht die drei Varianten live und rechnet vier Experimente.

## Befunde (gemessen, keine Behauptungen)

Jede Zahl steht in `tests/test_claims.py`. Alle Aufruf- und Kostenzahlen sind ganzzahlig und plattformunabhängig exakt. Sweeps sind Mediane über fünf feste Graphen (`SWEEP_SEEDS`), die Strukturtabelle über drei.

| Frage | Befund |
|---|---|
| Standardfall (14 Sendungen, 50 % verträglich, Zufallsregeln, Seed 35)? | 23 maximale Fuhren (19 mit 3, 4 mit 4 Sendungen). Aufrufe: 96 ohne Pivot, 44 mit Pivot, 56 mit Degeneracy-Außenschleife. Auswahlkosten 336 (Pivot) gegen 345 (Degeneracy). |
| Was spart der Pivot bei dichten Graphen? | Preset „Dicht“ (20 Sendungen, 85 %): 104 Fuhren, **20 720 Aufrufe ohne Pivot gegen 255 mit Pivot**, Faktor 81,3. Im Dichte-Sweep (n = 20, Zufallsregeln): Faktor 1,2 bei 10 % verträglichen Paaren (41 gegen 35 Aufrufe), **Faktor 210 bei 90 %** (34 688 gegen 165). |
| Und bei strukturierten Graphen? | Zeitfenster und Klassenregeln bei 90 %: ohne Pivot erreichen mindestens 4 von 5 Läufen die Grenze von 60 000 Aufrufen (der Median ist nur eine Untergrenze), mit Pivot sind es im Median **24** bzw. **25** Aufrufe. Preset „Klassenregeln“ (24 Sendungen, 50 %): 101 696 Aufrufe ohne Pivot, 42 mit. |
| Wann hilft der Pivot kaum? | Dünn: Preset „Dünn“ (30 Sendungen, 10 %): 88 gegen 72 Aufrufe, Faktor 1,2. Auf einem Baum mit 200 Knoten 400 gegen 391, auf dem 15 × 15-Gitter 646 gegen 642. Es gibt kaum Sackgassen, die der Pivot ersparen könnte. |
| Schlimmster Fall (Moon–Moser, k Dreiergruppen, n = 3k)? | Genau **3^k** maximale Cliquen, **4^k** Aufrufe ohne Pivot und **(3^(k+1) − 1)/2** mit Pivot, für alle gemessenen k = 1 bis 7 exakt (k = 7: 2 187 Cliquen, 16 384 gegen 3 280 Aufrufe). Die Formeln sind Messungen für diese k, kein hier geführter Beweis. Aufrufe mit Pivot ≈ 1,5-mal so viele wie Fuhren. |
| Senkt die Degeneracy-Außenschleife die Zahl der Aufrufe? | **Nein, fast nie.** In 7 von 8 Strukturen braucht sie mehr Aufrufe, zwischen 0,5 und 9,8 % (z. B. 7 897 statt 7 364 bei 40 Sendungen mit 80 %); nur bei skalenfreiem n = 1000, m = 8 sind es 0,2 % weniger. Das ist ein Negativbefund gegenüber der Erwartung. |
| Was bringt sie stattdessen? | Die **Pivot-Auswahl wird billiger, aber nur auf großen dünnen Graphen**: Baum n = 200 −55,4 %, Gitter −34,5 %, skalenfrei n = 1000, m = 3 −27,7 %, m = 8 −12,1 %, Zufall dünn n = 300 −26,7 %. Auf dichten Graphen wird sie teurer: Zeitfenster n = 200 +9,5 %, Zufall n = 40 mit 50 % +22,3 % und mit 80 % +30,8 %. 5 von 8 Strukturen billiger, 3 teurer. |
| Gilt „Cliquen = unabhängige Mengen des Komplements“? | Ja, auf dem Standardgraph mit 14 Sendungen: 23 = 23 Mengen, geprüft gegen das Aufzählen aller Teilmengen im Konfliktgraphen (ohne Bron–Kerbosch); umgekehrt 25 = 25. |

## Befunde und Korrekturen gegenüber dem Plan

Vor dem Bau lag eine Vormessung vor. Sie bestätigte den Pivot-Gewinn und die Moon–Moser-Formeln und **widerlegte die Annahme „die Degeneracy-Außenschleife senkt die Aufrufe“**; die App zeigt deshalb beide Kennzahlen (Aufrufe und Auswahlkosten) nebeneinander. Abweichungen vom Einzelplan: Kein PDF-Export (Konzepte-Demos haben üblicherweise keinen); die Regelarten Baum, Gitter und Moon–Moser sind keine Regler-Optionen, sondern feste Vergleichsgraphen in den Experimenten 2 und 3 (so bleibt jeder Regler immer wirksam); Experiment 1 rechnet bei fester Knotenzahl n = 20, unabhängig vom Regler.

## Ehrliche Grenzen

- **Aufrufe sind Elementarschritte, keine Laufzeit.** Reale Implementierungen nutzen Bitmengen oder Adjazenzlisten, und die Kosten je Aufruf unterscheiden sich. Hier Python-Mengen.
- **Kleine Graphen.** Bis n = 40 (Sweeps n = 20, Strukturen bis n = 1000) sieht man das Verhalten der Varianten, nicht, was auf Graphen mit Millionen Kanten passiert; dort ist die Degeneracy-Ordnung der Gewinn, den die Demo nur im Auswahlkostenmaß zeigt.
- **Rechengrenze.** Ohne Pivot bricht ein Lauf nach 200 000 Aufrufen (Hauptansicht) bzw. 60 000 (Sweeps) ab und meldet es; die Mediane solcher Zeilen sind Untergrenzen, in den Diagrammen mit offenen Quadraten markiert.
- **Alle Fuhren sind gesucht.** Gebraucht wird oft nur die größte; Aufzählen kostet dann so viel wie die Zahl aller maximalen Cliquen.
- **Nur paarweise Verträglichkeit.** Regeln für Dreiergruppen („je zwei erlaubt, alle drei nicht“) braucht einen Hypergraphen.
- **Synthetische Graphen.** Die Muster gelten für die Graphklassen, nicht für ein bestimmtes Lager.

## Verifikation

- **Kern:** jede Einheit (`choose_pivot_tomita`, `pivot_select_cost`, `split_candidates`, `child_sets`, `is_maximal`, `degeneracy_order`, `outer_split`) gegen Handrechnung auf der Mini-Instanz (Dreieck, Pendel, isolierter Knoten: 11 / 6 / 8 Aufrufe, Auswahlkosten 14), Aufrufbudget, Trace.
- **Orakel (`tests/test_oracle_bron_kerbosch.py`):** alle drei Varianten gegen `networkx.find_cliques` auf über 300 festen Zufalls-, Zeitfenster-, Klassen- und Sonderinstanzen (leer, vollständig, Pfad, Stern, Kreis, zwei Komponenten) und gegen Brute Force über alle Teilmengen (n ≤ 12, über 200 Instanzen); Familien mit bekanntem Wert (Moon–Moser 3^k, Baum: Cliquen = Kanten, vollständiger Graph: eine Clique); Komplement-Identität gegen Brute Force über unabhängige Mengen (25 Instanzen).
- **Zweige (`tests/test_branches.py`):** jede Variante weicht auf mindestens einer Instanz von der Nachbarvariante ab; die Gleichstandsregel der Pivotwahl ist wirksam; ein schlechter Pivot (wenigste Nachbarn) ist zulässig, aber teurer; die Rechengrenzen greifen.
- **Zahlen:** `tests/test_claims.py` rechnet jede Zahl dieser README über dieselben Auswertungsfunktionen wie die App nach.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum, jede Regelart, Variante und Ansicht, Extrem-Seeds, Permalink, langsamste Ecke) und Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Schritt-Ansicht, Kernfrage, vier Experimente, Grenzen, Mathematik |
| `bkr_algorithm.py` | Kern: Einheiten der drei Varianten, Komposition mit Budget und Trace, Brute-Force-Referenzen |
| `bkr_constants.py` | Regler-Grenzen, Rechengrenzen, Farben, Presets |
| `bkr_evaluation.py` | Einstellungen, Analyse, Sweeps (Dichte, Moon–Moser, Strukturen), Komplement-Prüfung |
| `bkr_presets.py` | Permalink (Begrenzen), Presets, Zufalls-Seed-Button |
| `bkr_scenario.py` | Graphen: Zufall, Zeitfenster, Klassenregeln, Moon–Moser, Baum, Gitter, skalenfrei |
| `bkr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und networkx (nur für die Gegenprobe) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Algorithmus, Orakel, Zweige, Szenarien, Zahlen, Figuren, Presets, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Größte Clique statt aller:** Schranken, die nur die größte Fuhre suchen, sind ein eigenes Stück der Reihe.
- **Bitmengen-Implementierung und Parallelisierung:** die Demo zählt Aufrufe, nicht Laufzeit.
- **Hypergraphen:** Regeln für mehr als zwei Sendungen.
- **PDF-Export** (siehe Korrekturen oben).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Literatur

- Bron, C., & Kerbosch, J. (1973). *Algorithm 457: finding all cliques of an undirected graph.* Communications of the ACM 16(9), 575–577.
- Moon, J. W., & Moser, L. (1965). *On cliques in graphs.* Israel Journal of Mathematics 3, 23–28.
- Tomita, E., Tanaka, A., & Takahashi, H. (2006). *The worst-case time complexity for generating all maximal cliques and computational experiments.* Theoretical Computer Science 363(1), 28–42.
- Eppstein, D., Löffler, M., & Strash, D. (2010). *Listing all maximal cliques in sparse graphs in near-optimal time.* ISAAC 2010, LNCS 6506, 403–414.

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
