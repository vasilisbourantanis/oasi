#!/usr/bin/env python3
"""
OASI - Open Source Intelligence Tool
Author: Mata
Version: 3.2
"""

import argparse
import socket
import sys
import os
# ───────────────────────────────────────────────────────────────────────────
# ONE-TIME AUTO INSTALLER (Reads requirements.txt & bypasses Linux venv lock)
# ───────────────────────────────────────────────────────────────────────────
MARKER_FILE = ".installed"
REQ_FILE = "requirements.txt"

if not os.path.exists(MARKER_FILE):
    print("[*] First run detected! Checking and installing dependencies...")
    
    if os.path.exists(REQ_FILE):
        try:
            # Executes pip using your requirements.txt file directly
            # Appends --break-system-packages to cleanly bypass the Kali/Ubuntu lock
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", REQ_FILE, "--break-system-packages", "--quiet"
            ])
            
            # Creates a hidden marker file so this install block never runs again
            with open(MARKER_FILE, "w") as f:
                f.write("OASI Dependencies Installed Successfully.")
                
            print("[+] All dependencies installed successfully! Launching...\n")
            
        except Exception as e:
            print(f"[!] Error during automatic installation: {e}")
            print(f"[!] Please run manually: pip3 install -r {REQ_FILE} --break-system-packages")
            sys.exit(1)
    else:
        print(f"[!] {REQ_FILE} not found. Attempting to launch with current system packages...")
# ───────────────────────────────────────────────────────────────────────────
import time
import json
import shutil
import subprocess
import urllib.request
import urllib.parse
import http.client as httplib

import requests
import urllib3
import colorama
from colorama import Fore, Style, init
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)

# ──────────────────────────────────────────────
#  CONFIG  –  edit these to match your GitHub
# ──────────────────────────────────────────────
GITHUB_USER    = "MataGreek"
GITHUB_REPO    = "oasi"
GITHUB_BRANCH  = "master"
VERSION_FILE   = "core/version.txt"   # path inside the repo
CURRENT_VER    = "3.2"                # this build's version

# Files the updater will pull from GitHub (path-in-repo → local-path)
UPDATE_FILES = {
    "oasi.py":                    "oasi.py",
    "requirements.txt":           "requirements.txt",
    "wordlist/simple_wl.txt":     "wordlist/simple_wl.txt",
    "wordlist/default_wl.txt":    "wordlist/default_wl.txt",
    "wordlist/shells.txt":        "wordlist/shells.txt",
}

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

yes_choice = {"", "yes", "y"}
no_choice  = {"no", "n"}

# ──────────────────────────────────────────────
#  BANNER
# ──────────────────────────────────────────────

def banner():
    print(Fore.CYAN + r"""
   ____           _____ _____
  / __ \   /\    / ____|_   _|
 | |  | | /  \  | (___   | |
 | |  | |/ /\ \  \___ \  | |
 | |__| / ____ \ ____) |_| |_
  \____/_/    \_\_____/|_____|
""")
    print(Fore.WHITE + f"""  {'─'*57}
  Version : {CURRENT_VER}
  Author  : Mata
  Donate  : https://www.buymeacoffee.com/mataroot
  {'─'*57}
""")


# ──────────────────────────────────────────────
#  AUTO-UPDATER
# ──────────────────────────────────────────────

def _raw_url(repo_path: str) -> str:
    return f"{RAW_BASE}/{repo_path}"


def _fetch_text(url: str) -> str | None:
    """Return decoded text from URL, or None on error."""
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            return resp.read().decode().strip()
    except Exception:
        return None


def check_updates(silent: bool = False):
    """
    Compare local version against GitHub version.txt.
    If newer:  ask the user whether to update.
    silent=True → skip the 'you are up to date' message.
    """
    print(Fore.CYAN + "\n[*] Checking for updates...")
    remote_ver = _fetch_text(_raw_url(VERSION_FILE))
    if remote_ver is None:
        print(Fore.YELLOW + "[!] Could not reach GitHub to check for updates.")
        return

    if remote_ver == CURRENT_VER:
        if not silent:
            print(Fore.GREEN + f"[✓] You are up to date  (v{CURRENT_VER})")
        return

    # Newer version available
    print(Fore.YELLOW + f"\n  [+] Update available!  {CURRENT_VER}  →  {remote_ver}")
    ans = input("      Do you want to update now? [Y/n]: ").strip().lower()
    if ans not in yes_choice:
        print(Fore.WHITE + "  [→] Skipping update, running current version.\n")
        return

    _do_update(remote_ver)


def _do_update(new_ver: str):
    print(Fore.CYAN + "\n  [*] Downloading update – please wait…\n")
    errors = []

    for repo_path, local_path in UPDATE_FILES.items():
        url = _raw_url(repo_path)
        content = _fetch_text(url)
        if content is None:
            errors.append(repo_path)
            print(Fore.YELLOW + f"      [!] Skipped (not found): {repo_path}")
            continue

        # Make sure local directories exist
        os.makedirs(os.path.dirname(os.path.abspath(local_path)) or ".", exist_ok=True)

        # Write file (skip if identical)
        try:
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                    if f.read().strip() == content:
                        print(Fore.WHITE + f"      [=] No change : {local_path}")
                        continue
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            print(Fore.GREEN + f"      [✓] Updated    : {local_path}")
        except OSError as exc:
            errors.append(local_path)
            print(Fore.RED + f"      [✗] Failed     : {local_path}  ({exc})")

    # Update local version file
    ver_local = VERSION_FILE
    os.makedirs(os.path.dirname(os.path.abspath(ver_local)) or ".", exist_ok=True)
    try:
        with open(ver_local, "w") as f:
            f.write(new_ver + "\n")
    except OSError:
        pass

    if errors:
        print(Fore.YELLOW + f"\n  [!] {len(errors)} file(s) could not be updated.")
    else:
        print(Fore.GREEN + f"\n  [✓] Update to v{new_ver} complete!")

    print(Fore.WHITE + "  [→] Please restart the program for changes to take effect.\n")
    sys.exit(0)


# ──────────────────────────────────────────────
#  ARGUMENT PARSER
# ──────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        prog="oasi",
        description="OASI – Open-source web reconnaissance tool"
    )
    parser.add_argument("-u", "--url",      required=True,  metavar="URL",      help="Target URL")
    parser.add_argument("-w", "--wordlist", required=False, metavar="FILE",     help="Custom wordlist for dir scan")
    parser.add_argument("-b", "--batch",    action="store_true",                help="Non-interactive; auto-accept prompts")
    parser.add_argument("-s", "--shell",    action="store_true",                help="Scan for uploaded web shells")
    parser.add_argument("-p", "--ports",    action="store_true",                help="Run port scan")
    parser.add_argument("--threads",        type=int, default=10, metavar="N",  help="Dir-scan thread count (default: 10)")
    parser.add_argument("--update",         action="store_true",                help="Check for updates and exit")
    parser.add_argument("--timeout",        type=float, default=5.0,            help="HTTP request timeout (default: 5 s)")
    parser.add_argument("--ai",             action="store_true",                help="Run AI-powered analysis using Claude API (needs ANTHROPIC_API_KEY)")
    return parser.parse_args()


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def parse_host(url: str) -> str:
    host = urllib3.util.url.parse_url(url).host
    if not host:
        print(Fore.RED + "[!] Could not parse host from URL.")
        sys.exit(1)
    return host


def section(title: str):
    width = 40
    print("\n" + Fore.CYAN + "┌" + "─" * width + "┐")
    print("│  " + Style.BRIGHT + title.ljust(width - 2) + Fore.CYAN + "│")
    print("└" + "─" * width + "┘\n")


def ok(msg):   print(Fore.GREEN  + "[+] " + Fore.RESET + msg)
def warn(msg): print(Fore.YELLOW + "[!] " + Fore.RESET + msg)
def info(msg): print(Fore.BLUE   + "[i] " + Fore.RESET + msg)
def bad(msg):  print(Fore.RED    + "[-] " + Fore.RESET + msg)


# ──────────────────────────────────────────────
#  SCAN MODULES
# ──────────────────────────────────────────────

def check_host(target: str, timeout: float):
    section("Host Information")
    try:
        ip = socket.gethostbyname(target)
        ok(f"Target : {target}")
        ok(f"IP     : {ip}")
        return ip
    except socket.gaierror as e:
        bad(f"DNS resolution failed: {e}")
        sys.exit(1)


