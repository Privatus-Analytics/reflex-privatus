"""Cookieless Privatus Analytics for Reflex apps.

Adds the tracking script to the page head and gives you a ``track`` event
helper. It never sends events from your server, sets no cookies and reads
nothing about your visitors.
"""

from reflex_privatus.tracker import MODULES, privatus_analytics, track

__version__ = "0.1.0"

__all__ = ["MODULES", "__version__", "privatus_analytics", "track"]
