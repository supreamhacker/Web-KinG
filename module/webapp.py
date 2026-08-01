"""
Web KinG - Web Application Module
====================================
Content discovery, tech fingerprinting, and web scanners. sqlmap/dalfox
are run in their safe defaults (no --risk/--level escalation, no
destructive --os-shell/--sql-shell) — this wraps the scanners in their
detection mode, it does not add any custom exploitation logic on top.
"""


def run_content_discovery(executor, url, wordlist, output_dir):
    results = {}
    results["gobuster"] = executor.run(
        "gobuster", ["dir", "-u", url, "-w", wordlist, "-o", f"{output_dir}/gobuster.txt"], timeout=900
    )
    results["feroxbuster"] = executor.run(
        "feroxbuster", ["-u", url, "-w", wordlist, "-o", f"{output_dir}/feroxbuster.txt"], timeout=900
    )
    results["dirsearch"] = executor.run(
        "dirsearch", ["-u", url, "-w", wordlist, "-o", f"{output_dir}/dirsearch.txt"], timeout=900
    )
    results["ffuf"] = executor.run(
        "ffuf", ["-u", f"{url}/FUZZ", "-w", wordlist, "-o", f"{output_dir}/ffuf.json"], timeout=900
    )
    results["dirb"] = executor.run("dirb", [url, wordlist, "-o", f"{output_dir}/dirb.txt"], timeout=900)
    return results


def run_fingerprint(executor, url, output_dir):
    results = {}
    results["httpx"] = executor.run("httpx", ["-u", url, "-tech-detect", "-title", "-status-code"], timeout=120)
    results["katana"] = executor.run("katana", ["-u", url, "-o", f"{output_dir}/katana_urls.txt"], timeout=600)
    results["wafw00f"] = executor.run("wafw00f", [url], timeout=120)
    return results


def run_scanners(executor, url, output_dir):
    results = {}
    results["nikto"] = executor.run("nikto", ["-h", url, "-o", f"{output_dir}/nikto.txt"], timeout=1200)
    results["sqlmap"] = executor.run(
        "sqlmap", ["-u", url, "--batch", "--crawl=2", "--output-dir", f"{output_dir}/sqlmap"], timeout=1800
    )
    results["wpscan"] = executor.run(
        "wpscan", ["--url", url, "--enumerate", "vp,vt,u", "-o", f"{output_dir}/wpscan.txt"], timeout=900
    )
    results["arjun"] = executor.run("arjun", ["-u", url, "-oT", f"{output_dir}/arjun.txt"], timeout=600)
    results["paramspider"] = executor.run("paramspider", ["-d", url], timeout=300)
    results["dalfox"] = executor.run("dalfox", ["url", url, "-o", f"{output_dir}/dalfox.txt"], timeout=900)
    return results


def run_all(executor, url, wordlist, output_dir):
    results = {}
    results.update(run_fingerprint(executor, url, output_dir))
    results.update(run_content_discovery(executor, url, wordlist, output_dir))
    results.update(run_scanners(executor, url, output_dir))
    return results