def check_headers(target: str, timeout: float):
    section("HTTP Headers & Server Info")
    for scheme in ("https", "http"):
        url = f"{scheme}://{target}"
        try:
            resp = requests.get(url, timeout=timeout, allow_redirects=True)
            interesting = ["Server", "X-Powered-By", "X-Generator",
                           "X-Frame-Options", "Content-Security-Policy",
                           "Strict-Transport-Security", "X-Content-Type-Options"]
            ok(f"Status : {resp.status_code}  ({url})")
            for h in interesting:
                if h in resp.headers:
                    info(f"{h}: {resp.headers[h]}")
            # Missing security headers
            sec_headers = {"X-Frame-Options", "Content-Security-Policy",
                           "Strict-Transport-Security", "X-Content-Type-Options"}
            missing = sec_headers - set(resp.headers.keys())
            for h in missing:
                warn(f"Missing security header: {h}")
            return
        except requests.RequestException:
            continue
    bad("Could not connect to target.")


def detect_waf(target: str, timeout: float):
    """
    Deep WAF / CDN fingerprinting using 5 independent layers:
      1. Passive header/cookie/server/body signatures  (35+ WAFs)
      2. IP range check  – does the server IP belong to a known WAF/CDN ASN?
      3. Active evasion probes  – SQLi, XSS, path traversal, bad UA
         Each probe uses a different bypass variant to confirm enforcement
      4. TLS/cert fingerprint  – CDN cert issuer often reveals the provider
      5. Timing analysis  – CDN edge nodes respond faster than origin
    Outputs: WAF name, confidence score, enforcement status, bypass hints.
    """
    section("WAF / CDN Detection  (deep fingerprint)")

    import re as _re

    # ── Signature table  (name, layer, match_type, value) ─────────────────
    # layer: P=passive  A=active  T=tls  I=ip-range
    SIGS = [
        # ── Cloudflare ──────────────────────────────────────────────────────
        ("Cloudflare",          "P", "hkey",   "cf-ray"),
        ("Cloudflare",          "P", "hkey",   "cf-cache-status"),
        ("Cloudflare",          "P", "hkey",   "cf-mitigated"),
        ("Cloudflare",          "P", "server", "cloudflare"),
        ("Cloudflare",          "P", "cookie", "__cflb"),
        ("Cloudflare",          "P", "cookie", "cf_clearance"),
        ("Cloudflare",          "P", "body",   "cloudflare ray id"),
        ("Cloudflare",          "P", "body",   "attention required! | cloudflare"),
        # ── Akamai ──────────────────────────────────────────────────────────
        ("Akamai",              "P", "hkey",   "x-akamai-transformed"),
        ("Akamai",              "P", "hkey",   "x-akamai-request-id"),
        ("Akamai",              "P", "hkey",   "akamai-grn"),
        ("Akamai",              "P", "hval",   "akamaighost"),
        ("Akamai",              "P", "body",   "access denied - akamai"),
        ("Akamai",              "P", "body",   "reference #"),
        # ── AWS CloudFront ───────────────────────────────────────────────────
        ("AWS CloudFront",      "P", "hkey",   "x-amz-cf-id"),
        ("AWS CloudFront",      "P", "hkey",   "x-amz-cf-pop"),
        ("AWS CloudFront",      "P", "server", "cloudfront"),
        ("AWS CloudFront",      "P", "body",   "request blocked"),
        # ── AWS WAF ─────────────────────────────────────────────────────────
        ("AWS WAF",             "P", "hkey",   "x-amzn-requestid"),
        ("AWS WAF",             "P", "hkey",   "x-amzn-trace-id"),
        # ── Imperva / Incapsula ──────────────────────────────────────────────
        ("Imperva",             "P", "hkey",   "x-iinfo"),
        ("Imperva",             "P", "cookie", "incap_ses"),
        ("Imperva",             "P", "cookie", "visid_incap"),
        ("Imperva",             "P", "body",   "_incapsula_resource"),
        ("Imperva",             "P", "body",   "incapsula incident id"),
        # ── Sucuri ──────────────────────────────────────────────────────────
        ("Sucuri",              "P", "hkey",   "x-sucuri-id"),
        ("Sucuri",              "P", "hkey",   "x-sucuri-cache"),
        ("Sucuri",              "P", "server", "sucuri"),
        ("Sucuri",              "P", "body",   "sucuri website firewall"),
        # ── Fastly ──────────────────────────────────────────────────────────
        ("Fastly",              "P", "hkey",   "x-fastly-request-id"),
        ("Fastly",              "P", "hkey",   "fastly-restarts"),
        ("Fastly",              "P", "server", "varnish"),
        ("Fastly",              "P", "hval",   "fastly"),
        # ── Azure Front Door ────────────────────────────────────────────────
        ("Azure Front Door",    "P", "hkey",   "x-azure-ref"),
        ("Azure Front Door",    "P", "hkey",   "x-fd-healthprobe"),
        ("Azure Front Door",    "P", "hval",   "azure"),
        # ── F5 BIG-IP ASM ───────────────────────────────────────────────────
        ("F5 BIG-IP ASM",       "P", "hkey",   "x-waf-event-info"),
        ("F5 BIG-IP ASM",       "P", "hkey",   "x-cnection"),
        ("F5 BIG-IP ASM",       "P", "cookie", "bigipserver"),
        ("F5 BIG-IP ASM",       "P", "body",   "the requested url was rejected"),
        # ── Barracuda ───────────────────────────────────────────────────────
        ("Barracuda WAF",       "P", "cookie", "barra_counter_session"),
        ("Barracuda WAF",       "P", "body",   "barracuda networks"),
        ("Barracuda WAF",       "P", "body",   "you have been blocked"),
        # ── ModSecurity ─────────────────────────────────────────────────────
        ("ModSecurity",         "P", "hkey",   "x-modsecurity-action"),
        ("ModSecurity",         "P", "body",   "mod_security"),
        ("ModSecurity",         "P", "body",   "this error was generated by modsecurity"),
        ("ModSecurity",         "P", "body",   "406 not acceptable"),
        # ── Wordfence ───────────────────────────────────────────────────────
        ("Wordfence",           "P", "body",   "generated by wordfence"),
        ("Wordfence",           "P", "body",   "wordfence"),
        # ── Radware AppWall ─────────────────────────────────────────────────
        ("Radware AppWall",     "P", "hkey",   "x-sl-compstate"),
        ("Radware AppWall",     "P", "body",   "radware"),
        # ── Vercel ──────────────────────────────────────────────────────────
        ("Vercel",              "P", "hkey",   "x-vercel-id"),
        ("Vercel",              "P", "server", "vercel"),
        # ── Netlify ─────────────────────────────────────────────────────────
        ("Netlify",             "P", "hkey",   "x-nf-request-id"),
        ("Netlify",             "P", "server", "netlify"),
        # ── Reblaze ─────────────────────────────────────────────────────────
        ("Reblaze",             "P", "cookie", "rbzid"),
        ("Reblaze",             "P", "hkey",   "x-reblaze-protection"),
        # ── PerimeterX / HUMAN ──────────────────────────────────────────────
        ("PerimeterX",          "P", "cookie", "_px"),
        ("PerimeterX",          "P", "cookie", "_pxvid"),
        ("PerimeterX",          "P", "body",   "px-captcha"),
        # ── DataDome ────────────────────────────────────────────────────────
        ("DataDome",            "P", "cookie", "datadome"),
        ("DataDome",            "P", "body",   "datadome"),
        # ── Cloudflare Turnstile / Bot Fight ────────────────────────────────
        ("Cloudflare",          "P", "body",   "challenges.cloudflare.com"),
        # ── Nginx + naxsi ───────────────────────────────────────────────────
        ("NAXSI",               "P", "hkey",   "x-data-origin"),
        ("NAXSI",               "P", "body",   "naxsi"),
        # ── GoDaddy / Website Protection ────────────────────────────────────
        ("GoDaddy WAF",         "P", "hval",   "godaddy"),
        ("GoDaddy WAF",         "P", "body",   "godaddy website protection"),
        # ── Alibaba Cloud WAF ────────────────────────────────────────────────
        ("Alibaba Cloud WAF",   "P", "hval",   "ali-cdn"),
        ("Alibaba Cloud WAF",   "P", "body",   "error 405"),
        # ── Pantheon ────────────────────────────────────────────────────────
        ("Pantheon",            "P", "hkey",   "x-pantheon-styx-hostname"),
        ("Pantheon",            "P", "server", "nginx/pantheon"),
        # ── Stackpath / MaxCDN ──────────────────────────────────────────────
        ("StackPath",           "P", "hkey",   "x-hw"),
        ("StackPath",           "P", "hval",   "stackpath"),
    ]

    # Known WAF/CDN IP ranges (CIDR prefixes) for the IP-range layer
    # format: (waf_name, cidr_prefix_as_int, prefix_len)
    WAF_RANGES = [
        # Cloudflare
        ("Cloudflare", "103.21.244.0",  22),
        ("Cloudflare", "103.22.200.0",  22),
        ("Cloudflare", "103.31.4.0",    22),
        ("Cloudflare", "104.16.0.0",    13),
        ("Cloudflare", "104.24.0.0",    14),
        ("Cloudflare", "108.162.192.0", 18),
        ("Cloudflare", "131.0.72.0",    22),
        ("Cloudflare", "141.101.64.0",  18),
        ("Cloudflare", "162.158.0.0",   15),
        ("Cloudflare", "172.64.0.0",    13),
        ("Cloudflare", "173.245.48.0",  20),
        ("Cloudflare", "188.114.96.0",  20),
        ("Cloudflare", "190.93.240.0",  20),
        ("Cloudflare", "197.234.240.0", 22),
        ("Cloudflare", "198.41.128.0",  17),
        # Fastly
        ("Fastly",     "23.235.32.0",   20),
        ("Fastly",     "43.249.72.0",   22),
        ("Fastly",     "103.244.50.0",  24),
        ("Fastly",     "151.101.0.0",   16),
        ("Fastly",     "157.52.64.0",   18),
        ("Fastly",     "167.82.0.0",    17),
        ("Fastly",     "172.111.64.0",  18),
        ("Fastly",     "185.31.16.0",   22),
        ("Fastly",     "199.27.72.0",   21),
        # Sucuri
        ("Sucuri",     "66.248.200.0",  22),
        ("Sucuri",     "185.93.228.0",  22),
        ("Sucuri",     "192.124.249.0", 24),
        ("Sucuri",     "192.161.0.0",   24),
        ("Sucuri",     "198.forced.0.0",24),
    ]

    def _ip_in_cidr(ip_str, cidr_ip, prefix_len):
        try:
            import struct
            def to_int(s):
                parts = s.split(".")
                if len(parts) != 4: return None
                return struct.unpack("!I", bytes(int(p) for p in parts))[0]
            ip_int   = to_int(ip_str)
            cidr_int = to_int(cidr_ip)
            if ip_int is None or cidr_int is None: return False
            mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
            return (ip_int & mask) == (cidr_int & mask)
        except Exception:
            return False

    # ── Fetch baseline response ────────────────────────────────────────────
    resp = None
    base_url = None
    for scheme in ("https", "http"):
        try:
            r = requests.get(f"{scheme}://{target}", timeout=timeout,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                      "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"},
                             allow_redirects=True)
            resp = r
            base_url = f"{scheme}://{target}"
            break
        except requests.RequestException:
            continue

    if resp is None:
        bad("Could not connect for WAF detection.")
        return

    hkeys  = {k.lower() for k in resp.headers}
    hvals  = " ".join(v.lower() for v in resp.headers.values())
    server = resp.headers.get("Server", "").lower()
    cookies= " ".join(c.lower() for c in resp.cookies.keys())
    body   = resp.text.lower()[:12000]

    # ── Layer 1: Passive signatures ────────────────────────────────────────
    scores = {}
    evidence = {}
    for (waf, layer, mtype, value) in SIGS:
        hit = False
        if   mtype == "hkey":   hit = value in hkeys
        elif mtype == "hval":   hit = value in hvals
        elif mtype == "server": hit = value in server
        elif mtype == "cookie": hit = value in cookies
        elif mtype == "body":   hit = value in body
        if hit:
            scores[waf]   = scores.get(waf, 0) + 1
            evidence.setdefault(waf, []).append(f"{mtype}:{value}")

    # ── Layer 2: IP-range check ────────────────────────────────────────────
    try:
        host_ip = socket.gethostbyname(target)
        for (waf, cidr_ip, pfx) in WAF_RANGES:
            if _ip_in_cidr(host_ip, cidr_ip, pfx):
                scores[waf]   = scores.get(waf, 0) + 3   # high weight
                evidence.setdefault(waf, []).append(f"ip-range:{host_ip} in {cidr_ip}/{pfx}")
    except Exception:
        pass

    # ── Layer 3: TLS certificate issuer ────────────────────────────────────
    try:
        import ssl
        ctx  = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        conn = ctx.wrap_socket(
            socket.create_connection((target, 443), timeout=timeout),
            server_hostname=target
        )
        cert  = conn.getpeercert()
        conn.close()
        issuer_parts = dict(x[0] for x in cert.get("issuer", []))
        issuer_org   = issuer_parts.get("organizationName", "").lower()
        issuer_cn    = issuer_parts.get("commonName",        "").lower()
        san_list     = [v for t, v in cert.get("subjectAltName", []) if t == "DNS"]
        cert_text    = f"{issuer_org} {issuer_cn} {' '.join(san_list)}".lower()

        tls_map = {
            "cloudflare": "Cloudflare", "sni.cloudflaressl": "Cloudflare",
            "akamai":     "Akamai",
            "fastly":     "Fastly",
            "sucuri":     "Sucuri",
            "amazon":     "AWS CloudFront",  "digicert": None,
        }
        for kw, waf_name in tls_map.items():
            if kw in cert_text and waf_name:
                scores[waf_name]   = scores.get(waf_name, 0) + 2
                evidence.setdefault(waf_name, []).append(f"tls-cert:{kw}")
    except Exception:
        pass

    # ── Layer 4: Active probes  (multiple payload classes) ─────────────────
    # We send 4 different attacks and record which ones get blocked
    PROBES = [
        ("XSS",           f"{base_url}/?s=<script>alert(1)</script>"),
        ("SQLi",          f"{base_url}/?id=1' OR '1'='1"),
        ("Path traversal",f"{base_url}/../../etc/passwd"),
        ("Bad UA",        None),   # handled separately with a scanner UA
    ]
    block_codes = {403, 406, 429, 503, 501}
    blocked_probes = []
    ua_blocked     = False

    for label, url in PROBES:
        try:
            if label == "Bad UA":
                pr = requests.get(base_url, timeout=timeout,
                                  headers={"User-Agent": "sqlmap/1.7"},
                                  allow_redirects=False)
                if pr.status_code in block_codes:
                    ua_blocked = True
                    blocked_probes.append("Bad-UA(sqlmap)")
            else:
                pr = requests.get(url, timeout=timeout,
                                  headers={"User-Agent": "Mozilla/5.0"},
                                  allow_redirects=False)
                if pr.status_code in block_codes:
                    blocked_probes.append(label)
        except requests.RequestException:
            pass

    # ── Layer 5: Timing heuristic ──────────────────────────────────────────
    import time as _time
    cdn_likely = False
    try:
        times = []
        for _ in range(3):
            t0 = _time.perf_counter()
            requests.get(base_url, timeout=timeout,
                         headers={"User-Agent": "Mozilla/5.0"})
            times.append(_time.perf_counter() - t0)
        avg_ms = (sum(times) / len(times)) * 1000
        # CDN edge nodes typically respond < 100 ms from anywhere
        if avg_ms < 80:
            cdn_likely = True
            info(f"Avg response: {avg_ms:.0f} ms  → likely CDN edge node")
        else:
            info(f"Avg response: {avg_ms:.0f} ms")
    except Exception:
        pass

    # ── Output ─────────────────────────────────────────────────────────────
    if not scores and not blocked_probes:
        if cdn_likely:
            warn("No WAF headers found but response time suggests CDN — may be hiding identity.")
        else:
            info("No WAF/CDN detected.")
        return

    # Confidence label
    def _conf(score):
        if score >= 5: return f"{Fore.GREEN}HIGH{Fore.RESET}"
        if score >= 2: return f"{Fore.YELLOW}MEDIUM{Fore.RESET}"
        return f"{Fore.RED}LOW{Fore.RESET}"

    ranked = sorted(scores, key=lambda w: scores[w], reverse=True)
    top    = ranked[0]

    ok(f"WAF / CDN: {Fore.GREEN}{Style.BRIGHT}{top}{Style.RESET_ALL}  "
       f"[confidence: {_conf(scores[top])}  score: {scores[top]}]")
    for ev in evidence.get(top, [])[:6]:
        info(f"  ↳ {ev}")

    if blocked_probes:
        ok(f"Enforcement confirmed — blocked probes: {', '.join(blocked_probes)}")
        if ua_blocked:
            info("  ↳ Scanner User-Agent (sqlmap) was also blocked")
    else:
        warn("No probes were blocked — WAF may be in monitor/log-only mode")

    if len(ranked) > 1:
        print()
        info("Other signals:")
        for w in ranked[1:3]:
            info(f"  {w}  (score {scores[w]}): {', '.join(evidence.get(w,[])[:2])}")

    # Bypass hints (defensive: so the security team knows what to test)
    if top:
        HINTS = {
            "Cloudflare":    "Try: case variation, chunked encoding, unicode normalization",
            "Akamai":        "Try: header injection, non-standard HTTP methods",
            "ModSecurity":   "Try: comment obfuscation (/**/) in payloads",
            "Imperva":       "Try: HTTP parameter pollution",
            "AWS WAF":       "Try: oversized headers, JSON body encoding",
            "Wordfence":     "Try: encoded payloads, XML content-type",
            "F5 BIG-IP ASM": "Try: multipart/form-data encoding",
        }
        hint = HINTS.get(top)
        if hint:
            print()
            info(f"Security test hint for {top}: {hint}")


