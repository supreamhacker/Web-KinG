#!/usr/bin/env python3
"""
Web KinG — Pentest Recon-to-Report Orchestrator
==================================================
A single CLI that drives already-installed security tools (nmap, amass,
subfinder, nuclei, gobuster, sqlmap, hydra, john, radare2, ...) and
compiles their output into one HTML/JSON report.

Web KinG does not implement any scanning/exploitation logic itself —
every module is a thin, logged subprocess wrapper around the real
tool, which must already be installed and on PATH.

USE ONLY AGAINST TARGETS YOU OWN OR ARE EXPLICITLY AUTHORIZED TO TEST.

Usage examples
--------------
  # Recon only against a domain
  ./webking.py recon -t example.com --domain

  # Full recon + web app pass against a URL, auto-confirm authorization
  ./webking.py full -t https://example.com --domain --wordlist /usr/share/wordlists/dirb/common.txt --yes

  # Just generate a report from a previous run's raw logs (see report.py)
  ./webking.py recon -t 10.10.10.5 --fast -o results/hostA
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.executor import Executor
from core.target import validate_target, confirm_authorization
from core.report import generate_report
from modules import recon, webapp, auth, creds, binary


BANNER = r"""
 __      __       _        _  ___         ____
 \ \    / /  ___  | |__    | |/ (_)  _ _   / ___|
  \ \/\/ /  / -_) | '_ \   | ' <| | | ' \  \___ \
   \_/\_/   \___| |_.__/   |_|\_\_| |_||_| |___/   Recon -> Report
"""


def build_parser():
    p = argparse.ArgumentParser(prog="webking", description="Web KinG pentest orchestrator")
    p.add_argument("-t", "--target", required=True, help="Target IP / domain / URL")
    p.add_argument("-o", "--output", default="webking_output", help="Output directory")
    p.add_argument("--domain", action="store_true", help="Treat target as a domain (enables DNS/OSINT modules)")
    p.add_argument("--fast", action="store_true", help="Use rustscan instead of nmap -p-")
    p.add_argument("--wordlist", default="/usr/share/wordlists/dirb/common.txt", help="Wordlist for content discovery")
    p.add_argument("--yes", action="store_true", help="Skip interactive authorization prompt (you are still asserting authorization)")
    p.add_argument("--dry-run", action="store_true", help="Print commands without executing them")

    sub = p.add_subparsers(dest="mode", required=True)
    sub.add_parser("recon", help="Network + DNS + OSINT recon")
    sub.add_parser("web", help="Web application content discovery + scanners")
    sub.add_parser("full", help="Recon + Web, then generate report")
    return p


def main():
    # Allow the mode keyword (recon/web/full) anywhere on the command line,
    # since global flags live on the parent parser but people naturally
    # type `webking full -t ...` with the mode first.
    raw = sys.argv[1:]
    modes = {"recon", "web", "full"}
    mode_tokens = [a for a in raw if a in modes]
    if mode_tokens:
        rest = [a for a in raw if a not in modes]
        sys.argv = [sys.argv[0]] + rest + mode_tokens[:1]

    args = build_parser().parse_args()
    print(BANNER)

    if not validate_target(args.target):
        print(f"[!] '{args.target}' doesn't look like a valid IP/domain/URL. Continuing anyway, but double-check it.")

    if not confirm_authorization(args.target, assume_yes=args.yes):
        print("[!] Authorization not confirmed. Exiting.")
        sys.exit(1)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    executor = Executor(log_dir=str(out_dir / "logs"), dry_run=args.dry_run)

    all_results = {}

    if args.mode in ("recon", "full"):
        print("\n[*] Running reconnaissance modules...")
        all_results["Recon"] = recon.run_all(
            executor, args.target, str(out_dir), is_domain=args.domain, fast=args.fast
        )

    if args.mode in ("web", "full"):
        url = args.target if args.target.startswith("http") else f"http://{args.target}"
        print("\n[*] Running web application modules...")
        all_results["Web Application"] = webapp.run_all(executor, url, args.wordlist, str(out_dir))

    print("\n[*] Generating report...")
    report_path = generate_report(args.target, all_results, output_dir=str(out_dir))
    print(f"\n[+] Done. Report: {report_path}")
    print(f"[+] Raw logs:      {out_dir / 'logs'}")
    print(f"[+] JSON summary:  {out_dir / 'report.json'}")

    print("\nNote: --full intentionally does NOT run the auth/creds/binary")
    print("modules (hydra, john, gdb, etc.) — those need explicit target-")
    print("specific parameters and are invoked separately, see modules/.")


if __name__ == "__main__":
    main()
