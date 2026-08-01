"""
Web KinG - Credential Analysis Module
========================================
Operates on hash files the operator already has in hand from an
authorized engagement (e.g. dumped during a prior finding). No
online attack surface here — these tools work offline against a
local file.
"""


def run_john(executor, hash_file, wordlist=None, output_dir="webking_output"):
    args = [hash_file]
    if wordlist:
        args = [f"--wordlist={wordlist}"] + args
    return {"john": executor.run("john", args, timeout=3600)}


def run_hashcat(executor, hash_file, wordlist, mode, output_dir):
    args = ["-m", str(mode), "-a", "0", hash_file, wordlist,
            "-o", f"{output_dir}/hashcat_cracked.txt"]
    return {"hashcat": executor.run("hashcat", args, timeout=3600)}


def run_hash_identifier(executor, hash_string):
    return {"hash-identifier": executor.run("hash-identifier", [], timeout=30)}
    # Note: hash-identifier is interactive; prefer `hashid` for scripted use.


def run_hashid(executor, hash_string):
    return {"hashid": executor.run("hashid", [hash_string], timeout=30)}


def run_ophcrack(executor, sam_file, output_dir):
    return {"ophcrack": executor.run(
        "ophcrack", ["-g", "-d", "/usr/share/ophcrack/tables", "-f", sam_file,
                     "-o", f"{output_dir}/ophcrack.txt"], timeout=1800
    )}