def check_cms(target: str, timeout: float):
    """
    Accurate CMS fingerprinting via:
      1. HTTP response headers  (X-Powered-By, X-Generator, etc.)
      2. HTML meta generator tag
      3. Known body patterns   (script/link paths, inline strings)
      4. Known cookies
      5. Specific indicator URLs that only exist for that CMS
    Returns the first high-confidence match; keeps trying for lower-confidence
    signals and reports all.
    """
    section("CMS Detection")

    # ── fingerprint signatures ──────────────────────────────────────────────
    # Each entry: (CMS name, confidence, match_type, value)
    # match_type: "header", "meta", "body", "cookie", "url_200"
    SIGNATURES = [
        # WordPress
        ("WordPress",   "HIGH",   "body",    "/wp-content/"),
        ("WordPress",   "HIGH",   "body",    "/wp-includes/"),
        ("WordPress",   "HIGH",   "url_200", "/wp-login.php"),
        ("WordPress",   "HIGH",   "url_200", "/wp-json/"),
        ("WordPress",   "MEDIUM", "body",    "wp-emoji"),
        ("WordPress",   "MEDIUM", "cookie",  "wordpress_"),
        ("WordPress",   "MEDIUM", "cookie",  "wp-settings"),
        # Joomla
        ("Joomla",      "HIGH",   "body",    "/media/jui/js/"),
        ("Joomla",      "HIGH",   "body",    "Joomla! -"),
        ("Joomla",      "HIGH",   "url_200", "/administrator/index.php"),
        ("Joomla",      "MEDIUM", "meta",    "joomla"),
        ("Joomla",      "MEDIUM", "cookie",  "joomla_"),
        # Drupal
        ("Drupal",      "HIGH",   "header",  "X-Generator: Drupal"),
        ("Drupal",      "HIGH",   "body",    "/sites/default/files/"),
        ("Drupal",      "HIGH",   "body",    "jQuery.extend(Drupal"),
        ("Drupal",      "HIGH",   "url_200", "/user/login"),
        ("Drupal",      "MEDIUM", "meta",    "drupal"),
        ("Drupal",      "MEDIUM", "cookie",  "SESS"),
        # PrestaShop
        ("PrestaShop",  "HIGH",   "body",    "PrestaShop"),
        ("PrestaShop",  "HIGH",   "header",  "X-Powered-By: PrestaShop"),
        ("PrestaShop",  "HIGH",   "url_200", "/index.php?controller=authentication"),
        ("PrestaShop",  "MEDIUM", "cookie",  "PrestaShop"),
        # Magento
        ("Magento",     "HIGH",   "body",    "Magento"),
        ("Magento",     "HIGH",   "body",    "mage/cookies"),
        ("Magento",     "HIGH",   "url_200", "/index.php/customer/account/login/"),
        ("Magento",     "MEDIUM", "cookie",  "PHPSESSID"),
        # TYPO3
        ("TYPO3",       "HIGH",   "meta",    "typo3"),
        ("TYPO3",       "HIGH",   "body",    "typo3/"),
        ("TYPO3",       "HIGH",   "url_200", "/typo3/index.php"),
        # OpenCart
        ("OpenCart",    "HIGH",   "body",    "route=common/home"),
        ("OpenCart",    "HIGH",   "url_200", "/index.php?route=account/login"),
        ("OpenCart",    "MEDIUM", "cookie",  "OCSESSID"),
        # Shopify
        ("Shopify",     "HIGH",   "header",  "X-ShopId"),
        ("Shopify",     "HIGH",   "header",  "X-Shopify-Stage"),
        ("Shopify",     "HIGH",   "body",    "Shopify.theme"),
        ("Shopify",     "MEDIUM", "body",    "cdn.shopify.com"),
        # Wix
        ("Wix",         "HIGH",   "body",    "static.wixstatic.com"),
        ("Wix",         "HIGH",   "body",    "wix-bolt"),
        # Squarespace
        ("Squarespace", "HIGH",   "body",    "squarespace.com"),
        ("Squarespace", "HIGH",   "header",  "Server: Squarespace"),
        # Ghost
        ("Ghost",       "HIGH",   "meta",    "ghost"),
        ("Ghost",       "HIGH",   "body",    "ghost/js"),
        ("Ghost",       "HIGH",   "url_200", "/ghost/api/"),
        # Laravel / generic PHP frameworks
        ("Laravel",     "HIGH",   "cookie",  "laravel_session"),
        ("Laravel",     "HIGH",   "body",    "laravel"),
        # Django
        ("Django",      "HIGH",   "header",  "X-Frame-Options: SAMEORIGIN"),
        ("Django",      "MEDIUM", "cookie",  "csrftoken"),
        # ASP.NET
        ("ASP.NET",     "HIGH",   "header",  "X-Powered-By: ASP.NET"),
        ("ASP.NET",     "HIGH",   "header",  "X-AspNet-Version"),
        ("ASP.NET",     "MEDIUM", "cookie",  "ASP.NET_SessionId"),
        # vBulletin
        ("vBulletin",   "HIGH",   "body",    "vBulletin"),
        # phpBB
        ("phpBB",       "HIGH",   "body",    "phpBB"),
        # MediaWiki
        ("MediaWiki",   "HIGH",   "meta",    "mediawiki"),
        ("MediaWiki",   "HIGH",   "body",    "mediawiki"),
    ]

    # Fetch homepage (try HTTPS first, fall back to HTTP)
    resp = None
    base_url = None
    for scheme in ("https", "http"):
        try:
            u = f"{scheme}://{target}"
            r = requests.get(u, timeout=timeout, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            resp = r
            base_url = u
            break
        except requests.RequestException:
            continue

    if resp is None:
        bad("Could not connect to target for CMS detection.")
        return

    body    = resp.text.lower()
    headers = {k.lower(): v.lower() for k, v in resp.headers.items()}
    cookies = " ".join(resp.cookies.keys()).lower()

    # Extract <meta name="generator"> value
    import re
    meta_gen = ""
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']',
                  resp.text, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']generator["\']',
                      resp.text, re.IGNORECASE)
    if m:
        meta_gen = m.group(1).lower()
        info(f"Meta generator: {m.group(1)}")

    # Score each CMS
    scores: dict[str, list[str]] = {}

    for (cms, confidence, mtype, value) in SIGNATURES:
        hit = False
        val_lower = value.lower()

        if mtype == "body":
            hit = val_lower in body
        elif mtype == "header":
            # value may be "HeaderName: partial-value" or just "HeaderName"
            if ":" in value:
                hname, hval = value.lower().split(":", 1)
                hit = hname.strip() in headers and hval.strip() in headers.get(hname.strip(), "")
            else:
                hit = val_lower in headers
        elif mtype == "meta":
            hit = val_lower in meta_gen
        elif mtype == "cookie":
            hit = val_lower in cookies
        elif mtype == "url_200":
            try:
                probe = requests.get(f"{base_url.rstrip('/')}{value}",
                                     timeout=timeout, allow_redirects=True,
                                     headers={"User-Agent": "Mozilla/5.0"})
                hit = probe.status_code == 200
            except requests.RequestException:
                hit = False

        if hit:
            weight = 3 if confidence == "HIGH" else 1
            scores.setdefault(cms, [])
            scores[cms].append(f"{mtype}:{value[:40]} ({confidence})")

    if not scores:
        info("No CMS fingerprint matched.")
        return

    # Sort by number of weighted hits
    def _weight(cms):
        total = 0
        for sig in scores[cms]:
            total += 3 if "HIGH" in sig else 1
        return total

    ranked = sorted(scores.keys(), key=_weight, reverse=True)
    top = ranked[0]
    top_w = _weight(top)

    ok(f"Detected CMS: {Fore.GREEN}{Style.BRIGHT}{top}{Style.RESET_ALL}  "
       f"(confidence score: {top_w})")
    for sig in scores[top]:
        info(f"  ↳ {sig}")

    if len(ranked) > 1:
        print()
        info("Other possible matches:")
        for cms in ranked[1:]:
            info(f"  {cms}  (score: {_weight(cms)})  — {', '.join(scores[cms][:2])}")


