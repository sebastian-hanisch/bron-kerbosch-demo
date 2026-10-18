"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: laedt app.py mit den
Standardeinstellungen, klickt jeden Preset-Button und faehrt jeden Slider an seine Grenzen und prueft, dass
kein Python-Fehler auftritt - insbesondere `streamlit.errors.StreamlitDuplicateElementId` (mehrere
st.plotly_chart-Aufrufe ohne eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)
und `StreamlitAPIException` bei Slidern mit berechneten Grenzen (min == max)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = 180
AUTOPLAY_MARKER = "\u25b6"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


# --- Zusätzlich: die echten Regler dieser Demo (Auswahlfelder, Optionsfelder, Seed, Permalink) -----------------------------------------------

def _slider(at, label_start):
    """Slider nach Beschriftung (die Reihenfolge in at.slider beginnt mit dem Schritt-Regler der Hauptfläche)."""
    return next(s for s in at.slider if s.label.startswith(label_start))


def test_every_graph_type_variant_and_view_renders_without_exception():
    for key in ("random", "windows", "classes"):
        at = _fresh_app()
        at.selectbox[0].set_value(key).run(timeout=TIMEOUT)     # roher Schlüssel (select_index kollidiert in AppTest mit format_func)
        assert not at.exception, (key, [str(e) for e in at.exception])
    for radio_index, keys in ((0, ("naive", "pivot", "degeneracy")), (1, ("compat", "conflict"))):      # 0: Variante, 1: Anzeige
        for key in keys:
            at = _fresh_app()
            at.radio[radio_index].set_value(key).run(timeout=TIMEOUT)
            assert not at.exception, (radio_index, key, [str(e) for e in at.exception])


def test_extreme_seeds_do_not_raise():
    for seed in (0, 999999):
        at = _fresh_app()
        at.number_input[0].set_value(seed).run(timeout=TIMEOUT)
        assert not at.exception, (seed, [str(e) for e in at.exception])


def test_slowest_corner_dense_forty_without_pivot_aborts_gracefully():
    at = _fresh_app()
    _slider(at, "Sendungen").set_value(40).run(timeout=TIMEOUT)
    _slider(at, "Anteil").set_value(95).run(timeout=TIMEOUT)
    at.radio[0].set_value("naive").run(timeout=TIMEOUT)      # ohne Pivot
    assert not at.exception, [str(e) for e in at.exception]
    assert any("abgebrochen" in w.value for w in at.warning)


def test_permalink_parameters_are_applied():
    at = AppTest.from_file(APP_PATH)
    at.query_params["gt"] = "classes"
    at.query_params["n"] = "22"
    at.query_params["d"] = "60"
    at.query_params["seed"] = "5"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert _slider(at, "Sendungen").value == 22 and _slider(at, "Anteil").value == 60 and at.number_input[0].value == 5
    assert at.selectbox[0].value == "classes"


def test_core_question_verdict_is_shown():
    at = _fresh_app()
    texts = [x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning]
    assert any("Aufrufe" in t for t in texts)
