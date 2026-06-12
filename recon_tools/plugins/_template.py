#!/usr/bin/env python3
"""
METATRON - plugin template
═══════════════════════════════════════════════════════════════════════════

HOW TO ADD A TOOL
  1. Copy this file:  cp _template.py mytool.py
  2. Rename the function and fill in the spec below.
  3. Done. The loader auto-discovers it — no edit to tools.py or anywhere else.

Files whose name starts with "_" (like this one) are SKIPPED by the loader,
so this template never registers anything.
═══════════════════════════════════════════════════════════════════════════

There are two kinds of tool:

──────────────────────────────────────────────────────────────────────────
A) SIMPLE TOOL  — one command, the target slots into the args.
   Use "{target}" as the placeholder; the generic runner substitutes it and
   calls run_tool() (handles timeout, missing-binary hint, no crashes).

    from recon_tools import recon_tool

    @recon_tool(
        name="mytool",                 # logical key + display name
        binary="mytool",               # executable on PATH (also the allowlist entry)
        args=["-flag", "{target}"],    # argv after the binary; {target} is filled in
        timeout=120,                   # seconds
        default_recon=True,            # included in "Run all (default)"?
        category="web",                # network | web | dns | subdomain | url | general
        target_type="domain",          # ip | domain | url | any
        install="sudo apt install mytool",
        description="what this tool does, one line (shown to the LLM)",
        # Optional: normalize the target before the run. to_domain strips
        # scheme/path/port so a URL becomes a bare domain (handy for tools that
        # only accept a domain, e.g. subfinder, gau):
        #   from recon_tools import to_domain
        #   target_transform=to_domain,
    )
    def mytool():
        # Empty body — the decorator builds a generic runner from `args`.
        pass

──────────────────────────────────────────────────────────────────────────
B) CUSTOM TOOL  — multiple commands / output aggregation.
   Decorate a function that takes `target` and returns a string. It becomes
   the tool's runner. Use run_tool() for each sub-command.

    from recon_tools import recon_tool, run_tool

    @recon_tool(
        name="mytool",
        binary="mytool",
        category="dns",
        target_type="domain",
        # no `args` here — the function below is the runner
    )
    def mytool(target):
        a = run_tool(["mytool", "-x", target], timeout=15)
        b = run_tool(["mytool", "-y", target], timeout=15)
        return f"[X]\n{a}\n\n[Y]\n{b}"
──────────────────────────────────────────────────────────────────────────
"""

# This template intentionally registers nothing.