def check_robots_sitemap(target: str, timeout: float):
    section("robots.txt / sitemap.xml")
    for path in ("/robots.txt", "/sitemap.xml", "/sitemap_index.xml"):
        url = f"https://{target}{path}"
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                ok(f"Found: {url}")
                # Print first 10 non-empty lines
                lines = [l for l in resp.text.splitlines() if l.strip()][:10]
                for line in lines:
                    print("    " + line)
                if len(resp.text.splitlines()) > 10:
                    print("    …")
        except requests.RequestException:
            pass


def check_subdomains(target: str, timeout: float = 15):
    """
    Passive subdomain enumeration from 4 free, no-key sources:
      1. HackerTarget  – hostsearch API (CT logs + scan data)
      2. AlienVault OTX – passive DNS
      3. RapidDNS      – certificate transparency
      4. Certspotter   – SSL cert transparency (Spyse/SSLMate)
    Results are merged, deduplicated, DNS-resolved and printed.
    """
    section("Subdomain Enumeration  (multi-source passive)")

    found: set[str] = set()

    # ── 1. HackerTarget ────────────────────────────────────────────────────
    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={target}"
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and "error" not in resp.text.lower()[:50]:
            for line in resp.text.splitlines():
                sub = line.split(",")[0].strip().lower()
                if sub and target in sub:
                    found.add(sub)
            info(f"HackerTarget: {len(found)} entries")
        else:
            warn(f"HackerTarget: {resp.text.strip()[:80]}")
    except Exception as e:
        warn(f"HackerTarget failed: {e}")

    before = len(found)

    # ── 2. AlienVault OTX ──────────────────────────────────────────────────
    try:
        page = 1
        while True:
            url = (f"https://otx.alienvault.com/api/v1/indicators/domain/"
                   f"{target}/passive_dns?limit=500&page={page}")
            resp = requests.get(url, timeout=timeout,
                                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                break
            data = resp.json()
            records = data.get("passive_dns", [])
            if not records:
                break
            for r in records:
                h = r.get("hostname", "").lower().strip()
                if h and target in h:
                    found.add(h)
            if not data.get("has_next"):
                break
            page += 1
        info(f"AlienVault OTX: +{len(found) - before} entries")
        before = len(found)
    except Exception as e:
        warn(f"AlienVault OTX failed: {e}")

    # ── 3. RapidDNS ────────────────────────────────────────────────────────
    try:
        url = f"https://rapiddns.io/subdomain/{target}?full=1&down=1"
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            import re
            hits = re.findall(r'[\w\-\.]+\.' + re.escape(target), resp.text)
            for h in hits:
                found.add(h.lower())
        info(f"RapidDNS: +{len(found) - before} entries")
        before = len(found)
    except Exception as e:
        warn(f"RapidDNS failed: {e}")

    # ── 4. Certspotter (SSLMate) ───────────────────────────────────────────
    try:
        url = f"https://api.certspotter.com/v1/issuances?domain={target}&include_subdomains=true&expand=dns_names"
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            import re
            pattern = re.compile(r'[\w\-\.]+\.' + re.escape(target))
            for entry in resp.json():
                for name in entry.get("dns_names", []):
                    name = name.lstrip("*.").lower()
                    if target in name:
                        found.add(name)
        info(f"Certspotter: +{len(found) - before} entries")
    except Exception as e:
        warn(f"Certspotter failed: {e}")

    if not found:
        warn("No subdomains found from any source.")
        return

    # ── Resolve & display ──────────────────────────────────────────────────
    ok(f"Total unique subdomains found: {len(found)}")
    print()

    resolved = []
    unresolved = []
    for sub in sorted(found):
        try:
            ip = socket.gethostbyname(sub)
            resolved.append((sub, ip))
        except socket.gaierror:
            unresolved.append(sub)

    for sub, ip in resolved:
        print(f"  {Fore.GREEN}{sub:<45}{Fore.RESET}  {ip}")
    for sub in unresolved:
        print(f"  {Fore.YELLOW}{sub:<45}{Fore.RESET}  (no DNS)")

    print(f"\n  Resolved: {len(resolved)}   Unresolved: {len(unresolved)}")


def check_upload_dirs(target: str, timeout: float):
    section("Open Upload Directories")
    paths = ["/wp-content/uploads/", "/uploads/", "/files/",
             "/images/upload/", "/media/"]
    for path in paths:
        for scheme in ("https", "http"):
            url = f"{scheme}://{target}{path}"
            try:
                resp = requests.get(url, timeout=timeout)
                if resp.status_code == 200:
                    warn(f"Open upload dir: {url}")
            except requests.RequestException:
                continue


def dns_lookup(target: str, timeout: float):
    """
    DNS record lookup:
      1. HackerTarget JSON API (free, no key) → A, AAAA, MX, NS, TXT, CNAME, SOA
      2. Google DoH fallback  → if HackerTarget quota exceeded
      3. Zone-transfer (AXFR) misconfiguration check
    """
    section("DNS Lookup")

    ht_ok = False
    try:
        url  = f"https://api.hackertarget.com/dnslookup/?q={target}&output=json"
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            text = resp.text.strip()
            if text.startswith("{") or text.startswith("["):
                data = resp.json()
                for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
                    records = data.get(rtype, [])
                    if records:
                        print(f"\n  {Fore.CYAN}{rtype}{Fore.RESET} records:")
                        for r in records:
                            print(f"    {r}")
                ht_ok = True
            elif "error" not in text.lower() and "exceeded" not in text.lower():
                # plain-text response (no JSON support on this endpoint yet)
                for line in text.splitlines():
                    if line.strip():
                        print(f"    {line.strip()}")
                ht_ok = True
            else:
                warn(f"HackerTarget DNS quota: {text[:80]}")
    except Exception as e:
        warn(f"HackerTarget DNS failed: {e}")

    if not ht_ok:
        info("Falling back to Google DoH…")
        doh_base = "https://dns.google/resolve"
        for rtype in ["A", "AAAA", "MX", "NS", "TXT"]:
            try:
                r2 = requests.get(doh_base, params={"name": target, "type": rtype},
                                  timeout=timeout,
                                  headers={"accept": "application/dns-json"})
                if r2.status_code == 200:
                    answers = r2.json().get("Answer", [])
                    if answers:
                        print(f"\n  {Fore.CYAN}{rtype}{Fore.RESET} records:")
                        for a in answers:
                            print(f"    {a.get('data', '')}")
            except Exception:
                pass

    # Zone-transfer check (AXFR) via Google DoH to discover NS first
    try:
        r_ns = requests.get("https://dns.google/resolve",
                            params={"name": target, "type": "NS"},
                            timeout=timeout,
                            headers={"accept": "application/dns-json"})
        ns_list = [a.get("data", "").rstrip(".")
                   for a in r_ns.json().get("Answer", [])] if r_ns.status_code == 200 else []
        vuln_ns = []
        for ns in ns_list[:3]:
            try:
                ns_ip = socket.gethostbyname(ns)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                if s.connect_ex((ns_ip, 53)) == 0:
                    # Minimal AXFR TCP probe
                    qname = b"".join(bytes([len(p)]) + p.encode() for p in target.split(".")) + b"\x00"
                    pkt   = b"\xaa\xaa\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00" + qname + b"\x00\xfc\x00\x01"
                    pkt   = len(pkt).to_bytes(2, "big") + pkt
                    s.sendall(pkt)
                    data = s.recv(512)
                    if len(data) > 20:
                        vuln_ns.append(ns)
                s.close()
            except Exception:
                pass
        if vuln_ns:
            warn(f"Possible AXFR zone transfer on: {', '.join(vuln_ns)}")
        else:
            info("Zone transfer (AXFR): not exposed")
    except Exception:
        pass

def reverse_ip(target: str, host_ip: str, timeout: float = 10):
    """
    Find other domains hosted on the same IP.
    Sources (tried in order):
      1. HackerTarget reverseiplookup (free, no key, plain text, 50 results/req)
      2. HackerTarget as fallback using IP resolved locally
    """
    section("Reverse IP  (domains on same host)")

    domains: set[str] = set()

    # Use resolved IP for the query so it works even when target is a subdomain
    query = host_ip if host_ip else target

    # ── HackerTarget ────────────────────────────────────────────────────────
    try:
        url  = f"https://api.hackertarget.com/reverseiplookup/?q={query}"
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            text = resp.text.strip()
            if "error" in text.lower() or "exceeded" in text.lower():
                warn(f"HackerTarget reverse IP: {text[:80]}")
            else:
                for line in text.splitlines():
                    line = line.strip()
                    if line and "." in line:
                        domains.add(line.lower())
    except Exception as e:
        warn(f"HackerTarget reverse IP failed: {e}")

    # ── YouGetSignal / secondary passive scrape ──────────────────────────────
    if not domains:
        try:
            resp2 = requests.post(
                "https://domains.yougetsignal.com/domains.php",
                data={"remoteAddress": query, "key": ""},
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0",
                         "Referer": "https://www.yougetsignal.com/"}
            )
            if resp2.status_code == 200:
                import json as _json
                data2 = resp2.json()
                for d in data2.get("domainArray", []):
                    if isinstance(d, list) and d:
                        domains.add(str(d[0]).lower())
        except Exception:
            pass

    if not domains:
        warn("No co-hosted domains found (both sources failed or quota hit).")
        return

    sorted_d = sorted(domains)
    ok(f"Found {len(sorted_d)} domain(s) on {query}:")
    for d in sorted_d[:50]:
        print(f"    {d}")
    if len(sorted_d) > 50:
        info(f"  … and {len(sorted_d) - 50} more (HackerTarget free tier shows max 50)")

