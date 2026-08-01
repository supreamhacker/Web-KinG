"""
Web KinG - Password & Authentication Module
==============================================
These tools perform active credential testing. Web KinG never picks
a wordlist, service, or username for you and never runs this module
as part of --full by default — you must explicitly invoke it and
supply every parameter yourself. That keeps the operator squarely
in control of what gets tested, on services that are actually in
your authorized scope.
"""


def run_hydra(executor, target, service, userlist, passlist, output_dir, port=None):
    args = ["-L", userlist, "-P", passlist]
    if port:
        args += ["-s", str(port)]
    args += ["-o", f"{output_dir}/hydra_{service}.txt", target, service]
    return {"hydra": executor.run("hydra", args, timeout=1800)}


def run_medusa(executor, target, service, userlist, passlist, output_dir):
    args = ["-h", target, "-U", userlist, "-P", passlist, "-M", service,
            "-O", f"{output_dir}/medusa_{service}.txt"]
    return {"medusa": executor.run("medusa", args, timeout=1800)}


def run_patator(executor, module, extra_args, output_dir):
    """
    `module` e.g. 'ssh_login', extra_args is a list of patator
    key=value tokens the caller builds explicitly (host=, user=, password=...).
    """
    args = [module] + extra_args
    return {"patator": executor.run("patator", args, timeout=1800)}


def run_crackmapexec(executor, protocol, target, userlist=None, passlist=None, extra_args=None):
    args = [protocol, target]
    if userlist:
        args += ["-u", userlist]
    if passlist:
        args += ["-p", passlist]
    if extra_args:
        args += extra_args
    # netexec is the maintained fork of crackmapexec; try it first, fall back
    tool = "netexec" if executor.which("netexec") else "crackmapexec"
    return {tool: executor.run(tool, args, timeout=1800)}


def run_enum4linux(executor, target, output_dir):
    return {"enum4linux-ng": executor.run(
        "enum4linux-ng", ["-A", target, "-oY", f"{output_dir}/enum4linux.yaml"], timeout=600
    )}


def run_evil_winrm(executor, target, user, password_or_hash, use_hash=False):
    """Post-exploitation shell — only for a host/credential pair you already
    legitimately hold as part of the engagement (e.g. from a prior finding)."""
    args = ["-i", target, "-u", user]
    args += ["-H", password_or_hash] if use_hash else ["-p", password_or_hash]
    return {"evil-winrm": executor.run("evil-winrm", args, timeout=120)}
