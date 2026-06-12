#!/usr/bin/env python3
"""
METATRON - recon_tools/normalize.py
Target normalizers usable as a ToolSpec.target_transform.

Some tools want a bare domain (subfinder, gau) even when the user or the LLM
hands them a full URL like "http://2million.htb/home/access". to_domain strips
scheme, userinfo, path and port down to the host.
"""

from __future__ import annotations

from urllib.parse import urlparse


def to_domain(target: str) -> str:
    """
    Reduce any target to a bare hostname/domain.

      http://2million.htb/home/access  -> 2million.htb
      https://user@host.tld:8443/x      -> host.tld
      2million.htb/home                 -> 2million.htb
      2million.htb                       -> 2million.htb
    """
    t = target.strip()
    if not t:
        return t
    # Give urlparse a netloc to work with even when there's no scheme.
    parsed = urlparse(t if "://" in t else "//" + t)
    host = parsed.netloc or parsed.path
    host = host.split("/")[0]     # defensive: drop any leftover path
    host = host.split("@")[-1]    # strip userinfo
    host = host.split(":")[0]     # strip port
    return host or t