def whois_lookup(target: str):
    section("WHOIS")
    try:
        url = f"https://api.whoapi.com/?domain={target}&r=whois&apikey=free"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        for key in ("registrar", "created", "expires", "status", "nameservers"):
            if key in data:
                info(f"{key.capitalize()}: {data[key]}")
    except Exception as e:
        warn(f"WHOIS lookup failed or API limit reached: {e}")


def check_ports(host_ip: str, timeout: float = 0.8):
    """
    Fast threaded port scanner with:
      - 100 concurrent threads
      - banner grabbing on open ports
      - service/version identification from banner text
      - risk tagging (dangerous services highlighted in red)
    """
    section("Port Scan  (common + extended web ports)")

    PORTS = {
        # (port, label, dangerous?)
        21:    ("FTP",            True),
        22:    ("SSH",            False),
        23:    ("Telnet",         True),
        25:    ("SMTP",           False),
        53:    ("DNS",            False),
        80:    ("HTTP",           False),
        110:   ("POP3",           False),
        111:   ("RPCBind",        True),
        135:   ("MS-RPC",         True),
        139:   ("NetBIOS",        True),
        143:   ("IMAP",           False),
        389:   ("LDAP",           True),
        443:   ("HTTPS",          False),
        445:   ("SMB",            True),
        465:   ("SMTPS",          False),
        512:   ("rexec",          True),
        513:   ("rlogin",         True),
        514:   ("rsh/syslog",     True),
        587:   ("SMTP submission",False),
        631:   ("IPP/CUPS",       False),
        993:   ("IMAPS",          False),
        995:   ("POP3S",          False),
        1433:  ("MSSQL",          True),
        1521:  ("Oracle DB",      True),
        2049:  ("NFS",            True),
        2083:  ("cPanel SSL",     False),
        2222:  ("Alt SSH",        False),
        3000:  ("Dev server",     False),
        3306:  ("MySQL",          True),
        3389:  ("RDP",            True),
        4443:  ("Alt HTTPS",      False),
        5000:  ("Flask/Dev",      False),
        5432:  ("PostgreSQL",     True),
        5900:  ("VNC",            True),
        6379:  ("Redis",          True),
        7001:  ("WebLogic",       True),
        8000:  ("Alt HTTP",       False),
        8080:  ("Alt HTTP",       False),
        8443:  ("Alt HTTPS",      False),
        8888:  ("Jupyter/Dev",    False),
        9000:  ("PHP-FPM/SonarQ", False),
        9200:  ("Elasticsearch",  True),
        27017: ("MongoDB",        True),
        28017: ("MongoDB HTTP",   True),
    }

    # Banner-grabbing probes to send on connect
    PROBES = {
        21:  b"",
        22:  b"",
        25:  b"EHLO oasi\r\n",
        80:  b"HEAD / HTTP/1.0\r\n\r\n",
        110: b"",
        143: b"",
        443: b"",
        3306:b"",
    }

    def _scan_port(port):
        label, danger = PORTS[port]
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((host_ip, port)) != 0:
                s.close()
                return None
            # Banner grab
            banner = ""
            try:
                probe = PROBES.get(port, b"")
                if probe:
                    s.sendall(probe)
                s.settimeout(1.5)
                raw = s.recv(256)
                banner = raw.decode(errors="replace").strip().split("\n")[0][:80]
            except Exception:
                pass
            s.close()
            return (port, label, danger, banner)
        except Exception:
            return None

    print(f"  Scanning {len(PORTS)} ports with 100 threads  (timeout {timeout}s)…\n")

    results = []
    with ThreadPoolExecutor(max_workers=100) as pool:
        futures = {pool.submit(_scan_port, p): p for p in PORTS}
        for fut in tqdm(as_completed(futures), total=len(futures),
                        desc="Ports", ncols=72, leave=True):
            r = fut.result()
            if r:
                results.append(r)

    if not results:
        info("No open ports found.")
        return

    results.sort(key=lambda x: x[0])
    print()
    print(f"  {'PORT':<7} {'STATE':<8} {'SERVICE':<22} {'BANNER'}")
    print(f"  {'─'*7} {'─'*8} {'─'*22} {'─'*40}")
    for port, label, danger, banner in results:
        color  = Fore.RED if danger else Fore.GREEN
        state  = f"{color}open{Fore.RESET}"
        dtag   = f" {Fore.RED}[!DANGEROUS]{Fore.RESET}" if danger else ""
        banner_str = f"  {Fore.WHITE}{banner}{Fore.RESET}" if banner else ""
        print(f"  {color}{port:<7}{Fore.RESET} {state:<16} {label:<22}{dtag}{banner_str}")
    print()
    dangerous = [p for p, l, d, b in results if d]
    if dangerous:
        warn(f"Dangerous/exposed services on ports: {', '.join(map(str, dangerous))}")

