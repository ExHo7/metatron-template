#!/usr/bin/env python3
"""whatweb — fingerprint web technologies, CMS, frameworks, headers."""

from recon_tools import recon_tool


@recon_tool(
    name="whatweb",
    binary="whatweb",
    args=["-a", "3", "{target}"],
    timeout=60,
    default_recon=True,
    category="web",
    target_type="any",
    install="sudo apt install whatweb",
    description="web technology fingerprinting (aggression level 3)",
)
def whatweb():
    pass
