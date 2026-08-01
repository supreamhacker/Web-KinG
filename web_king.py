#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style, init

init(autoreset=True)

BANNER = f"""
{Fore.RED}{Style.BRIGHT}================================================================================
{Fore.GREEN}{Style.BRIGHT}██╗    ██╗███████╗██████╗     ██╗  ██╗██╗███╗   ██╗ ██████╗ 
██║    ██║██╔════╝██╔══██╗    ██║  ██║██║████╗  ██║██╔════╝ 
██║ █╗ ██║█████╗  ██████╔╝    ███████║██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══╝  ██╔══██╗    ██╔══██║██║██║╚██╗██║██║   ██║
╚███╔███╔╝███████╗██████╔╝    ██║  ██║██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚══════╝╚═════╝     ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
{Fore.YELLOW}{Style.BRIGHT}           -- Full Power Automated Vulnerability Matrix --             
================================================================================
"""

class WebKingFramework:
    def __init__(self, domain):
        self.domain = domain
        self.output_dir = f"webking_recon_{domain}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.subs_raw = f"{self.output_dir}/subdomains_all_raw.txt"
        self.subs_clean = f"{self.output_dir}/subdomains_unique.txt"
        self.live_hosts = f"{self.output_dir}/live_hosts.txt"
        self.ports_scan = f"{self.output_dir}/open_ports_naabu.txt"
        self.urls_all = f"{self.output_dir}/extracted_urls_raw.txt"
        self.urls_clean = f"{self.output_dir}/extracted_urls_clean.txt"
        self.fuzz_results = f"{self.output_dir}/directory_fuzzing.txt"
        self.parameters = f"{self.output_dir}/hidden_parameters.txt"
        self.js_links = f"{self.output_dir}/js_files_links.txt"
        self.js_endpoints = f"{self.output_dir}/js_endpoints_extracted.txt"
        self.nuclei_vulns = f"{self.output_dir}/nuclei_vulnerabilities.txt"
        self.dalfox_xss = f"{self.output_dir}/dalfox_xss_results.txt"
        self.sqlmap_dir = f"{self.output_dir}/sqlmap_dump"
        self.report_md = f"{self.output_dir}/WEB_KING_FINAL_REPORT.md"

    def logger(self, log_type, msg):
        if log_type == "info":
            print(f"[{Fore.BLUE}*{Fore.RESET}] {msg}")
        elif log_type == "success":
            print(f"[{Fore.GREEN}+{Fore.RESET}] {Fore.GREEN}{Style.BRIGHT}{msg}")
        elif log_type == "warning":
            print(f"[{Fore.YELLOW}!{Fore.RESET}] {Fore.YELLOW}{msg}")
        elif log_type == "error":
            print(f"[{Fore.RED}x{Fore.RESET}] {Fore.RED}{Style.BRIGHT}{msg}")

    def tool_exists(self, binary):
        if shutil.which(binary) is None:
            self.logger("warning", f"Dependency '{binary}' is not available in system path. Skipping step dynamically.")
            return False
        return True

    def run_engine(self, command, task_desc):
        self.logger("info", f"Initiating: {task_desc}")
        try:
            process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode == 0:
                self.logger("success", f"Successfully Completed: {task_desc}")
                return True
            else:
                self.logger("warning", f"Execution alert for {task_desc}. Checking output consistency.")
                return False
        except Exception as e:
            self.logger("error", f"Critical engine execution failure during [{task_desc}]: {str(e)}")
            return False

    def process_subdomains_dedup(self):
        if os.path.exists(self.subs_raw):
            with open(self.subs_raw, "r") as f:
                lines = f.readlines()
            clean_subs = sorted(list(set([line.strip().lower() for line in lines if line.strip()])))
            with open(self.subs_clean, "w") as f:
                f.write("\n".join(clean_subs))
            self.logger("success", f"Subdomain pipeline clean. Total unique assets tracked: {len(clean_subs)}")

    def process_urls_dedup(self):
        if os.path.exists(self.urls_all):
            with open(self.urls_all, "r") as f:
                lines = f.readlines()
            clean_urls = sorted(list(set([line.strip() for line in lines if line.strip()])))
            with open(self.urls_clean, "w") as f:
                f.write("\n".join(clean_urls))
            self.logger("success", f"URL map clean. Saved {len(clean_urls)} active target templates endpoints.")

    def step1_aggressive_subdomain_enum(self):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 01] RUNNING AGGRESSIVE SUBDOMAIN ENUMERATION")
        
        if self.tool_exists("subfinder"):
            self.run_engine(f"subfinder -d {self.domain} -all -recursive -silent -o {self.subs_raw}", "Subfinder Active Passive deep-scan")
            
        if self.tool_exists("assetfinder"):
            self.run_engine(f"assetfinder --subs-only {self.domain} >> {self.subs_raw}", "Assetfinder data scraper extraction")
            
        if self.tool_exists("findomain"):
            self.run_engine(f"findomain -t {self.domain} -q >> {self.subs_raw}", "Findomain tracking agent lookup")
            
        if self.tool_exists("amass"):
            self.run_engine(f"amass enum -passive -d {self.domain} -norefresh >> {self.subs_raw}", "OWASP Amass Passive framework layout mapping")

        if self.tool_exists("puredns") and os.path.exists(self.subs_raw):
            self.run_engine(f"puredns resolve {self.subs_raw} --quiet -r /usr/share/wordlists/dns/resolvers.txt -w {self.subs_raw}_resolved", "PureDNS resolving cluster processing")
            if os.path.exists(f"{self.subs_raw}_resolved"):
                shutil.move(f"{self.subs_raw}_resolved", self.subs_raw)

        self.process_subdomains_dedup()

    def step2_probing_and_port_scanning(self):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 02] RUNNING PORT SCANNING & ACTIVE SERVICE PROBING")
        if not os.path.exists(self.subs_clean) or os.stat(self.subs_clean).st_size == 0:
            self.logger("error", "Empty target matrix detected. Aborting probing routing.")
            return

        if self.tool_exists("httpx"):
            self.run_engine(f"httpx -l {self.subs_clean} -sc -title -td -ip -follow-redirects -threads 100 -silent -o {self.live_hosts}", "HTTPX Deep technology inspection stack analysis")
        elif self.tool_exists("httprobe"):
            self.run_engine(f"cat {self.subs_clean} | httprobe -p http:80,https:443,http:8080,https:8443 > {self.live_hosts}", "Httprobe emergency fallback array initialization")

        if self.tool_exists("naabu"):
            self.run_engine(f"naabu -l {self.subs_clean} -top-ports 1000 -rate 5000 -silent -o {self.ports_scan}", "Naabu Rapid Multi-port core distribution scanning matrix")

    def step3_endpoint_and_spider_crawling(self):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 03] EXTRACTING URLS, HISTORICAL ENDPOINTS & CRAWLING")
        
        if self.tool_exists("waybackurls"):
            self.run_engine(f"waybackurls {self.domain} > {self.urls_all}", "Waybackurls historical parameter footprint pull")
            
        if self.tool_exists("gau"):
            self.run_engine(f"gau --subs {self.domain} --threads 50 >> {self.urls_all}", "GAU Aggressive multi-threaded endpoint sync tracking")
            
        if self.tool_exists("katana"):
            self.run_engine(f"katana -u https://{self.domain} -jc -kf all -c 20 -d 3 -silent >> {self.urls_all}", "Katana complete script-aware automation crawler array")

        self.process_urls_dedup()

    def step4_directory_and_parameter_fuzzing(self):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 04] DIRECTORY BRUTE-FORCING & HIDDEN PARAMETER DISCOVERY")
        
        target_fuzz_url = f"https://{self.domain}"
        if os.path.exists(self.live_hosts) and os.stat(self.live_hosts).st_size > 0:
            with open(self.live_hosts, "r") as f:
                first_line = f.readline().strip()
            if " " in first_line:
                target_fuzz_url = first_line.split()[0]
            else:
                target_fuzz_url = first_line

        wordlist_path = "/usr/share/wordlists/dirb/common.txt"
        if not os.path.exists(wordlist_path):
            wordlist_path = "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt"

        if self.tool_exists("ffuf") and os.path.exists(wordlist_path):
            self.run_engine(f"ffuf -w {wordlist_path} -u {target_fuzz_url}/FUZZ -t 100 -mc 200,204,301,302,307,403 -recursion -recursion-depth 2 -s -o {self.fuzz_results}_json", "FFUF multi-tier path structural recursive brute forcing")

        if self.tool_exists("arjun"):
            self.run_engine(f"arjun -u {target_fuzz_url} -t 50 -oT {self.parameters}", "Arjun intelligent parameter detection testing maps")

    def step5_vulnerability_assessment_matrix(self):
        print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 05] LAUNCHING TARGET VULNERABILITY ASSESSMENT ENGINE")

        scan_target_file = self.subs_clean
        if os.path.exists(self.live_hosts) and os.stat(self.live_hosts).st_size > 0:
            scan_target_file = f"{self.output_dir}/nuclei_clean_targets.txt"
            with open(self.live_hosts, "r") as f, open(scan_target_file, "w") as out:
                for line in f:
                    if line.strip():
                        out.write(line.split()[0] + "\n")

        if self.tool_exists("nuclei") and os.path.exists(scan_target_file):
            self.run_engine(f"nuclei -l {scan_target_file} -severity info,low,medium,high,critical -rate-limit 150 -bulk-size 25 -silent -o {self.nuclei_vulns}", "Nuclei ultimate core vulnerabilities scanning execution")

        if self.tool_exists("dalfox") and os.path.exists(self.urls_clean):
            self.run_engine(f"dalfox file {self.urls_clean} --worker 50 --silent -o {self.dalfox_xss}", "Dalfox mass XSS parameter exploitation analysis array")
