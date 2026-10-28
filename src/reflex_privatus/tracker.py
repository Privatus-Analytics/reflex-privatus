"""The tracker script tag and the event helper for Reflex apps.

Nothing here sends a request from your server, sets a cookie or reads anything
about a visitor. It only builds a ``<script>`` tag for the page head and small
pieces of browser JavaScript for event triggers.
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Iterable, Mapping
from typing import Any

import reflex as rx
from privatus_analytics.core import QUEUE_STUB_JS, Config, tag_attributes
from reflex.event import EventSpec

logger = logging.getLogger("reflex_privatus")

SITE_ID_PATTERN = re.compile(r"^pa_[A-Za-z0-9]+$")
MODULES = ("engage", "auto", "vitals", "clicks", "ask")

_JSON_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    "\u2028": "\\u2028",
    "\u2029": "\\u2029",
}


def privatus_analytics(
    site_id: str | None = None,
    *,
    modules: Iterable[str] | None = None,
    script_host: str | None = None,
    excluded_paths: Iterable[str] | None = None,
    domains: Iterable[str] | None = None,
    spa: str | None = None,
    manual: bool = False,
    enabled: bool = True,
    extra_attributes: Mapping[str, Any] | None = None,
) -> rx.Component:
    """Build the Privatus Analytics script tag for the page head.

    Add it to ``rx.App(head_components=[...])`` so it loads once on every page.

    Args:
        site_id: Your site id, for example ``"pa_AbC123"``. Falls back to the
            ``PRIVATUS_SITE_ID`` environment variable.
        modules: Tracker modules to turn on, from ``engage``, ``auto``,
            ``vitals``, ``clicks`` and ``ask``. ``None`` keeps the tracker
            default (``engage``).
        script_host: Origin that serves ``/js/pa.js``. Falls back to
            ``PRIVATUS_SCRIPT_HOST``, then ``https://privatusstats.com``.
        excluded_paths: Path patterns that are never counted, like ``["/admin/*"]``.
        domains: Hostnames to count. ``None`` counts every host.
        spa: How page changes are followed: ``auto``, ``history``, ``hash`` or ``off``.
        manual: ``True`` turns off the automatic page view.
        enabled: ``False`` leaves the tag out, for example in tests.
        extra_attributes: Other ``data-*`` attributes for the tag.

    Returns:
        A head component with the script tag, or an empty fragment when the tag
        is turned off or no site id is set.

    Raises:
        ValueError: If the site id or a module name is not valid.
    """
    config = Config(
        site_id=site_id,
        script_host=script_host,
        modules=list(modules) if modules is not None else None,
        excluded_paths=list(excluded_paths or []),
        domains=list(domains) if domains is not None else None,
        spa=spa,
        manual=manual,
        enabled=enabled,
        extra_attributes=dict(extra_attributes or {}),
    )

    resolved = config.resolved_site_id()
    if resolved is None:
        if enabled:
            logger.warning("Privatus Analytics: no site id set, so the tracking script is left out.")
        return rx.fragment()
    if not SITE_ID_PATTERN.fullmatch(resolved):
        raise ValueError(f"Privatus Analytics site id {resolved!r} must look like pa_AbC123.")
    unknown = sorted(set(config.modules or []) - set(MODULES))
    if unknown:
        raise ValueError(f"Unknown Privatus Analytics module(s): {', '.join(unknown)}. Use {', '.join(MODULES)}.")
    if not config.should_render():
        return rx.fragment()

    attrs = tag_attributes(config)
    src = attrs.pop("src")
    attrs.pop("defer", None)
    return rx.script(src=src, defer=True, custom_attrs={name: str(value) for name, value in attrs.items()})


def track(
    name: str,
    props: Mapping[str, Any] | None = None,
    *,
    revenue: float | None = None,
    currency: str | None = None,
) -> EventSpec:
    """Send a custom event from the browser.

    Use it as an event trigger, ``rx.button("Join", on_click=track("Signup"))``,
    or return it from an event handler. Events sent before the script loads
    are queued, so none are lost.

    Args:
        name: The event name, for example ``"Signup"``.
        props: Extra details as simple values, for example ``{"plan": "pro"}``.
            Never put names, emails or other personal data here.
        revenue: An amount of money to record with the event.
        currency: A three-letter currency code for ``revenue``, like ``"USD"``.

    Returns:
        An event spec that runs the tracking call in the browser.

    Raises:
        ValueError: If the name is empty, ``revenue`` is not a finite number,
            or ``currency`` is not a three-letter code.
    """
    event_name = str(name or "").strip()
    if not event_name:
        raise ValueError("Privatus Analytics event name must not be empty.")

    payload: dict[str, Any] = dict(props or {})
    if revenue is not None:
        if isinstance(revenue, bool) or not isinstance(revenue, (int, float)) or not math.isfinite(revenue):
            raise ValueError("revenue must be a finite number.")
        payload["revenue"] = revenue
    if currency is not None:
        code = str(currency).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", code):
            raise ValueError("currency must be a three-letter code, like USD.")
        payload["currency"] = code

    args = _js_json(event_name) + ("," + _js_json(payload) if payload else "")
    return rx.call_script(f"{QUEUE_STUB_JS};window.privatus.track({args})")


def _js_json(value: Any) -> str:
    text = json.dumps(value, separators=(",", ":"), default=str)
    for char, escape in _JSON_ESCAPES.items():
        text = text.replace(char, escape)
    return text