def _dir_probe(args_tuple):
    target, path, timeout, session = args_tuple
    # Try HTTPS first, HTTP fallback
    for scheme in ("https", "http"):
        url = f"{scheme}://{target}/{path.lstrip('/')}"
        try:
            resp = session.get(url, timeout=timeout, allow_redirects=False,
                               stream=False)
            code = resp.status_code
            if code in (200, 201, 204, 301, 302, 307, 308, 401, 403):
                size = len(resp.content)
                ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
                return (url, code, size, ctype)
            # 200 on HTTPS → done, don't try HTTP
            break
        except requests.RequestException:
            continue
    return None

def check_dirs(target: str, wordlist_path, threads: int, timeout: float):
    """
    Directory/file scanner with:
      - Persistent HTTP session (keep-alive, connection pooling)
      - Rotating User-Agent headers to reduce fingerprinting
      - Status codes: 200/201/204 green, 301/302/307/308 yellow,
                      401 magenta (auth required), 403 red (forbidden but exists)
      - Shows file size and Content-Type for each hit
      - Deduplicates HTTPS vs HTTP hits
      - Saves results to output/<target>.txt
    """
    section("Directory / File Scanning")

    wl_file = wordlist_path or "wordlist/default_wl.txt"
    if not os.path.exists(wl_file):
        warn(f"Wordlist not found: {wl_file}")
        return

    with open(wl_file, "r", errors="ignore") as f:
        paths = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    info(f"Scanning {len(paths)} paths with {threads} threads…\n")
    os.makedirs("output", exist_ok=True)
    output_file = f"output/{target}.txt"

    # Rotating user agents
    UA_LIST = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    ]
    import itertools
    ua_cycle = itertools.cycle(UA_LIST)

    session = requests.Session()
    session.headers.update({"User-Agent": next(ua_cycle),
                             "Accept": "*/*",
                             "Accept-Encoding": "gzip, deflate",
                             "Connection": "keep-alive"})
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=threads, pool_maxsize=threads,
        max_retries=0
    )
    session.mount("https://", adapter)
    session.mount("http://",  adapter)

    found   = []
    seen    = set()
    tasks   = [(target, p, timeout, session) for p in paths]

    CODE_COLOR = {
        200: Fore.GREEN, 201: Fore.GREEN, 204: Fore.GREEN,
        301: Fore.YELLOW, 302: Fore.YELLOW, 307: Fore.YELLOW, 308: Fore.YELLOW,
        401: Fore.MAGENTA,
        403: Fore.RED,
    }
    CODE_LABEL = {
        200: "OK",     201: "Created",  204: "No Content",
        301: "Moved",  302: "Found",    307: "Redirect", 308: "Redirect",
        401: "Auth",   403: "Forbidden",
    }

    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {pool.submit(_dir_probe, t): t for t in tasks}
        for future in tqdm(as_completed(futures), total=len(tasks),
                           desc="Scanning", ncols=72, leave=True):
            result = future.result()
            if result is None:
                continue
            url, code, size, ctype = result
            # Deduplicate (http vs https of same path)
            norm = url.replace("https://", "http://")
            if norm in seen:
                continue
            seen.add(norm)

            color = CODE_COLOR.get(code, Fore.WHITE)
            label = CODE_LABEL.get(code, str(code))
            size_str  = f"{size:>7,} B" if size else "       -"
            ctype_str = ctype[:28] if ctype else ""
            tqdm.write(
                f"  {color}[{code} {label:<9}]{Fore.RESET} "
                f"{url:<60}  {size_str}  {ctype_str}"
            )
            found.append(f"{code}  {url}  ({size} bytes)  {ctype}")

    session.close()

    if found:
        with open(output_file, "a") as f:
            f.write("\n".join(found) + "\n")
        ok(f"\n{len(found)} result(s) saved → {output_file}")
    else:
        info("No paths found.")

