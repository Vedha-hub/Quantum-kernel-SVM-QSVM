"""Step 4: one function that runs the whole experiment and returns plain dicts."""
import time

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.svm import SVC

from .classical import run_classical
from .data import prepare_data
from .quantum import FEATURE_MAPS, circuit_drawing, circuit_stats, compute_kernels


def _metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def run_experiment(
    dataset: str = "iris",
    n_qubits: int = 4,
    feature_map: str = "zz",
    reps: int = 2,
    bandwidth: float = 0.5,
    test_size: float = 0.25,
    max_samples: int = 120,
    C: float = 1.0,
    seed: int = 42,
) -> dict:
    if feature_map not in FEATURE_MAPS:
        raise ValueError(f"Unknown feature map '{feature_map}'")
    if not 2 <= n_qubits <= 10:
        raise ValueError("n_qubits must be between 2 and 10 (simulation cost grows as 2^n)")

    data = prepare_data(dataset, n_qubits, test_size, max_samples, seed)

    # Classical baselines
    rbf_pred, rbf_time = run_classical(data.X_train, data.y_train, data.X_test, "rbf", C)
    lin_pred, lin_time = run_classical(data.X_train, data.y_train, data.X_test, "linear", C)

    # Quantum kernel SVM. `bandwidth` shrinks the angles: big angles make every
    # pair of states look "far apart", so the kernel stops being useful.
    K_train, K_test, kernel_time = compute_kernels(
        feature_map, n_qubits, reps, data.X_train * bandwidth, data.X_test * bandwidth
    )
    t0 = time.perf_counter()
    qsvm = SVC(kernel="precomputed", C=C).fit(K_train, data.y_train)
    q_pred = qsvm.predict(K_test)
    q_fit_time = time.perf_counter() - t0

    # Small heatmap: up to 40 train samples, sorted by class so blocks are visible
    order = np.argsort(data.y_train, kind="stable")[:40]
    heat = K_train[np.ix_(order, order)]

    return {
        "config": {
            "dataset": dataset, "n_qubits": n_qubits, "feature_map": feature_map,
            "reps": reps, "bandwidth": bandwidth, "test_size": test_size, "max_samples": max_samples, "C": C, "seed": seed,
        },
        "data": {
            "n_train": int(len(data.y_train)),
            "n_test": int(len(data.y_test)),
            "class_names": data.class_names,
            "pca_explained_variance": round(data.explained_variance, 4),
        },
        "circuit": {**circuit_stats(feature_map, n_qubits, reps),
                    "diagram": circuit_drawing(feature_map, n_qubits, reps)},
        "results": {
            "qsvm": {**_metrics(data.y_test, q_pred),
                     "kernel_time_s": round(kernel_time, 3), "fit_time_s": round(q_fit_time, 4)},
            "classical_rbf": {**_metrics(data.y_test, rbf_pred), "fit_time_s": round(rbf_time, 4)},
            "classical_linear": {**_metrics(data.y_test, lin_pred), "fit_time_s": round(lin_time, 4)},
        },
        "kernel_heatmap": {
            "values": np.round(heat, 4).tolist(),
            "labels": data.y_train[order].tolist(),
        },
    }


def run_sweep(
    dataset: str = "iris",
    n_qubits: int = 4,
    reps: int = 2,
    bandwidths: tuple = (0.1, 0.25, 0.5, 1.0),
    test_size: float = 0.25,
    max_samples: int = 120,
    C: float = 1.0,
    seed: int = 42,
) -> dict:
    """Try every feature map at several bandwidths. This is the main comparison table."""
    data = prepare_data(dataset, n_qubits, test_size, max_samples, seed)
    rbf_pred, _ = run_classical(data.X_train, data.y_train, data.X_test, "rbf", C)
    rbf_acc = round(float(accuracy_score(data.y_test, rbf_pred)), 4)

    rows = []
    for fm in FEATURE_MAPS:
        stats = circuit_stats(fm, n_qubits, reps)
        for bw in bandwidths:
            K_tr, K_te, k_time = compute_kernels(fm, n_qubits, reps, data.X_train * bw, data.X_test * bw)
            pred = SVC(kernel="precomputed", C=C).fit(K_tr, data.y_train).predict(K_te)
            rows.append({
                "feature_map": fm, "bandwidth": bw,
                "accuracy": round(float(accuracy_score(data.y_test, pred)), 4),
                "f1": round(float(f1_score(data.y_test, pred, average="macro", zero_division=0)), 4),
                "depth": stats["depth"], "gate_count": stats["gate_count"],
                "kernel_time_s": round(k_time, 3),
            })
    return {
        "config": {"dataset": dataset, "n_qubits": n_qubits, "reps": reps, "seed": seed,
                   "max_samples": max_samples, "test_size": test_size},
        "classical_rbf_accuracy": rbf_acc,
        "rows": rows,
    }
