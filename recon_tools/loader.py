#!/usr/bin/env python3
"""
METATRON - recon_tools/loader.py
Auto-discovery: import every module in recon_tools/plugins/ so each plugin's
register()/@recon_tool call populates the REGISTRY.

Adding a tool = drop a file in plugins/. No central edit required.
"""

from __future__ import annotations

import importlib
import pkgutil

from . import plugins as _plugins_pkg
from .registry import REGISTRY


_loaded = False


def load_plugins(force: bool = False) -> dict:
    """
    Import all plugin modules under recon_tools/plugins/, skipping private
    modules (names starting with '_', e.g. _template.py). Idempotent.
    Returns the populated REGISTRY.
    """
    global _loaded
    if _loaded and not force:
        return REGISTRY

    # Sort module names so menu numbering is deterministic across platforms.
    names = sorted(
        mod.name
        for mod in pkgutil.iter_modules(_plugins_pkg.__path__)
        if not mod.name.startswith("_")
    )
    for name in names:
        importlib.import_module(f"{_plugins_pkg.__name__}.{name}")

    _loaded = True
    return REGISTRY
