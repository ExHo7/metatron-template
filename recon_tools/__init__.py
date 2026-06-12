#!/usr/bin/env python3
"""
METATRON - recon_tools package
Declarative tool registry + plugin auto-discovery.

Public API:
    from recon_tools import (
        ToolSpec, recon_tool, register, REGISTRY, run_tool,
        load_plugins, build_menu, allowed_binaries,
        default_recon_specs, make_runner, available_tools_text,
    )

Add a tool: copy recon_tools/plugins/_template.py to plugins/<yourtool>.py and
fill in the spec. It is auto-discovered on load_plugins() — no other edits.
"""

from .spec import ToolSpec, recon_tool, TARGET_TYPES
from .registry import (
    REGISTRY,
    register,
    run_tool,
    make_runner,
    build_menu,
    allowed_binaries,
    default_recon_specs,
    available_tools_text,
)
from .loader import load_plugins

__all__ = [
    "ToolSpec",
    "recon_tool",
    "TARGET_TYPES",
    "REGISTRY",
    "register",
    "run_tool",
    "make_runner",
    "build_menu",
    "allowed_binaries",
    "default_recon_specs",
    "available_tools_text",
    "load_plugins",
]
