"""Run the full comparison WITHOUT the web app and save a CSV + graph for the report.

    python scripts/run_experiments.py --dataset breast_cancer --qubits 4
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backend.services.evaluate import run_sweep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="iris", choices=["iris", "wine", "breast_cancer"])
    ap.add_argument("--qubits", type=int, default=4)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--max-samples", type=int, default=150)
    args = ap.parse_args()

    out = run_sweep(args.dataset, args.qubits, args.reps, max_samples=args.max_samples)
    df = pd.DataFrame(out["rows"])
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    stem = f"sweep_{args.dataset}_{args.qubits}q"
    df.to_csv(out_dir / f"{stem}.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nClassical RBF baseline accuracy: {out['classical_rbf_accuracy']}")

    fig, ax = plt.subplots(figsize=(8, 5))
    for fm, grp in df.groupby("feature_map"):
        ax.plot(grp["bandwidth"], grp["accuracy"], marker="o", label=f"QSVM - {fm}")
    ax.axhline(out["classical_rbf_accuracy"], color="black", linestyle="--", label="Classical RBF SVM")
    ax.set_xlabel("Bandwidth (data scaling)")
    ax.set_ylabel("Test accuracy")
    ax.set_title(f"{args.dataset}, {args.qubits} qubits, reps={args.reps}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}.png", dpi=150)
    print(f"Saved results/{stem}.csv and results/{stem}.png")


if __name__ == "__main__":
    main()
