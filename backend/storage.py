"""Tiny run history: one JSON line per experiment in results/runs.jsonl.
(An internship project would use a database; a file keeps this project simple.)"""
import json
from datetime import datetime, timezone
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
HISTORY_FILE = RESULTS_DIR / "runs.jsonl"


def save_run(result: dict) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": result["config"],
        "qsvm_accuracy": result["results"]["qsvm"]["accuracy"],
        "rbf_accuracy": result["results"]["classical_rbf"]["accuracy"],
        "linear_accuracy": result["results"]["classical_linear"]["accuracy"],
        "circuit_depth": result["circuit"]["depth"],
    }
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_history(limit: int = 50) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines[-limit:]][::-1]
