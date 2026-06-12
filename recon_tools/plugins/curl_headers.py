#!/usr/bin/env python3
"""curl headers — HTTP + HTTPS response headers. Custom runner (two requests)."""

from recon_tools import recon_tool, run_tool


@recon_tool(
    name="curl headers",
    binary="curl",
    timeout=20,
    default_recon=True,
    category="web",
    target_type="any",
    install="sudo apt install curl",
    description="fetch HTTP and HTTPS response headers",
)
def curl_headers(target):
    print(f"  [*] curl -sI http://{target}")
    http_output = run_tool([
        "curl", "-sI",
        "--max-time", "10",
        "--location",          # follow redirects
        f"http://{target}",
    ], timeout=20)

    https_output = run_tool([
        "curl", "-sI",
        "--max-time", "10",
        "--location",
        "-k",                  # ignore cert errors
        f"https://{target}",
    ], timeout=20)

    return f"[HTTP Headers]\n{http_output}\n\n[HTTPS Headers]\n{https_output}"
