#!/usr/bin/env python3
"""katana — web crawler / endpoint discovery (ProjectDiscovery)."""

from recon_tools import recon_tool


@recon_tool(
    name="katana",
    binary="katana",
    args=["-silent", "-u", "{target}"],
    timeout=180,
    default_recon=False,           # active crawl, noisy/slow — opt-in via menu
    category="url",
    target_type="url",
    install="go install github.com/projectdiscovery/katana/cmd/katana@latest",
    description="active web crawler that discovers URLs/endpoints",
)
def katana():
    pass