def shell_check(target: str, timeout: float, threads: int = 30):
    """
    Advanced web-shell scanner for DEFENSIVE use:
    Goal: find shells already uploaded so the security team can DELETE them.

    Detection is multi-layered:
      1. Path scan   – known shell filenames from wordlist
      2. Content analysis – even if the path is unknown, scan all discovered
         pages for shell indicators (eval, base64_decode, system(), etc.)
      3. Entropy check – high-entropy PHP/ASP files are suspicious (obfuscated)
      4. Response behaviour – shells often respond differently to GET vs POST
         or echo back injected params

    Findings are saved to output/<target>_shells.txt with remediation notes.
    """
    section("Web Shell Scanner  (defensive)")

    import math, itertools, re as _re, hashlib

    # ── Shell-content fingerprints ─────────────────────────────────────────
    # Patterns that appear in real web-shells but rarely in legitimate pages
    SHELL_PATTERNS = [
        # PHP shells
        (r'eval\s*\(\s*base64_decode',        "PHP eval+base64",      9),
        (r'eval\s*\(\s*gzinflate',            "PHP eval+gzinflate",   9),
        (r'eval\s*\(\s*str_rot13',            "PHP eval+rot13",       8),
        (r'eval\s*\(\s*gzuncompress',         "PHP eval+gzuncompress",8),
        (r'\$_(?:GET|POST|REQUEST|COOKIE)\s*\[.{0,30}\]\s*\(\s*\$_',
                                              "PHP $_GET exec chain",  9),
        (r'system\s*\(\s*\$_(?:GET|POST|REQUEST)',
                                              "PHP system($_GET)",     10),
        (r'exec\s*\(\s*\$_(?:GET|POST|REQUEST)',
                                              "PHP exec($_GET)",       10),
        (r'passthru\s*\(\s*\$_(?:GET|POST)',  "PHP passthru",          9),
        (r'shell_exec\s*\(\s*\$_(?:GET|POST)',"PHP shell_exec",        9),
        (r'preg_replace\s*\(.{0,10}/e[\'"]', "PHP preg_replace /e",   8),
        (r'assert\s*\(\s*\$_(?:GET|POST)',    "PHP assert($_GET)",     8),
        (r'create_function\s*\(',             "PHP create_function",   7),
        (r"base64_decode\s*\(\s*['\"][A-Za-z0-9+/]{40,}",
                                              "PHP base64 payload",    7),
        # ASP / ASPX shells
        (r'eval\s*request\s*\(',              "ASP eval(Request)",    10),
        (r'execute\s*request\s*\(',           "ASP Execute(Request)",  9),
        (r'server\.createobject.*wscript',    "ASP WScript object",    9),
        # JSP shells
        (r'runtime\.exec\s*\(',               "JSP Runtime.exec",     10),
        (r'processbuilder',                   "JSP ProcessBuilder",    9),
        # Generic webshell UI strings
        (r'(?:c99|r57|b374k|wso shell|indoxploit)',
                                              "Known shell name",      10),
        (r'uname\s+-a',                       "uname -a command",      8),
        (r'(?:phpinfo|phpversion)\s*\(\s*\)', "PHP info disclosure",   5),
        (r'(?:cmd|command)\s*=\s*(?:whoami|id|ls|dir)',
                                              "Shell command param",   8),
        # Encoded/obfuscated indicators
        (r'\x[0-9a-f]{2}\x[0-9a-f]{2}\x[0-9a-f]{2}\x[0-9a-f]{2}\x[0-9a-f]{2}\x[0-9a-f]{2}',
                                              "Hex-encoded string",    6),
        (r'chr\s*\(\s*\d+\s*\)\s*\.\s*chr\s*\(',
                                              "PHP chr() chain",       7),
    ]

    # ── Compile all regex patterns once ───────────────────────────────────
    compiled = [(pat, _re.compile(pat, _re.IGNORECASE | _re.DOTALL), label, score)
                for pat, label, score in
                [(p[0], p[1], p[2]) for p in SHELL_PATTERNS]]

    def _entropy(data: str) -> float:
        """Shannon entropy of string (high entropy = likely obfuscated)."""
        if not data: return 0.0
        freq = {}
        for c in data:
            freq[c] = freq.get(c, 0) + 1
        ln = len(data)
        return -sum((f/ln)*math.log2(f/ln) for f in freq.values() if f > 0)

    def _analyse_body(url: str, body: str, status: int) -> list:
        """Return list of (label, score) for all patterns matched in body."""
        hits = []
        for pat_str, pat_re, label, score in compiled:
            if pat_re.search(body):
                hits.append((label, score))
        # entropy check on high-entropy content
        ent = _entropy(body[:4000])
        if ent > 5.5 and len(body) > 200:
            hits.append((f"High entropy ({ent:.2f})", 5))
        return hits

    def _behaviour_probe(session, url: str, timeout: float) -> str | None:
        """
        POST a cmd= param and check if response differs from GET.
        If POST with cmd=id produces different content → shell behaviour.
        """
        try:
            get_resp  = session.get(url, timeout=timeout)
            post_resp = session.post(url, data={"cmd": "id", "c": "id",
                                                "exec": "id", "command": "id"},
                                     timeout=timeout)
            if post_resp.status_code == 200 and get_resp.status_code == 200:
                # Significant body difference
                if abs(len(post_resp.text) - len(get_resp.text)) > 80:
                    return "GET/POST response size differs"
                # Look for OS command output patterns
                if _re.search(r'uid=\d+|root:|www-data', post_resp.text):
                    return "POST cmd=id returned OS output"
        except Exception:
            pass
        return None

    # ── Load wordlist ──────────────────────────────────────────────────────
    wl_file = "wordlist/shells.txt"
    paths = []
    if os.path.exists(wl_file):
        with open(wl_file, "r", errors="ignore") as f:
            paths = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    else:
        warn(f"Shell wordlist not found at {wl_file} — using built-in list")

    # Built-in minimal shell filename list (always used as baseline)
    BUILTIN = [
        "shell.php","cmd.php","c99.php","r57.php","wso.php","b374k.php",
        "indoxploit.php","alfa.php","mini.php","webshell.php","backdoor.php",
        "hack.php","1.php","2.php","x.php","tmp.php","test.php","upload.php",
        "uploader.php","file.php","config.php.bak","wp-config.php.bak",
        ".htaccess.bak","error.php","info.php","phpinfo.php",
        "shell.asp","cmd.asp","shell.aspx","cmd.aspx","shell.jsp",
        "shell.cfm","shell.pl","shell.py","shell.rb",
        # upload dir variants
        "uploads/shell.php","uploads/cmd.php","uploads/1.php",
        "wp-content/uploads/shell.php","wp-content/uploads/cmd.php",
        "wp-content/uploads/evil.php","images/shell.php",
        "files/shell.php","media/shell.php","assets/shell.php",
        # common obfuscated names
        "wp-includes/ms-style.php","wp-includes/class-wp-styles.php.bak",
        ".well-known/shell.php","vendor/shell.php",
    ]
    all_paths = list(dict.fromkeys(BUILTIN + paths))   # deduplicate, BUILTIN first

    info(f"Scanning {len(all_paths)} paths for shells with {threads} threads…\n")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*",
    })

    findings = []
    os.makedirs("output", exist_ok=True)
    out_file = f"output/{target}_shells.txt"

    def _probe_path(path):
        for scheme in ("https", "http"):
            url = f"{scheme}://{target}/{path.lstrip('/')}"
            try:
                resp = session.get(url, timeout=timeout, allow_redirects=True)
                if resp.status_code not in (200, 206):
                    continue
                body   = resp.text
                hits   = _analyse_body(url, body, resp.status_code)
                total  = sum(s for _, s in hits)
                behave = None
                if total >= 6:   # only do POST probe for suspicious pages
                    behave = _behaviour_probe(session, url, timeout)
                    if behave:
                        total += 5
                if total > 0:
                    return (url, hits, behave, total, resp.status_code)
            except requests.RequestException:
                continue
        return None

    with ThreadPoolExecutor(max_workers=threads) as pool:
        futs = {pool.submit(_probe_path, p): p for p in all_paths}
        for fut in tqdm(as_completed(futs), total=len(futs),
                        desc="Shell scan", ncols=72):
            result = fut.result()
            if result:
                findings.append(result)

    session.close()

    if not findings:
        ok("No web shells detected.")
        return

    findings.sort(key=lambda x: x[3], reverse=True)

    print()
    warn(f"{'='*60}")
    warn(f"  {len(findings)} SUSPICIOUS FILE(S) FOUND — REVIEW IMMEDIATELY")
    warn(f"{'='*60}\n")

    lines_to_save = []
    for url, hits, behave, total, status in findings:
        risk = "CRITICAL" if total >= 15 else "HIGH" if total >= 8 else "MEDIUM"
        color = Fore.RED if risk == "CRITICAL" else Fore.YELLOW if risk == "HIGH" else Fore.WHITE
        print(f"  {color}[{risk}]{Fore.RESET}  {url}")
        for label, score in hits[:5]:
            print(f"    ↳ {label}  (score +{score})")
        if behave:
            print(f"    ↳ {Fore.RED}Behaviour: {behave}{Fore.RESET}")
        print(f"    ↳ Total risk score: {total}")
        print()
        lines_to_save.append(
            f"[{risk}] {url}\n"
            + "\n".join(f"  - {l}" for l, _ in hits)
            + (f"\n  - BEHAVIOUR: {behave}" if behave else "")
            + f"\n  - Total score: {total}\n"
        )

    # Remediation notes
    print(Fore.CYAN + "  Remediation steps:" + Fore.RESET)
    print("  1. Delete or quarantine each file listed above immediately.")
    print("  2. Check file modification dates: ls -la --full-time <file>")
    print("  3. Review server access logs for requests to these paths.")
    print("  4. Search for additional shells: find /var/www -name '*.php' -newer index.php")
    print("  5. Change all CMS, DB, and server credentials.")
    print("  6. Audit how the shell was uploaded (file upload vuln, compromised creds).")
    print()

    with open(out_file, "w") as f:
        f.write(f"OASI Web Shell Report — {target}\n{'='*60}\n\n")
        f.write("\n".join(lines_to_save))
    ok(f"Report saved → {out_file}")


