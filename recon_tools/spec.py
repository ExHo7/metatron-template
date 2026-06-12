#!/usr/bin/env python3
"""
METATRON - recon_tools/spec.py
ToolSpec dataclass + @recon_tool decorator.

A ToolSpec declares everything METATRON needs to know about a recon tool in
one place. The rest of the system (menu, allowlist, default recon, LLM prompt)
is derived from the registry of specs — so adding a tool means adding one spec,
nothing else.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


# Valid target types — used for the interactive menu label and to filter which
# tools run in the "Run all" default recon for a given target.
TARGET_TYPES = ("ip", "domain", "url", "any")


@dataclass
class ToolSpec:
    """
    Declarative description of a recon tool.

    Two flavours:
      - simple tool  : provide `args` with a "{target}" placeholder. A generic
                       runner substitutes the target and calls run_tool().
      - complex tool : provide `runner` — a callable run(target) -> str that does
                       its own multi-command logic (e.g. dig, curl headers).

    Exactly one of `args` / `runner` must be set.
    """

    name: str                                   # display name / logical key (e.g. "subfinder")
    binary: str                                 # executable — drives allowlist + FileNotFound hint
    args: Optional[list] = None                 # arg template, e.g. ["-sV", "--open", "{target}"]
    runner: Optional[Callable[[str], str]] = None   # custom runner(target) -> str
    target_transform: Optional[Callable[[str], str]] = None  # normalize target before run (e.g. to_domain)
    timeout: int = 120                          # seconds before run_tool kills it
    default_recon: bool = True                  # included in "Run all (default)"
    category: str = "general"                   # network | web | dns | subdomain | url | general
    target_type: str = "any"                    # ip | domain | url | any
    install: str = ""                           # install hint shown to the user
    description: str = ""                        # one-liner for the LLM prompt / menu

    def __post_init__(self):
        if not self.name or not self.binary:
            raise ValueError("ToolSpec requires both 'name' and 'binary'.")
        if self.args is None and self.runner is None:
            raise ValueError(
                f"ToolSpec '{self.name}': set either 'args' (simple tool) "
                "or 'runner' (custom tool)."
            )
        if self.args is not None and self.runner is not None:
            raise ValueError(
                f"ToolSpec '{self.name}': set only one of 'args' or 'runner', not both."
            )
        if self.target_type not in TARGET_TYPES:
            raise ValueError(
                f"ToolSpec '{self.name}': target_type must be one of {TARGET_TYPES}."
            )

    @property
    def is_custom(self) -> bool:
        return self.runner is not None

    def build_command(self, target: str) -> list:
        """Build the argv list for a simple tool by substituting {target}."""
        if self.args is None:
            raise ValueError(f"ToolSpec '{self.name}' has no args to build a command from.")
        argv = [self.binary]
        for a in self.args:
            argv.append(a.replace("{target}", target))
        return argv


# ─────────────────────────────────────────────
# DECORATOR
# ─────────────────────────────────────────────

def recon_tool(**kwargs):
    """
    Decorator form for plugin files. Registers a ToolSpec built from kwargs.

    Simple tool (no custom logic) — decorate a stub:

        @recon_tool(name="subfinder", binary="subfinder",
                    args=["-silent", "-d", "{target}"],
                    category="subdomain", target_type="domain")
        def subfinder():
            pass

    Custom tool — decorate the runner itself; it becomes the spec's runner:

        @recon_tool(name="dig", binary="dig", category="dns")
        def dig(target):
            ...
            return output

    Whether the decorated function is treated as the runner is decided by its
    signature: a function taking one positional arg (target) is used as runner
    when no `args` were supplied.
    """
    # Import here to avoid a circular import at module load time.
    from .registry import register

    def decorator(func):
        spec_kwargs = dict(kwargs)
        # If no args template given and the function accepts a target, use it as runner.
        if spec_kwargs.get("args") is None and spec_kwargs.get("runner") is None:
            import inspect
            params = inspect.signature(func).parameters
            if len(params) >= 1:
                spec_kwargs["runner"] = func
        spec = ToolSpec(**spec_kwargs)
        register(spec)
        return func

    return decorator
