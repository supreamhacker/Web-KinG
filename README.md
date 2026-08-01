# Web KinG

Ek Python orchestrator jo already-installed pentest tools ko chalata hai aur
sab ka output ek HTML report mein compile kar deta hai. Ye khud koi scanning
ya exploitation logic implement nahi karta — har module sirf ek asli tool
(nmap, amass, sqlmap, hydra, radare2 waghera) ko subprocess ke zariye call
karta hai, uska output capture karta hai, aur log rakhta hai.

**Sirf authorized targets pe use karo** — apni khud ki systems, ya jahan
likhit permission ho (bug bounty scope, signed pentest agreement, CTF box).
Tool run se pehle authorization confirm karwata hai (`--yes` se skip ho
sakta hai automation ke liye, lekin ye bhi ek explicit assertion hai).

## Structure

webking/
webking.py <- CLI entrypoint
core/
executor.py <- subprocess wrapper (timeout, logging, arg-list only)
target.py <- target validation + authorization gate
report.py <- HTML/JSON report generator
modules/
recon.py <- nmap, masscan, rustscan, amass, subfinder, nuclei,
fierce, dnsenum, autorecon, theharvester, enum4linux-ng
webapp.py <- gobuster, feroxbuster, dirsearch, ffuf, dirb, httpx,
katana, nikto, sqlmap, wpscan, arjun, paramspider,
dalfox, wafw00f
auth.py <- hydra, medusa, patator, crackmapexec/netexec,
enum4linux-ng, evil-winrm (explicit params only,
NOT included in the automatic full pipeline)
creds.py <- john, hashcat, hashid, ophcrack (offline hash files)
binary.py <- gdb, radare2, ghidra (headless), binwalk, checksec,
strings, objdump, volatility3, foremost, steghide,
exiftool


## Install (Kali/Debian — tools themselves, not Web KinG's own code)

Web KinG doesn't reimplement any of these; you need them installed and on
`$PATH`. Most ship with Kali already; the rest:

```bash
sudo apt install nmap masscan amass nikto sqlmap hydra john hashcat \
    binwalk gdb radare2 exiftool foremost steghide dirb enum4linux-ng
pip install theHarvester wpscan-cli 2>/dev/null  # some are gem/go installs, see each tool's own docs
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/ffuf/ffuf/v2@latest
cargo install rustscan
```
Any tool that's missing is skipped automatically (Web KinG checks `PATH`
before calling it) rather than crashing the whole run.

## Usage

### 1. CLI flags

python3 webking.py -t TARGET [options] {recon|web|full}

-t, --target Target IP / domain / URL (required)
-o, --output Output directory (default: webking_output)
--domain Treat target as a domain (turns on DNS/OSINT modules)
--fast Use rustscan instead of nmap -p- for port scanning
--wordlist PATH Wordlist for content discovery (gobuster/ffuf/etc.)
--yes Skip the interactive authorization prompt (non-interactive mode)
--dry-run Print every command that WOULD run, without running it


The `{recon|web|full}` keyword can go before or after the other flags —
both `webking.py full -t example.com` and `webking.py -t example.com full`
work.

### 2. The three modes

**`recon`** — network + DNS + OSINT only (nmap/masscan/rustscan, subfinder,
amass, fierce, dnsenum, theHarvester, nuclei).

```bash
python3 webking.py -t example.com --domain recon
```

**`web`** — web application testing only (httpx, katana, wafw00f, gobuster,
feroxbuster, dirsearch, ffuf, dirb, nikto, sqlmap, wpscan, arjun,
paramspider, dalfox). Target should be a URL, or a bare host (`http://`
gets prefixed automatically).

```bash
python3 webking.py -t https://example.com \
    --wordlist /usr/share/wordlists/dirb/common.txt web
```

**`full`** — runs `recon` then `web`, then generates the report.

```bash
python3 webking.py -t https://example.com --domain \
    --wordlist /usr/share/wordlists/dirb/common.txt --yes full
```

