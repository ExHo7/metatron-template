#!/usr/bin/env python3
"""gau (getallurls) — known URLs from Wayback / CommonCrawl / OTX / URLScan."""

from recon_tools import recon_tool, to_domain


@recon_tool(
    name="gau",
    binary="gau",
    args=["{target}"],
    target_transform=to_domain,    # gau wants a domain, not a full URL+path
    timeout=120,
    default_recon=False,           # large output — opt-in via menu
    category="url",
    target_type="domain",
    install="go install github.com/lc/gau/v2/cmd/gau@latest",
    description="fetch known URLs for a domain from public archives",
)
def gau():
    pass
