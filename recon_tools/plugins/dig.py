#!/usr/bin/env python3
"""dig — A / MX / NS / TXT DNS records. Custom runner (four lookups)."""

from recon_tools import recon_tool, run_tool


@recon_tool(
    name="dig DNS",
    binary="dig",
    timeout=15,
    default_recon=True,
    category="dns",
    target_type="domain",
    install="sudo apt install dnsutils",
    description="DNS records: A, MX, NS, TXT",
)
def dig(target):
    print(f"  [*] dig {target} (A/MX/NS/TXT)")
    a_record   = run_tool(["dig", "+short", "A",   target], timeout=15)
    mx_record  = run_tool(["dig", "+short", "MX",  target], timeout=15)
    ns_record  = run_tool(["dig", "+short", "NS",  target], timeout=15)
    txt_record = run_tool(["dig", "+short", "TXT", target], timeout=15)

    return (
        f"[A Records]\n{a_record}\n\n"
        f"[MX Records]\n{mx_record}\n\n"
        f"[NS Records]\n{ns_record}\n\n"
        f"[TXT Records]\n{txt_record}"
    )
