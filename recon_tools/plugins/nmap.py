#!/usr/bin/env python3
"""nmap — service/version + default scripts, open ports only."""

from recon_tools import recon_tool


@recon_tool(
    name="nmap",
    binary="nmap",
    args=["-sV", "-sC", "-T4", "--open", "{target}"],
    timeout=180,
    default_recon=True,
    category="network",
    target_type="any",
    install="sudo apt install nmap",
    description="port/service scan with version detection and default scripts",
)
def nmap():
    pass
