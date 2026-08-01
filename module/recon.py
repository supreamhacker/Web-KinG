"""
Web KinG - Reconnaissance Module
===================================
Network discovery, subdomain/DNS enumeration, and OSINT.
Nothing here touches credentials or attempts exploitation —
it's pure information gathering.
"""


def run_port_scan(executor, target, output_dir, fast=False):
    results = {}
    if fast:
        results["rustscan"] = executor.run(
            "rustscan", ["-a", target, "--", "-sV", "-sC"], timeout=600
        )
    else:
        results["nmap"] = executor.run(
            "nmap",
            ["-sV", "-sC", "-T4", "-p-", "-oN", f"{output_dir}/nmap_full.txt", target],
            timeout=1800,
        )
        results["masscan"] = executor.run(
            "masscan",
            ["-p1-65535", "--rate=1000", "-oG", f"{output_dir}/masscan.txt", target],
            timeout=900,
        )
    return results


def run_dns_recon(executor, domain, output_dir):
    results = {}
    results["subfinder"] = executor.run(
        "subfinder", ["-d", domain, "-silent", "-o", f"{output_dir}/subfinder.txt"], timeout=600
    )
    results["amass"] = executor.run(
        "amass", ["enum", "-passive", "-d", domain, "-o", f"{output_dir}/amass.txt"], timeout=900
    )
    results["fierce"] = executor.run("fierce", ["--domain", domain], timeout=300)
    results["dnsenum"] = executor.run("dnsenum", [domain], timeout=300)
    return results


def run_osint(executor, domain, output_dir):
    results = {}
    results["theharvester"] = executor.run(
        "theHarvester",
        ["-d", domain, "-b", "all", "-f", f"{output_dir}/theharvester"],
        timeout=600,
    )
    return results


def run_vuln_templates(executor, target, output_dir):
    """Template-based, non-intrusive vulnerability signature scanning."""
    results = {}
    results["nuclei"] = executor.run(
        "nuclei", ["-target", target, "-o", f"{output_dir}/nuclei.txt"], timeout=1200
    )
    return results


def run_autorecon(executor, target, output_dir):
    return {"autorecon": executor.run("autorecon", [target, "-o", output_dir], timeout=3600)}


def run_internal_enum(executor, target, output_dir):
    """Internal/AD-style host enumeration (assumes network access + authorization)."""
    return {
        "enum4linux-ng": executor.run(
            "enum4linux-ng", ["-A", target, "-oY", f"{output_dir}/enum4linux.yaml"], timeout=600
        )
    }


def run_all(executor, target, output_dir, is_domain, fast=False):
    """Runs the full recon suite and returns a merged results dict."""
    results = {}
    results.update(run_port_scan(executor, target, output_dir, fast=fast))
    if is_domain:
        results.update(run_dns_recon(executor, target, output_dir))
        results.update(run_osint(executor, target, output_dir))
    results.update(run_vuln_templates(executor, target, output_dir))
    return results