### 3. First run: authorization prompt

Every run — unless you pass `--yes` — stops and asks you to type `yes`
to confirm you're authorized to test the target:
==============================================================
WEB KING — AUTHORIZATION CHECK
Target: example.com
Only scan systems you own or have written permission to
test (e.g. a signed pentest/bug-bounty scope). Unauthorized
scanning is illegal in most jurisdictions.

Type 'yes' to confirm you are authorized to test this target:


For scripted/CI use, add `--yes` — that itself counts as your explicit
authorization statement, so use it only when it's actually true.

### 4. Dry-run first (recommended before any real scan)

See exactly what commands Web KinG would execute, in what order, without
touching the network at all:

```bash
python3 webking.py -t example.com --domain --yes --dry-run full
```

### 5. Output

Everything lands under `-o` (default `webking_output/`):

webking_output/
├── report.html <- human-readable report, open in any browser
├── report.json <- same data, machine-readable
├── logs/ <- one raw .log file per tool invocation (full stdout/stderr)
├── nmap_full.txt <- individual tool output files (per-module, as configured)
├── subfinder.txt
├── nuclei.txt
├── gobuster.txt
├── sqlmap/
└── ...


Open `report.html` in a browser: it shows a summary bar (how many tools
ran OK / failed / were skipped because they're not installed), then one
collapsible section per tool with the command that was run and its full
output.

### 6. Auth / credential / binary modules

`hydra`, `medusa`, `patator`, `crackmapexec`, `john`, `hashcat`, `gdb`,
`radare2`, `ghidra`, `volatility3`, etc. are **not** part of the `recon`/
`web`/`full` CLI modes — they require target-specific parameters (which
service, which wordlist, which hash file) that only make sense once you
know what you're dealing with. Import them directly, e.g.:

```python
from core.executor import Executor
from modules import auth

executor = Executor()
result = auth.run_hydra(
    executor, target="10.10.10.5", service="ssh",
    userlist="users.txt", passlist="passwords.txt",
    output_dir="webking_output",
)
print(result["hydra"].stdout)
```

More examples:

```python
# Offline hash cracking (creds.py) — you already hold the hash file
from modules import creds
creds.run_hashcat(executor, hash_file="hashes.txt",
                   wordlist="/usr/share/wordlists/rockyou.txt",
                   mode=0, output_dir="webking_output")   # mode 0 = MD5

# Internal AD enumeration (auth.py)
from modules import auth
auth.run_crackmapexec(executor, protocol="smb", target="10.10.10.5",
                       userlist="users.txt", passlist="passwords.txt")

# Static binary analysis (binary.py)
from modules import binary
binary.run_static_analysis(executor, binary_path="./challenge.bin",
                            output_dir="webking_output")
```

Every one of these still returns `ToolResult` objects — feed them into
`core.report.generate_report()` the same way `webking.py` does if you
want them folded into the same HTML report:

```python
from core.report import generate_report
all_results = {"Auth": result}
generate_report("10.10.10.5", all_results, output_dir="webking_output")
```

## Troubleshooting

- **"not found on PATH — skipped"** in a log/report entry → that tool
  isn't installed, or isn't on `$PATH`. Web KinG skips it and keeps going
  rather than crashing the whole run.
- **Nothing happens / long wait** → some tools (nmap `-p-`, masscan) are
  slow by nature; use `--fast` for a quicker rustscan-based pass, or check
  `logs/` for the specific tool's raw output while it runs.
- **Permission errors on masscan/rustscan** → these need raw socket access;
  run with `sudo` or grant the binary `CAP_NET_RAW`.

## Notes

- `executor.py` never builds a shell string from target input — every
  command is an argument list, so there's no shell-injection surface.
- Every run writes a raw log file per tool call under `logs/`, so nothing
  is lost even if the report generation step fails.
- sqlmap/dalfox run in their default (non-destructive, non-shell) detection
  modes — no `--os-shell`, no risk/level escalation baked in.
