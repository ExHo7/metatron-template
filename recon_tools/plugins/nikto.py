#!/usr/bin/env python3
"""nikto — web server vulnerability scanner. Noisy; off by default."""

from recon_tools import recon_tool


@recon_tool(
    name="nikto",
    binary="nikto",
    args=["-h", "{target}", "-nointeractive"],
    timeout=300,
    default_recon=False,   # noisy/slow — opt-in via the menu
    category="web",
    target_type="any",
    install="sudo apt install nikto",
    description="web server vuln scan (noisy; only with permission)",
)
def nikto():
    pass