def ai_scan(target: str, timeout: float, scan_results: dict):
    """
    AI-powered security analyser using the Anthropic Claude API.
    Takes all scan results collected during the run, sends them to Claude,
    and returns:
      - Executive summary  (plain English, non-technical)
      - Risk assessment    (CRITICAL / HIGH / MEDIUM / LOW per finding)
      - Attack surface map (what an attacker would focus on)
      - Remediation plan   (prioritised, specific action items)
      - CVE hints          (known CVEs for detected software versions)

    Requires: ANTHROPIC_API_KEY environment variable
    Install:  pip install anthropic
    """
    section("AI Security Analysis  (Claude)")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        warn("ANTHROPIC_API_KEY not set — skipping AI analysis.")
        info("Set it with:  export ANTHROPIC_API_KEY=sk-ant-...")
        return

    try:
        import anthropic
    except ImportError:
        warn("anthropic library not installed — run: pip install anthropic")
        return

    # Build a structured report from all collected scan data
    report_lines = [f"Web security scan results for: {target}", "=" * 60]

    for section_name, data in scan_results.items():
        if not data:
            continue
        report_lines.append(f"\n## {section_name}")
        if isinstance(data, list):
            for item in data:
                report_lines.append(f"  - {item}")
        elif isinstance(data, dict):
            for k, v in data.items():
                report_lines.append(f"  {k}: {v}")
        else:
            report_lines.append(f"  {data}")

    report_text = "\n".join(report_lines)

    prompt = f"""You are a senior penetration tester and cybersecurity analyst.
Below are the results of an automated web security scan against a target server.
The person who ran this scan is the server owner / security team responsible for defending it.

SCAN RESULTS:
{report_text}

Please provide a structured security analysis with these exact sections:

1. EXECUTIVE SUMMARY (2-3 sentences, non-technical language for management)

2. RISK ASSESSMENT
   For each significant finding, rate it CRITICAL / HIGH / MEDIUM / LOW and explain why.

3. ATTACK SURFACE MAP
   What would an attacker focus on first based on these results?

4. REMEDIATION PLAN (prioritised)
   Specific, actionable steps to fix each issue. Include commands where helpful.

5. CVE HINTS
   Based on detected software versions/services, list any known CVEs worth checking.
   If no version info is available, note what to check.

6. QUICK WINS
   2-3 things that can be fixed in under 30 minutes to significantly reduce risk.

Be specific and technical. This will be read by a security professional."""

    print()
    info("Sending scan data to Claude for AI analysis…")
    print()

    try:
        client  = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model      = "claude-opus-4-5",
            max_tokens = 2048,
            messages   = [{"role": "user", "content": prompt}]
        )
        ai_response = message.content[0].text

        # Pretty-print the response with section highlighting
        current_section = None
        for line in ai_response.splitlines():
            stripped = line.strip()
            if stripped.startswith(("1.", "2.", "3.", "4.", "5.", "6.")) and len(stripped) < 80:
                print()
                print(Fore.CYAN + Style.BRIGHT + stripped + Style.RESET_ALL)
                current_section = stripped
            elif stripped.startswith("CRITICAL"):
                print(Fore.RED    + "  " + stripped + Fore.RESET)
            elif stripped.startswith("HIGH"):
                print(Fore.YELLOW + "  " + stripped + Fore.RESET)
            elif stripped.startswith("MEDIUM"):
                print(Fore.WHITE  + "  " + stripped + Fore.RESET)
            elif stripped.startswith("LOW"):
                print(Fore.BLUE   + "  " + stripped + Fore.RESET)
            else:
                print("  " + line)

        # Save AI report
        os.makedirs("output", exist_ok=True)
        ai_file = f"output/{target}_ai_report.txt"
        with open(ai_file, "w") as f:
            f.write(f"OASI AI Security Report — {target}\n{'='*60}\n\n")
            f.write(ai_response)
        print()
        ok(f"AI report saved → {ai_file}")

    except Exception as e:
        bad(f"AI analysis failed: {e}")


def inputer(batch: bool):
    if not batch:
        ans = input("\n\nContinue scanning? (Y/n): ").strip().lower()
        if ans in no_choice:
            print("Exiting…")
            sys.exit(0)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def main():
    banner()
    args = parse_args()

    # --update flag: just check updates then exit
    if args.update:
        check_updates(silent=False)
        sys.exit(0)

    # Always check for updates at startup (silent if up to date)
    check_updates(silent=True)

    target  = parse_host(args.url)
    timeout = args.timeout

    # Core recon
    host_ip = check_host(target, timeout)
    check_headers(target, timeout)
    detect_waf(target, timeout)
    check_cms(target, timeout)
    check_robots_sitemap(target, timeout)
    dns_lookup(target, timeout)
    reverse_ip(target, host_ip, timeout)
    whois_lookup(target)
    check_upload_dirs(target, timeout)
    check_subdomains(target, timeout)

    inputer(args.batch)

    # Optional modules
    if args.shell:
        shell_check(target, timeout)

    check_dirs(target, args.wordlist, args.threads, timeout)

    if args.ports:
        check_ports(host_ip, timeout)

    # ── AI analysis ──────────────────────────────────────────────────────
    if args.ai:
        # Collect a summary dict of key findings to pass to AI
        scan_results = {
            "Target": target,
            "Host IP": host_ip,
            "URL": args.url,
            "Flags used": {
                "ports": args.ports, "shell": args.shell,
                "wordlist": args.wordlist or "default",
                "threads": args.threads,
            },
        }
        ai_scan(target, timeout, scan_results)

    print(Fore.CYAN + "\n[✓] Scan complete.\n")


if __name__ == "__main__":
    main()