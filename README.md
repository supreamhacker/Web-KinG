# Web-KinG
"Disclaimmer ' it is only use ethically. Without permission if you use it I am not resposebale for it" A powerfull tool that find any type of vulnerability. It's start from reconesince and stop with clear report that define every step of the proccess.
# 👑 Web KinG - Advanced Automated Reconnaissance Framework

Web KinG is a powerful, multi-threaded automated recon pipeline designed for Pentesters and Bug Bounty hunters. It wraps top-tier Kali Linux tools into a single, high-speed execution matrix.

## 🚀 Features
- **Parallel Processing:** Runs subdomain discovery and URL scraping simultaneously using Python threads.
- **Fail-Safe execution:** Missing system tools are automatically skipped without crashing the script.
- **Unified Reporting:** Generates a structured Markdown report after scanning.

## 🛠️ Integrated Tools
- **Subdomains:** Subfinder, Assetfinder, Findomain
- **Probing:** HTTPX, Httprobe, Naabu
- **Crawling:** Waybackurls, GAU, Katana
- **Fuzzing:** FFUF, Dirsearch, Arjun
- **Vuln Scan:** Nuclei, SQLMap, Dalfox

## 💻 Installation & Usage
```bash
# Clone the repository
git clone https://github.com
cd Web-KinG

# Install requirements
pip3 install -r requirements.txt

# Run the tool
python3 web_king.py example.com
```
