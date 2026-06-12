#!/usr/bin/env python3
"""
METATRON - recon_tools/registry.py
The single source of truth: REGISTRY of ToolSpecs and everything derived from it
(menu, allowlist, default-recon set, LLM prompt text).

tools.py imports these derivations instead of hard-coding tool wiring.
"""

from __future__ import annotations

import subprocess

from .spec import ToolSpec


# name -> ToolSpec. Insertion order is preserved (dict, Py3.7+) and drives the
# numeric menu keys 1..N.
REGISTRY: dict[str, ToolSpec] = {}


# ─────────────────────────────────────────────
# BASE RUNNER (moved from tools.py — robust, never crashes)
# ─────────────────────────────────────────────

def run_tool(command: list, timeout: int = 120) -> str:
    """
    Execute a shell command, return combined stdout + stderr as string.
    Never crashes the program — always returns something.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        errors = result.stderr.strip()

        if output and errors:
            return output + "\n[STDERR]\n" + errors
        elif output:
            return output
        elif errors:
            return errors
        else:
            return "[!] Tool returned no output."

    except subprocess.TimeoutExpired:
        return f"[!] Timed out after {timeout}s: {' '.join(command)}"
    except FileNotFoundError:
        return (
            f"[!] Tool not found: {command[0]} — "
            f"install it with: sudo apt install {command[0]}"
        )
    except Exception as e:
        return f"[!] Unexpected error running {command[0]}: {e}"


# ─────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────

def register(spec: ToolSpec) -> ToolSpec:
    """Add a spec to the registry. Last registration of a name wins (override)."""
    REGISTRY[spec.name] = spec
    return spec


def make_runner(spec: ToolSpec):
    """
    Return a callable run(target) -> str for a spec.
    Simple tools get a generic runner that builds argv and calls run_tool;
    custom tools wrap their own runner. In both cases spec.target_transform
    (if set) normalizes the target first (e.g. URL -> bare domain).
    """
    transform = spec.target_transform or (lambda t: t)

    if spec.is_custom:
        def _run_custom(target: str) -> str:
            return spec.runner(transform(target))
        return _run_custom

    def _run(target: str) -> str:
        command = spec.build_command(transform(target))
        print(f"  [*] {' '.join(command)}")
        return run_tool(command, timeout=spec.timeout)

    return _run


# ─────────────────────────────────────────────
# DERIVATIONS — consumed by tools.py
# ─────────────────────────────────────────────

def build_menu() -> dict:
    """
    Build the interactive menu: {str(key): (name, runner)} numbered 1..N
    in registration order.
    """
    menu = {}
    for i, spec in enumerate(REGISTRY.values(), start=1):
        menu[str(i)] = (spec.name, make_runner(spec))
    return menu


def allowed_binaries() -> set:
    """Allowlist of executables for LLM [TOOL: ...] dispatch."""
    return {spec.binary for spec in REGISTRY.values()}


def default_recon_specs(target_type: str | None = None) -> list:
    """
    Specs that run in the default 'Run all' recon. If target_type is given,
    keep only specs compatible with it (spec.target_type == 'any' or matches).
    """
    specs = [s for s in REGISTRY.values() if s.default_recon]
    if target_type:
        specs = [s for s in specs if s.target_type in ("any", target_type)]
    return specs


def available_tools_text() -> str:
    """
    Human-readable tool catalogue for injection into the LLM system prompt.
    One line per tool: name — category/target_type — description.
    """
    lines = []
    for spec in REGISTRY.values():
        desc = f" — {spec.description}" if spec.description else ""
        lines.append(
            f"  {spec.binary} ({spec.category}, target: {spec.target_type}){desc}"
        )
    return "\n".join(lines)
