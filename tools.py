#!/usr/bin/env python3
"""
METATRON - tools.py
Thin layer over the recon_tools registry.

All tool wiring (which tools exist, their args, timeouts, allowlist, default
recon) now lives in recon_tools/plugins/*. This module only DERIVES the
runtime structures the rest of METATRON consumes and keeps the original public
API stable (run_default_recon, interactive_tool_run, format_recon_for_llm,
run_single_tool, run_tool_by_command).

Add a tool: copy recon_tools/plugins/_template.py to plugins/<tool>.py.
"""

import re

from recon_tools import (
    load_plugins,
    REGISTRY,
    run_tool,                 # re-exported base runner (back-compat)
    build_menu,
    allowed_binaries,
    default_recon_specs,
    make_runner,
    available_tools_text,
)

# Populate the registry from plugins, then derive runtime structures.
load_plugins()

# {menu_key: (display_name, runner)} — numbered 1..N in plugin order.
TOOLS_MENU = build_menu()

# Allowlist for LLM [TOOL: ...] dispatch — auto-derived from registered binaries.
ALLOWED_TOOLS = allowed_binaries()


# ─────────────────────────────────────────────
# TARGET TYPE DETECTION
# ─────────────────────────────────────────────

_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def detect_target_type(target: str) -> str:
    """Best-effort classify a target as ip | url | domain."""
    t = target.strip()
    if _IPV4_RE.match(t):
        return "ip"
    if t.startswith(("http://", "https://")):
        return "url"
    return "domain"


# ─────────────────────────────────────────────
# RECON PIPELINE
# ─────────────────────────────────────────────

def run_default_recon(target: str) -> dict:
    """
    Run the default recon pipeline (specs with default_recon=True that are
    compatible with the target type). Returns {tool_name: output_string}.
    """
    ttype = detect_target_type(target)
    specs = default_recon_specs(target_type=ttype)

    print(f"\n[*] Starting recon on: {target}  (type: {ttype})")
    print("─" * 50)

    results = {}
    for spec in specs:
        runner = make_runner(spec)
        results[spec.name] = runner(target)

    print("─" * 50)
    print("[+] Recon complete.\n")
    return results


def run_single_tool(tool_key: str, target: str) -> str:
    """Run one tool by its menu key. Used by AI tool dispatch / manual select."""
    if tool_key in TOOLS_MENU:
        name, func = TOOLS_MENU[tool_key]
        return func(target)
    return f"[!] Unknown tool key: {tool_key}"


def format_recon_for_llm(results: dict) -> str:
    """Flatten the recon results dict into one clean string for the LLM prompt."""
    output = ""
    for tool, data in results.items():
        output += f"\n{'='*50}\n"
        output += f"[ {tool.upper()} OUTPUT ]\n"
        output += f"{'='*50}\n"
        output += data.strip() + "\n"
    return output


def run_tool_by_command(command_str: str) -> str:
    """
    Execute a raw command string from the LLM ([TOOL: ...]) — allowlist only.
    The allowlist is derived from the registered tools' binaries.
    """
    parts = command_str.strip().split()
    if not parts:
        return "[!] Empty command."

    tool = parts[0].lower().split("/")[-1]  # handles /usr/bin/nmap etc.
    if tool not in ALLOWED_TOOLS:
        return f"[!] Tool '{parts[0]}' is not permitted. Allowed: {sorted(ALLOWED_TOOLS)}"

    return run_tool(parts)


# ─────────────────────────────────────────────
# INTERACTIVE TOOL SELECTOR (called from CLI)
# ─────────────────────────────────────────────

def interactive_tool_run(target: str) -> str:
    """Let the user manually pick which tools to run. Returns combined output."""
    ttype = detect_target_type(target)

    print("\n[ SELECT TOOLS TO RUN ]")
    for key, (name, _) in TOOLS_MENU.items():
        spec = REGISTRY.get(name)
        tag = ""
        if spec:
            flag = "default" if spec.default_recon else "opt-in"
            tag = f"  ({spec.category}/{spec.target_type}, {flag})"
        print(f"  [{key}] {name}{tag}")
    print("  [a] Run all default (target-compatible)")
    print("  [n] Run everything (incl. opt-in: nikto, katana, gau...)")

    choice = input("\nChoice(s) e.g. 1 2 4 or a: ").strip().lower()

    if choice == "a":
        results = run_default_recon(target)
        return format_recon_for_llm(results)

    if choice == "n":
        combined = {}
        for key, (name, func) in TOOLS_MENU.items():
            print(f"\n[*] Running {name}...")
            combined[name] = func(target)
        return format_recon_for_llm(combined)

    combined = {}
    for key in choice.split():
        if key in TOOLS_MENU:
            name, func = TOOLS_MENU[key]
            print(f"\n[*] Running {name}...")
            combined[name] = func(target)
        else:
            print(f"[!] Unknown option: {key}")

    return format_recon_for_llm(combined)


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("[ Registered tools ]")
    print(available_tools_text())
    print()
    target = input("Enter test target (IP or domain): ").strip()
    results = run_default_recon(target)
    print(format_recon_for_llm(results))
