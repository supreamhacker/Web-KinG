
Ek Python orchestrator jo already-installed pentest tools ko chalata hai aur sab ka output ek HTML report mein compile kar deta hai. Ye khud koi scanning ya exploitation logic implement nahi karta — har module sirf ek asli tool (nmap, amass, sqlmap, hydra, radare2 waghera) ko subprocess ke zariye call karta hai, uska output capture karta hai, aur log rakhta hai.

Sirf authorized targets pe use karo — apni khud ki systems, ya jahan likhit permission ho (bug bounty scope, signed pentest agreement, CTF box). Tool run se pehle authorization confirm karwata hai (--yes se skip ho sakta hai automation ke liye, lekin ye bhi ek explicit assertion hai).

Structure
webking/
  webking.py          <- CLI entrypoint
  core/
    executor.py        <- subprocess wrapper (timeout, logging, arg-list only)
    target.py           <- target validation + authorization gate
    report.py            <- HTML/JSON report generator
  modules/
    recon.py           <- nmap, masscan, rustscan, amass, subfinder, nuclei,
                           fierce, dnsenum, autorecon, theharvester, enum4linux-ng
    webapp.py           <- gobuster, feroxbuster, dirsearch, ffuf, dirb, httpx,
                           katana, nikto, sqlmap, wpscan, arjun, paramspider,
                           dalfox, wafw00f
    auth.py             <- hydra, medusa, patator, crackmapexec/netexec,
                           enum4linux-ng, evil-winrm (explicit params only,
                           NOT included in the automatic `full` pipeline)
    creds.py           <- john, hashcat, hashid, ophcrack (offline hash files)
    binary.py           <- gdb, radare2, ghidra (headless), binwalk, checksec,
                           strings, objdump, volatility3, foremost, steghide,
                           exiftool
Install (Kali/Debian — tools themselves, not Web KinG's own code)
Web KinG doesn't reimplement any of these; you need them installed and on $PATH. Most ship with Kali already; the rest:

sudo apt install nmap masscan amass nikto sqlmap hydra john hashcat \
    binwalk gdb radare2 exiftool foremost steghide dirb enum4linux-ng
pip install theHarvester wpscan-cli 2>/dev/null  # some are gem/go installs, see each tool's own docs
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/ffuf/ffuf/v2@latest
cargo install rustscan
Any tool that's missing is skipped automatically (Web KinG checks PATH before calling it) rather than crashing the whole run.

Usage
# Recon only, against a domain
python3 webking.py recon -t example.com --domain

# Full recon + web app pass, auto-confirm authorization
python3 webking.py full -t https://example.com --domain \
    --wordlist /usr/share/wordlists/dirb/common.txt --yes

# See exactly what would run, without executing anything
python3 webking.py full -t example.com --domain --dry-run
Output lands in webking_output/:

report.html — the human-readable report
report.json — same data, machine-readable
logs/ — full raw stdout/stderr per tool invocation
Auth / credential / binary modules
hydra, medusa, patator, crackmapexec, john, hashcat, gdb, radare2, ghidra, volatility3, etc. are not part of the recon/ web/full CLI modes — they require target-specific parameters (which service, which wordlist, which hash file) that only make sense once you know what you're dealing with. Import them directly, e.g.:

from core.executor import Executor
from modules import auth

executor = Executor()
result = auth.run_hydra(
    executor, target="10.10.10.5", service="ssh",
    userlist="users.txt", passlist="passwords.txt",
    output_dir="webking_output",
)
Notes



webking/
├── webking.py
├── README.md
├── core/
│   ├── __init__.py
│   ├── executor.py
│   ├── target.py
│   └── report.py
└── modules/
    ├── __init__.py
    ├── recon.py
    ├── webapp.py
    ├── auth.py
    ├── creds.py
    └── binary.py
executor.py never builds a shell string from target input — every command is an argument list, so there's no shell-injection surface.
Every run writes a raw log file per tool call under logs/, so nothing is lost even if the report generation step fails.
sqlmap/dalfox run in their default (non-destructive, non-shell) detection modes — no --os-shell, no risk/level escalation baked in.
