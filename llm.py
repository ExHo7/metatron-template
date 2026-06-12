#!/usr/bin/env python3
"""
METATRON - llm.py
Ollama interface for metatron-qwen model.
Builds prompts, handles AI responses, runs tool dispatch loop.
Model: metatron-qwen (fine-tuned from huihui_ai/qwen3.5-abliterated:9b)
"""

import re
import requests
import json
from tools import run_tool_by_command, available_tools_text
from search import handle_search_dispatch

OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL_NAME  = "metatron-qwen"
MAX_TOKENS = 8192
MAX_TOOL_LOOPS = 9   # max times AI can call tools per session
OLLAMA_TIMEOUT = 600 

# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are METATRON, an elite AI penetration testing assistant running on Parrot OS.
You are precise, technical, and direct. No fluff.

You have access to real tools. To use them, write tags in your response:

  [TOOL: nmap -sV 192.168.1.1]       → runs nmap or any CLI tool
  [SEARCH: CVE-2021-44228 exploit]   → searches the web via DuckDuckGo

Available recon tools (use exact binary name inside [TOOL:]):
{{TOOLS}}

Rules:
- Always analyze scan data thoroughly before suggesting exploits
- List vulnerabilities with: name, severity (critical/high/medium/low), port, service
- For each vulnerability, suggest a concrete fix
- If you need more information, use [SEARCH:] or [TOOL:]
- Format vulnerabilities clearly so they can be saved to a database
- Be specific about CVE IDs when you know them
- Always give a final risk rating: CRITICAL / HIGH / MEDIUM / LOW

Output format for vulnerabilities (use this exactly):
VULN: <name> | SEVERITY: <level> | PORT: <port> | SERVICE: <service>
DESC: <description>
FIX: <fix recommendation>

Output format for exploits:
EXPLOIT: <name> | TOOL: <tool> | PAYLOAD: <payload or description>
RESULT: <expected result>
NOTES: <any notes>

