#!/usr/bin/env python3
"""subfinder — passive subdomain enumeration (ProjectDiscovery)."""

from recon_tools import recon_tool


@recon_tool(
    name="subfinder",
    binary="subfinder",
    args=["-silent", "-d", "{target}"],
    timeout=120,
    default_recon=True,            # passive + fast — safe for default recon
    category="subdomain",
    target_type="domain",
    install="go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
    description="passive subdomain enumeration for a domain",
)
def subfinder():
    pass
