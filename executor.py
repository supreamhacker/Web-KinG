"""
Web KinG - Core Command Executor
=================================
Every external tool call in Web KinG goes through this module. It:

  - never builds a shell string from raw input (commands are argument lists,
    so there is no shell-injection surface even with untrusted target strings)
  - enforces a per-tool timeout so one hanging tool can't stall the whole run
  - captures stdout/stderr and writes a raw log file per invocation
  - skips gracefully (instead of crashing) when a tool isn't installed
"""
import subprocess
import shlex
import time
from pathlib import Path
from datetime import datetime
from shutil import which as _which


class ToolResult:
    def __init__(self, tool, command, returncode, stdout, stderr, duration, timed_out=False):
        self.tool = tool
        self.command = command
        self.returncode = returncode
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.duration = duration
        self.timed_out = timed_out
        self.timestamp = datetime.now().isoformat()

    @property
    def success(self):
        return self.returncode == 0 and not self.timed_out

    def to_dict(self):
        return {
            "tool": self.tool,
            "command": self.command,
            "returncode": self.returncode,
            "success": self.success,
            "timed_out": self.timed_out,
            "duration_sec": round(self.duration, 2),
            "timestamp": self.timestamp,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


class Executor:
    def __init__(self, log_dir="webking_output/logs", dry_run=False, default_timeout=600):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        self.default_timeout = default_timeout

    def which(self, binary):
        return _which(binary)

    def run(self, tool, args, timeout=None, cwd=None):
        """Run `tool` with argument list `args`. Returns a ToolResult (never raises)."""
        timeout = timeout or self.default_timeout
        command_list = [tool] + list(args)
        command_str = " ".join(shlex.quote(c) for c in command_list)

        if not self.which(tool):
            msg = f"[!] '{tool}' not found on PATH — skipped. Install it or check your environment."
            result = ToolResult(tool, command_str, -1, "", msg, 0.0)
            self._log(result)
            return result

        if self.dry_run:
            print(f"[DRY-RUN] {command_str}")
            return ToolResult(tool, command_str, 0, "(dry run - not executed)", "", 0.0)

        start = time.time()
        timed_out = False
        try:
            proc = subprocess.run(
                command_list, cwd=cwd, capture_output=True, text=True, timeout=timeout
            )
            stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode(errors="ignore") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr, returncode, timed_out = f"[!] Timed out after {timeout}s", -1, True
        except FileNotFoundError:
            stdout, stderr, returncode = "", f"[!] '{tool}' not found", -1
        except Exception as e:
            stdout, stderr, returncode = "", f"[!] Error running {tool}: {e}", -1

        duration = time.time() - start
        result = ToolResult(tool, command_str, returncode, stdout, stderr, duration, timed_out)
        self._log(result)
        return result

    def _log(self, result: ToolResult):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fname = self.log_dir / f"{result.tool}_{ts}.log"
        try:
            with open(fname, "w", encoding="utf-8", errors="ignore") as f:
                f.write(f"COMMAND: {result.command}\n")
                f.write(f"RETURN CODE: {result.returncode}\n")
                f.write(f"DURATION: {result.duration:.2f}s\n")
                f.write(f"TIMED OUT: {result.timed_out}\n\n")
                f.write("--- STDOUT ---\n")
                f.write(result.stdout)
                f.write("\n--- STDERR ---\n")
                f.write(result.stderr)
        except OSError:
            pass