End your analysis with:
RISK_LEVEL: <CRITICAL|HIGH|MEDIUM|LOW>
SUMMARY: <2-3 sentence overall summary>
IMPORTANT: Never use markdown bold (**text**) or 
headers (## text). Plain text only. No exceptions.
IMPORTANT RULES FOR ACCURACY:
- nmap filtered or no-response means INCONCLUSIVE not vulnerable
- Never assert a server version without seeing it in scan output
- Never infer CVEs from guessed versions
- curl timeouts and HTTP_CODE=000 mean the host is unreachable not exploitable
- ab and stress tools are not Slowloris unless confirmed
- Only assign CRITICAL if there is direct evidence of exploitability
- If evidence is weak mark severity as LOW with note: unconfirmed"""

# Inject the live tool catalogue (derived from recon_tools registry) so the
# model knows which tools it can dispatch via [TOOL: ...].
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{TOOLS}}", available_tools_text())


# ─────────────────────────────────────────────
# OLLAMA API CALL
# ─────────────────────────────────────────────

def ask_ollama(messages: list) -> str:
    try:
        payload = {
            "model":  MODEL_NAME,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": MAX_TOKENS,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        print(f"\n[*] Sending to {MODEL_NAME}...")
        resp = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        response = data.get("message", {}).get("content", "").strip()
        if not response:
            return "[!] Model returned empty response."
        return response
    except requests.exceptions.ConnectionError:
        return "[!] Cannot connect to Ollama. Is it running? Try: ollama serve"
    except requests.exceptions.Timeout:
        return "[!] Ollama timed out. Model may be loading, try again."
    except requests.exceptions.HTTPError as e:
        return f"[!] Ollama HTTP error: {e}"
    except Exception as e:
        return f"[!] Unexpected error: {e}"


# ─────────────────────────────────────────────
# TOOL DISPATCH
# ─────────────────────────────────────────────

def extract_tool_calls(response: str) -> list:
    """
    Extract all [TOOL: ...] and [SEARCH: ...] tags from AI response.
    Returns list of tuples: [("TOOL", "nmap -sV x.x.x.x"), ("SEARCH", "CVE...")]
    """
    calls = []

    tool_matches   = re.findall(r'\[TOOL:\s*(.+?)\]',   response)
    search_matches = re.findall(r'\[SEARCH:\s*(.+?)\]', response)

    for m in tool_matches:
        calls.append(("TOOL", m.strip()))
    for m in search_matches:
        calls.append(("SEARCH", m.strip()))

    return calls

def summarize_tool_output(raw_output: str) -> str:
    """
    Compress raw tool output into security-relevant bullet points
    before injecting into the LLM context.
    Keeps context size manageable across rounds.
    """
    if len(raw_output) < 500:
        return raw_output

    try:
        payload = {
            "model":  MODEL_NAME,
            "messages": [
    {"role": "system", "content": "You are a security data compressor. Extract only security-relevant facts. Return maximum 15 bullet points. Plain text only. No markdown."},
    {"role": "user", "content": f"Compress this tool output:\n{raw_output[:6000]}"} ],
            "stream": False,
            "options": {
                "num_predict": 512,
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        summary = resp.json().get("message", {}).get("content", "").strip()
        return summary if summary else raw_output
    except Exception:
        return raw_output
def run_tool_calls(calls: list) -> str:
    """
    Execute all tool/search calls and return combined results string.
    """
    if not calls:
        return ""

    results = ""
    for call_type, call_content in calls:
        print(f"\n  [DISPATCH] {call_type}: {call_content}")

        if call_type == "TOOL":
            output = run_tool_by_command(call_content)
        elif call_type == "SEARCH":
            output = handle_search_dispatch(call_content)
        else:
            output = f"[!] Unknown call type: {call_type}"

        compressed = summarize_tool_output(output.strip())
        results += f"\n[{call_type} RESULT: {call_content}]\n"
        results += "─" * 40 + "\n"
        results += compressed + "\n"

    return results


# ─────────────────────────────────────────────
# PARSER — extract structured data from AI output
# ─────────────────────────────────────────────
def _clean(line: str) -> str:
    return re.sub(r'\*+', '', line).strip()
def parse_vulnerabilities(response: str) -> list:
    """
    Parse VULN: lines from AI response into dicts.
    Returns list of vulnerability dicts ready for db.save_vulnerability()
    """
    vulns = []
    lines = response.splitlines()

    i = 0
    while i < len(lines):
        line = _clean(lines[i])
        if line.startswith("VULN:"):
            vuln = {
                "vuln_name":   "",
                "severity":    "medium",
                "port":        "",
                "service":     "",
                "description": "",
                "fix":         ""
            }

            # parse header line: VULN: name | SEVERITY: x | PORT: x | SERVICE: x
            parts = line.split("|")
            for part in parts:
                part = part.strip()
                if part.startswith("VULN:"):
                    vuln["vuln_name"] = part.replace("VULN:", "").strip()
                elif part.startswith("SEVERITY:"):
                    vuln["severity"] = part.replace("SEVERITY:", "").strip().lower()
                elif part.startswith("PORT:"):
                    vuln["port"] = part.replace("PORT:", "").strip()
                elif part.startswith("SERVICE:"):
                    vuln["service"] = part.replace("SERVICE:", "").strip()

            # look ahead for DESC: and FIX: lines
            j = i + 1
            while j < len(lines) and j <= i + 5:
                next_line = _clean(lines[j])
                if next_line.startswith(("VULN:", "EXPLOIT:", "RISK_LEVEL:", "SUMMARY:")):
                    break
                if next_line.startswith("DESC:"):
                    vuln["description"] = next_line.replace("DESC:", "").strip()
                elif next_line.startswith("FIX:"):
                    vuln["fix"] = next_line.replace("FIX:", "").strip()
                j += 1

            if vuln["vuln_name"]:
                vulns.append(vuln)

        i += 1

    return vulns


def parse_exploits(response: str) -> list:
    """
    Parse EXPLOIT: lines from AI response into dicts.
    Returns list of exploit dicts ready for db.save_exploit()
    """
    exploits = []
    lines = response.splitlines()

    i = 0
    while i < len(lines):
        line = _clean(lines[i])
        if line.startswith("EXPLOIT:"):
            exploit = {
                "exploit_name": "",
                "tool_used":    "",
                "payload":      "",
                "result":       "unknown",
                "notes":        ""
            }

            parts = line.split("|")
            for part in parts:
                part = part.strip()
                if part.startswith("EXPLOIT:"):
                    exploit["exploit_name"] = part.replace("EXPLOIT:", "").strip()
                elif part.startswith("TOOL:"):
                    exploit["tool_used"] = part.replace("TOOL:", "").strip()
                elif part.startswith("PAYLOAD:"):
                    exploit["payload"] = part.replace("PAYLOAD:", "").strip()

            j = i + 1
            while j < len(lines) and j <= i + 4:
                next_line = _clean(lines[j])
                if next_line.startswith(("VULN:", "EXPLOIT:", "RISK_LEVEL:", "SUMMARY:")):
                    break
                if next_line.startswith("RESULT:"):
                    exploit["result"] = next_line.replace("RESULT:", "").strip()
                elif next_line.startswith("NOTES:"):
                    exploit["notes"] = next_line.replace("NOTES:", "").strip()
                j += 1

            if exploit["exploit_name"]:
                exploits.append(exploit)

        i += 1

    return exploits


def parse_risk_level(response: str) -> str:
    """Extract the LAST RISK_LEVEL from AI response (most recent verdict wins)."""
    matches = re.findall(r'RISK_LEVEL:\s*(CRITICAL|HIGH|MEDIUM|LOW)', response, re.IGNORECASE)
    return matches[-1].upper() if matches else "UNKNOWN"


def parse_summary(response: str) -> str:
    matches = re.findall(r'SUMMARY:\s*(.+)', response, re.IGNORECASE)
    return matches[-1].strip() if matches else ""


def _dedup_by(items: list, key: str) -> list:
    """Keep first occurrence per key (case-insensitive) — vulns/exploits can
    repeat across analysis rounds when we parse the whole transcript."""
    seen = set()
    out = []
    for it in items:
        k = it.get(key, "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out


def _is_error_response(response: str) -> bool:
    """ask_ollama returns '[!] ...' sentinels on errors / empty output."""
    return (not response.strip()) or response.startswith("[!]")


# ─────────────────────────────────────────────
# MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────

def analyse_target(target: str, raw_scan: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"""TARGET: {target}

RECON DATA:
{raw_scan}

Analyze this target completely. Use [TOOL:] or [SEARCH:] if you need more information.
List all vulnerabilities, fixes, and suggest exploits where applicable."""
        }
    ]

    transcript = []   # every non-error model response, in order
    last_raw = ""     # last raw response (even an error) — fallback for display

    for loop in range(MAX_TOOL_LOOPS):
        response = ask_ollama(messages)
        last_raw = response

        print(f"\n{'─'*60}")
        print(f"[METATRON - Round {loop + 1}]")
        print(f"{'─'*60}")
        print(response)

        is_error = _is_error_response(response)
        if not is_error:
            transcript.append(response)

        # An empty/error response yields no tool calls and must NOT wipe the
        # analysis collected in earlier rounds — stop and keep what we have.
        tool_calls = [] if is_error else extract_tool_calls(response)
        if not tool_calls:
            if is_error:
                print("\n[!] Empty/error response — stopping, keeping earlier analysis.")
            else:
                print("\n[*] No tool calls. Analysis complete.")
            break

        tool_results = run_tool_calls(tool_calls)

        # add assistant response and tool results as new messages
        messages.append({
            "role": "assistant",
            "content": response
        })
        messages.append({
            "role": "user",
            "content": f"""[TOOL RESULTS]
{tool_results}

Continue your analysis with this new information.
If analysis is complete, give the final RISK_LEVEL and SUMMARY."""
        })

    # Parse across ALL rounds, not just the last — the model often stops
    # re-listing earlier findings (or returns empty) on the final turn.
    full_text = "\n\n".join(transcript)
    vulnerabilities = _dedup_by(parse_vulnerabilities(full_text), "vuln_name")
    exploits        = _dedup_by(parse_exploits(full_text), "exploit_name")
    risk_level      = parse_risk_level(full_text)
    summary         = parse_summary(full_text)

    full_response = full_text if transcript else last_raw

    print(f"\n[+] Parsed: {len(vulnerabilities)} vulns, {len(exploits)} exploits | Risk: {risk_level}")

    return {
        "full_response":   full_response,
        "vulnerabilities": vulnerabilities,
        "exploits":        exploits,
        "risk_level":      risk_level,
        "summary":         summary,
        "raw_scan":        raw_scan
    }
# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("[ llm.py test — direct AI query ]\n")

    # test if ollama is reachable
    try:
        r = requests.get("http://localhost:11434", timeout=5)
        print("[+] Ollama is running.")
    except Exception:
        print("[!] Ollama not reachable. Run: ollama serve")
        exit(1)

    target = input("Test target: ").strip()
    test_scan = f"Test recon for {target} — nmap and whois data would appear here."
    result = analyse_target(target, test_scan)

    print(f"\nRisk Level : {result['risk_level']}")
    print(f"Summary    : {result['summary']}")
    print(f"Vulns found: {len(result['vulnerabilities'])}")
    print(f"Exploits   : {len(result['exploits'])}")
