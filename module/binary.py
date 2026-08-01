"""
Web KinG - Binary Analysis & Forensics Module
================================================
Wraps static-analysis / forensics tools in their batch/non-interactive
modes. gdb and Ghidra are primarily interactive tools; where a
non-interactive path exists it's used, otherwise the module reports
that manual analysis is required rather than faking automation.
"""


def run_static_analysis(executor, binary_path, output_dir):
    results = {}
    results["file"] = executor.run("file", [binary_path], timeout=30)
    results["strings"] = executor.run("strings", [binary_path], timeout=60)
    results["checksec"] = executor.run("checksec", ["--file", binary_path], timeout=30)
    results["objdump"] = executor.run("objdump", ["-d", binary_path], timeout=120)
    results["binwalk"] = executor.run("binwalk", [binary_path], timeout=120)
    return results


def run_gdb_batch(executor, binary_path, gdb_script, output_dir):
    """Run gdb non-interactively with a pre-written .gdbscript of commands."""
    return {"gdb": executor.run(
        "gdb", ["-batch", "-x", gdb_script, binary_path], timeout=120
    )}


def run_radare2_batch(executor, binary_path, r2_commands, output_dir):
    """r2_commands: e.g. 'aaa; afl; pdf @ main'"""
    return {"radare2": executor.run("r2", ["-q", "-c", r2_commands, binary_path], timeout=120)}


def run_ghidra_headless(executor, project_dir, project_name, binary_path, output_dir):
    """Requires Ghidra's analyzeHeadless script on PATH."""
    args = [project_dir, project_name, "-import", binary_path, "-deleteProject"]
    return {"ghidra": executor.run("analyzeHeadless", args, timeout=1800)}


def run_forensics(executor, image_path, output_dir):
    results = {}
    results["foremost"] = executor.run(
        "foremost", ["-i", image_path, "-o", f"{output_dir}/foremost_out"], timeout=1800
    )
    results["exiftool"] = executor.run("exiftool", [image_path], timeout=60)
    return results


def run_steghide_extract(executor, image_path, passphrase, output_dir):
    return {"steghide": executor.run(
        "steghide", ["extract", "-sf", image_path, "-p", passphrase, "-xf",
                     f"{output_dir}/steghide_out"], timeout=60
    )}


def run_volatility(executor, memory_image, plugin, output_dir):
    return {"volatility3": executor.run(
        "vol", ["-f", memory_image, plugin], timeout=1800
    )}
