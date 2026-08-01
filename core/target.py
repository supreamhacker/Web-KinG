"""
Web KinG - Target & Authorization Handling
============================================
Web KinG refuses to run anything until the operator explicitly confirms
they are authorized to test the given target. This is a deliberate,
non-optional gate — it stays in place even in --yes automation mode
(you still have to pass --yes, which is itself an explicit statement
of authorization).
"""
import re


def validate_target(target: str) -> bool:
    """Basic sanity check for a hostname / IP / CIDR / URL."""
    patterns = [
        r"^https?://\S+$",
        r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$",
        r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    ]
    return any(re.match(p, target) for p in patterns)


def confirm_authorization(target: str, assume_yes: bool = False) -> bool:
    print("=" * 62)
    print(" WEB KING — AUTHORIZATION CHECK")
    print("=" * 62)
    print(f" Target: {target}")
    print(" Only scan systems you own or have written permission to")
    print(" test (e.g. a signed pentest/bug-bounty scope). Unauthorized")
    print(" scanning is illegal in most jurisdictions.")
    print("=" * 62)

    if assume_yes:
        print(" [--yes supplied: authorization confirmed non-interactively]")
        return True

    ans = input(" Type 'yes' to confirm you are authorized to test this target: ").strip().lower()
    return ans == "yes"