if self.tool_exists("sqlmap") and os.path.exists(self.urls_clean) and os.stat(self.urls_clean).st_size > 0:self.run_engine(f"sqlmap -m {self.urls_clean} --batch --smart --level=2 --risk=2 --threads=5 --random-agent --output-dir={self.sqlmap_dir}", "SQLMap advanced database testing scripts array profiles execution")def step6_javascript_static_analysis(self):print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 06] EXTRACTING JAVASCRIPT LINKS AND ANALYZING SECRETS")if os.path.exists(self.urls_clean):self.run_engine(f"grep '\.js' {self.urls_clean} > {self.js_links}", "Filtering out structural system JavaScript link maps references")if os.path.exists(self.js_links) and os.stat(self.js_links).st_size > 0:if self.tool_exists("linkfinder"):self.run_engine(f"linkfinder -i {self.js_links} -o cli > {self.js_endpoints}", "LinkFinder script data compilation mapping execution sequence")if self.tool_exists("secretfinder"):self.run_engine(f"python3 -m secretfinder -i {self.js_links} -o cli > {self.output_dir}/js_leaked_secrets.txt", "SecretFinder continuous verification extraction")def step7_generate_ultimate_report(self):print(f"\n{Fore.MAGENTA}{Style.BRIGHT}[STAGE 07] GENERATING COMPREHENSIVE PENTESTING REPORT SUMMARY")self.logger("info", "Structuring gathered telemetry logs into standard Markdown formats...")try:with open(self.report_md, "w") as r:r.write(f"# 👑 WEB KING AUTOMATED PENTESTING INTEL REPORT: {self.domain.upper()}\n\n")r.write(f"### 🎯 Target System Domain Parameter: {self.domain}\n")r.write("--- \n\n")r.write("## 📜 1. Subdomain Enumeration Intelligence\n")if os.path.exists(self.subs_clean):with open(self.subs_clean, "r") as f:subs = f.readlines()r.write(f"- Total Discovered Assets: {len(subs)} unique subdomains verified.\n\n")r.write("### 🔍 Snapshot (Top 20 Verified Domains):\ntext\n") r.write("".join(subs[:20]) + ("\n...[Truncated for clarity]..." if len(subs) > 20 else "") + "\n\n\n")else:r.write("❌ No subdomain artifacts architecture verified.\n\n")r.write("## 🌐 2. Verified Active Hosts & Technology Stack Fingerprints\n")if os.path.exists(self.live_hosts) and os.stat(self.live_hosts).st_size > 0:with open(self.live_hosts, "r") as f:r.write("text\n" + f.read() + "\n\n")else:r.write("⚠️ No alive endpoint systems responded down the line.\n\n")r.write("## ⚡ 3. Vulnerability Findings & Security Assessment Matrix\n")vuln_found = Falseif os.path.exists(self.nuclei_vulns) and os.stat(self.nuclei_vulns).st_size > 0:vuln_found = Truer.write("### 🟢 Nuclei Vulnerability Scan Matches:\ntext\n") with open(self.nuclei_vulns, "r") as f: r.write(f.read() + "\n\n")if os.path.exists(self.dalfox_xss) and os.stat(self.dalfox_xss).st_size > 0:vuln_found = Truer.write("### 🧪 Confirmed Cross-Site Scripting (XSS) Vulnerabilities:\ntext\n") with open(self.dalfox_xss, "r") as f: r.write(f.read() + "\n\n")if not vuln_found:r.write("✅ No critical automated vulnerability vectors directly mapped during this rapid fuzz configuration sequence.\n\n")r.write("\n\n---\nReport compiled securely via Web KinG Framework Automated Process System Engine.")self.logger("success", f"Framework report generation sequence complete. Target location path: {self.report_md}")if self.tool_exists("pandoc"):self.run_engine(f"pandoc {self.report_md} -o {self.report_md.replace('.md', '.pdf')}", "Converting system compiled logs markdown into PDF format")except Exception as e:self.logger("error", f"Failed compiling report format blueprints maps metrics: {str(e)}")def execute_full_pipeline(self):print(BANNER)self.logger("success", f"Initializing Web KinG Engine Pipeline execution for target: {self.domain}")with ThreadPoolExecutor(max_workers=2) as executor:executor.submit(self.step1_aggressive_subdomain_enum)executor.submit(self.step3_endpoint_and_spider_crawling)self.step2_probing_and_port_scanning()self.step4_directory_and_parameter_fuzzing()self.step5_vulnerability_assessment_matrix()self.step6_javascript_static_analysis()self.step7_generate_ultimate_report()print(f"\n{Fore.GREEN}{Style.BRIGHT}================================================================================")self.logger("success", f"Web KinG Pipeline execution arrays completed completely. Path: {self.output_dir}")print(f"{Fore.GREEN}{Style.BRIGHT}================================================================================\n")if name == "main":if len(sys.argv) < 2:print(BANNER)print(f"{Fore.YELLOW}Usage Framework Execution: python3 web_king.py <target_domain.com>")sys.exit(1)raw_input = sys.argv[1].strip().lower()clean_target = raw_input.replace("https://", "").replace("http://", "").split("/")[0]king_framework = WebKingFramework(clean_target)king_framework.execute_full_pipeline()
