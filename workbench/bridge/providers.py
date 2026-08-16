"""Run external agent CLIs. Captures stdout to a log file, never a pipe."""

import subprocess


def run_provider(provider, workspace, log_path):
    """Run the provider command with cwd=workspace; return exit code or 'timeout'."""
    command = [provider["command"]] + list(provider.get("args", []))
    timeout = provider.get("timeout_s", 300)
    with open(log_path, "wb") as log:
        try:
            result = subprocess.run(
                command,
                cwd=str(workspace),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=timeout,
            )
            return result.returncode
        except subprocess.TimeoutExpired:
            return "timeout"
