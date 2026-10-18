"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink-Begrenzung."""

import pytest
from streamlit.testing.v1 import AppTest

import bkr_constants as C
import bkr_evaluation as ev
import bkr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_options():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX, name
        assert C.DENSITY_MIN <= p["density"] <= C.DENSITY_MAX, name
        assert 0 <= p["seed"] <= C.SEED_MAX, name
        assert p["type"] in C.GRAPH_TYPES and p["variant"] in C.VARIANTS and p["view"] in C.VIEWS, name


def test_default_settings_are_valid_and_inside_the_bounds():
    s = ev.Settings()
    assert s.graph_type in C.GRAPH_TYPES and s.variant in C.VARIANTS and s.view in C.VIEWS
    assert C.N_MIN <= s.n <= C.N_MAX and C.DENSITY_MIN <= s.density <= C.DENSITY_MAX


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_url_params_are_unique():
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_every_preset_loads_into_valid_settings():
    for name, p in C.PRESETS.items():
        s = ev.Settings(graph_type=p["type"], n=p["n"], density=p["density"], seed=p["seed"], variant=p["variant"], view=p["view"])
        a = ev.analyse(s)
        assert a.result.calls > 0, name


def test_coerce_clamps_numbers_and_rejects_unknown_choices():
    n_spec = P.SETTING_SPECS["n_slider"]
    assert P._coerce(n_spec, "9999") == C.N_MAX and P._coerce(n_spec, "-5") == C.N_MIN and P._coerce(n_spec, "abc") is None
    type_spec = P.SETTING_SPECS["type_select"]
    assert P._coerce(type_spec, "windows") == "windows" and P._coerce(type_spec, "zzz") is None
    assert P._coerce(n_spec, ["12"]) == 12


def _probe():
    import streamlit as st

    import bkr_presets as P
    P.load_permalink_settings()
    P.init_session_state_defaults()
    st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}


def test_permalink_is_clamped_to_the_bounds_and_invalid_values_fall_back():
    at = AppTest.from_function(_probe)
    at.query_params["n"] = "9999"
    at.query_params["d"] = "-3"
    at.query_params["gt"] = "windows"
    at.query_params["v"] = "nonsense"
    at.run()
    assert not at.exception
    seen = at.session_state["seen"]
    assert seen["n_slider"] == C.N_MAX and seen["density_slider"] == C.DENSITY_MIN
    assert seen["type_select"] == "windows" and seen["variant_radio"] == C.DEFAULT_VARIANT


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_apply_preset_writes_every_state_key(name):
    def _apply(preset_name):
        import streamlit as st

        import bkr_presets as P
        P.init_session_state_defaults()
        P.apply_preset(preset_name)
        st.session_state["seen"] = {k: st.session_state[k] for k in P.SETTING_SPECS}

    at = AppTest.from_function(_apply, args=(name,))
    at.run()
    assert not at.exception
    p = C.PRESETS[name]
    seen = at.session_state["seen"]
    assert seen["n_slider"] == p["n"] and seen["type_select"] == p["type"] and seen["density_slider"] == p["density"]
