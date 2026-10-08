"""Python bridge to the Node oref oracle.

Runs the real oref0 determine-basal (see oracle/determine.js). The subprocess runner is
injectable so the counterfactual logic can be unit-tested without Node or oref0 present —
the same pattern as ingestion's HTTP transport.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

ORACLE_DIR = Path(__file__).parent / "oracle"

# runner(requests) -> list of result dicts, each {"ok": bool, "rt": {...}} or {"ok": False, "error": str}
Runner = Callable[[list[dict]], list[dict]]


class OracleUnavailable(RuntimeError):
    pass


class OracleError(RuntimeError):
    pass


class _NodeSimulator:
    """A long-lived `node determine.js --serve` process for request.js `simulate`.

    One process for the oracle's lifetime keeps the simulator's insulin-on-board cache
    between the stages of a report; a fresh process per call would rebuild it each time
    (about 22 s for a week at 5-minute cycles).
    """

    def __init__(self, oracle_dir: Path, node_bin: str = "node"):
        self._args = [node_bin, str(oracle_dir / "determine.js"), "--serve"]
        self._cwd = str(oracle_dir)
        self._proc = None

    def _start(self):
        import subprocess

        try:
            # oref narrates to stderr at length; an undrained pipe would stall the process
            self._proc = subprocess.Popen(
                self._args, cwd=self._cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
        except FileNotFoundError as exc:
            raise OracleUnavailable(f"node not found ({self._args[0]})") from exc

    def __call__(self, payload: dict) -> dict:
        if self._proc is None or self._proc.poll() is not None:
            self._start()
        self._proc.stdin.write(json.dumps({"simulate": payload}) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line:
            raise OracleError("simulator exited without a reply")
        out = json.loads(line)
        if "error" in out:
            raise OracleError(f"simulation error: {out['error']}")
        return out["simulation"]

    def close(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.stdin.close()
            self._proc.wait(timeout=10)
        self._proc = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def _node_runner(oracle_dir: Path, node_bin: str = "node", timeout_s: float = 60.0) -> Runner:
    import subprocess  # lazy: not available under Pyodide, and only the CLI/server path needs it

    script = oracle_dir / "determine.js"

    def run(requests: list[dict]) -> list[dict]:
        if not script.exists():
            raise OracleUnavailable(f"oracle script missing: {script}")
        try:
            proc = subprocess.run(
                [node_bin, str(script)],
                input=json.dumps({"requests": requests}),
                capture_output=True, text=True, cwd=str(oracle_dir), timeout=timeout_s,
            )
        except FileNotFoundError as exc:
            raise OracleUnavailable(f"node not found ({node_bin})") from exc
        except subprocess.TimeoutExpired as exc:
            raise OracleError("oracle timed out") from exc
        if not proc.stdout.strip():
            raise OracleError(f"oracle produced no output (stderr: {proc.stderr[:400]})")
        payload = json.loads(proc.stdout)
        if "error" in payload:
            raise OracleError(f"oracle error: {payload['error']}")
        return payload.get("results", [])

    return run


class OrefOracle:
    def __init__(self, runner: Runner | None = None, oracle_dir: Path = ORACLE_DIR,
                 simulator: Callable[[dict], dict] | None = None):
        self._runner = runner or _node_runner(oracle_dir)
        self._simulator = simulator or (_NodeSimulator(oracle_dir) if runner is None else None)

    def simulate(self, payload: dict) -> dict:
        """Closed-loop scenario simulation (oracle/request.js `simulate`)."""
        if self._simulator is None:
            raise OracleUnavailable("no simulator configured")
        return self._simulator(payload)

    def evaluate(self, requests: list[dict]) -> list[dict]:
        """Return the raw result records (one per request), preserving ok/error per item."""
        if not requests:
            return []
        return self._runner(requests)

    def enacted(self, requests: list[dict]) -> list[dict | None]:
        """Return just the rT decision per request, or None where that cycle errored."""
        out: list[dict | None] = []
        for r in self.evaluate(requests):
            out.append(r.get("rt") if r.get("ok") else None)
        return out
