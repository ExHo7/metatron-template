#!/usr/bin/env python3
"""whois — domain registration, registrar, IP ownership."""

from recon_tools import recon_tool


@recon_tool(
    name="whois",
    binary="whois",
    args=["{target}"],
    timeout=30,
    default_recon=True,
    category="network",
    target_type="any",
    install="sudo apt install whois",
    description="domain/IP registration and ownership info",
)
def whois():
    pass
