import pytest
import reflex as rx

from reflex_privatus import MODULES, __version__, privatus_analytics, track


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in ("PRIVATUS_SITE_ID", "PRIVATUS_SCRIPT_HOST", "PRIVATUS_ENV"):
        monkeypatch.delenv(name, raising=False)


def _jsx(component) -> str:
    return str(component)


def test_renders_the_script_tag_in_the_head():
    rendered = _jsx(privatus_analytics("pa_AbC123"))

    assert "Helmet" in rendered
    assert 'src:"https://privatusstats.com/js/pa.js"' in rendered
    assert '"data-site":"pa_AbC123"' in rendered
    assert "defer:true" in rendered
    assert "data-modules" not in rendered


def test_loads_through_react_helmet():
    imports = privatus_analytics("pa_AbC123")._get_all_imports()

    assert any(lib.startswith("react-helmet") for lib in imports)


def test_modules_are_listed_in_order():
    rendered = _jsx(privatus_analytics("pa_AbC123", modules=list(MODULES)))

    assert '"data-modules":"engage,auto,vitals,clicks,ask"' in rendered


def test_an_empty_module_list_loads_none():
    assert '"data-modules":""' in _jsx(privatus_analytics("pa_AbC123", modules=[]))


def test_other_settings_become_data_attributes():
    rendered = _jsx(
        privatus_analytics(
            "pa_AbC123",
            script_host="https://stats.example.com/",
            excluded_paths=["/admin/*", "/drafts/*"],
            domains=["example.com"],
            spa="hash",
            manual=True,
            extra_attributes={"data-canonical": "true"},
        )
    )

    assert 'src:"https://stats.example.com/js/pa.js"' in rendered
    assert '"data-exclude":"/admin/*,/drafts/*"' in rendered
    assert '"data-domains":"example.com"' in rendered
    assert '"data-spa":"hash"' in rendered
    assert '"data-manual":"true"' in rendered
    assert '"data-canonical":"true"' in rendered


def test_site_id_and_host_fall_back_to_the_environment(monkeypatch):
    monkeypatch.setenv("PRIVATUS_SITE_ID", "pa_FromEnv1")
    monkeypatch.setenv("PRIVATUS_SCRIPT_HOST", "https://stats.example.com")

    rendered = _jsx(privatus_analytics())

    assert '"data-site":"pa_FromEnv1"' in rendered
    assert 'src:"https://stats.example.com/js/pa.js"' in rendered


def test_renders_in_every_environment_by_default(monkeypatch):
    monkeypatch.setenv("PRIVATUS_ENV", "development")

    assert "pa.js" in _jsx(privatus_analytics("pa_AbC123"))


def test_missing_site_id_renders_nothing(caplog):
    component = privatus_analytics()

    assert isinstance(component, rx.Fragment)
    assert "pa.js" not in _jsx(component)
    assert "no site id" in caplog.text


def test_disabled_renders_nothing():
    component = privatus_analytics("pa_AbC123", enabled=False)

    assert isinstance(component, rx.Fragment)
    assert "pa.js" not in _jsx(component)


@pytest.mark.parametrize("site_id", ["AbC123", "pa_", "pa_Ab-C", 'pa_x" onload="alert(1)'])
def test_invalid_site_id_is_rejected(site_id):
    with pytest.raises(ValueError, match="site id"):
        privatus_analytics(site_id)


def test_unknown_module_is_rejected():
    with pytest.raises(ValueError, match="module"):
        privatus_analytics("pa_AbC123", modules=["engage", "heatmap"])


def test_works_as_an_app_head_component():
    app = rx.App(head_components=[privatus_analytics("pa_AbC123")])

    assert len(app.head_components) == 1


def _script(spec) -> str:
    return str(spec.args[0][1])


def test_track_runs_in_the_browser_with_a_queue():
    js = _script(track("Signup"))

    assert "window.privatus=window.privatus||{q:[]}" in js
    assert 'window.privatus.track(\\"Signup\\")' in js


def test_track_sends_props_revenue_and_currency():
    js = _script(track("Purchase", {"plan": "pro"}, revenue=49.5, currency="usd"))

    assert '\\"plan\\":\\"pro\\"' in js
    assert '\\"revenue\\":49.5' in js
    assert '\\"currency\\":\\"USD\\"' in js


def test_track_escapes_script_breaking_characters():
    js = _script(track("</script><b>", {"note": "a & b"}))

    assert "</script>" not in js
    assert "\\\\u003c/script\\\\u003e" in js
    assert "\\\\u0026" in js


def test_track_works_as_an_event_trigger():
    button = rx.button("Join", on_click=track("Signup"))

    assert "on_click" in button.event_triggers


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": ""}, "name"),
        ({"name": "Buy", "revenue": float("nan")}, "revenue"),
        ({"name": "Buy", "revenue": True}, "revenue"),
        ({"name": "Buy", "revenue": "10"}, "revenue"),
        ({"name": "Buy", "revenue": 10, "currency": "dollars"}, "currency"),
    ],
)
def test_track_rejects_bad_input(kwargs, message):
    with pytest.raises(ValueError, match=message):
        track(**kwargs)


def test_version_is_set():
    assert __version__.count(".") == 2
