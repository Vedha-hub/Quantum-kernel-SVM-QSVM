"""Step 3: the quantum part - feature maps and the quantum kernel.

Idea in one line:
    k(x, y) = |<phi(x)|phi(y)>|^2
where |phi(x)> is the state produced by running a feature-map circuit on data x.
The kernel matrix is then given to a classical SVM (kernel='precomputed').

We compute the states exactly with Qiskit's Statevector (an ideal simulator).
This gives the same numbers as Qiskit Machine Learning's FidelityQuantumKernel
on a noiseless simulator, but it is faster and easier to explain.
"""
import time

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector

FEATURE_MAPS = {
    "angle": "RY rotation per qubit. No entanglement. Simplest map.",
    "z": "H then phase rotation per qubit. No entanglement.",
    "zz": "Like Z map, plus ZZ entangling terms between qubits.",
    "entangled_ry": "RY rotations followed by a ring of CNOT gates.",
}


def build_feature_map(name: str, n_qubits: int, reps: int = 2) -> QuantumCircuit:
    """Return a parameterised circuit. Parameters x[0..n-1] hold the data."""
    if name not in FEATURE_MAPS:
        raise ValueError(f"Unknown feature map '{name}'. Choose from {list(FEATURE_MAPS)}")

    x = ParameterVector("x", n_qubits)
    qc = QuantumCircuit(n_qubits, name=f"{name}_map")

    for _ in range(reps):
        if name == "angle":
            for i in range(n_qubits):
                qc.ry(x[i], i)

        elif name == "z":
            for i in range(n_qubits):
                qc.h(i)
                qc.p(2 * x[i], i)

        elif name == "zz":
            for i in range(n_qubits):
                qc.h(i)
                qc.p(2 * x[i], i)
            for i in range(n_qubits - 1):
                j = i + 1
                qc.cx(i, j)
                qc.p(2 * (np.pi - x[i]) * (np.pi - x[j]), j)
                qc.cx(i, j)

        elif name == "entangled_ry":
            for i in range(n_qubits):
                qc.ry(x[i], i)
            for i in range(n_qubits - 1):
                qc.cx(i, i + 1)
            if n_qubits > 2:
                qc.cx(n_qubits - 1, 0)
        qc.barrier()
    return qc


def circuit_drawing(name: str, n_qubits: int, reps: int) -> str:
    """Text diagram of the circuit (shown on the frontend)."""
    return str(build_feature_map(name, n_qubits, reps).draw(output="text", fold=120))


def circuit_stats(name: str, n_qubits: int, reps: int) -> dict:
    qc = build_feature_map(name, n_qubits, reps).decompose()
    ops = qc.count_ops()
    return {
        "qubits": n_qubits,
        "depth": qc.depth(),
        "gate_count": int(sum(v for k, v in ops.items() if k != "barrier")),
    }


def _states(qc: QuantumCircuit, X: np.ndarray) -> np.ndarray:
    """Statevector for every sample -> matrix of shape (n_samples, 2**n_qubits)."""
    out = []
    for row in X:
        bound = qc.assign_parameters(row)
        out.append(Statevector.from_instruction(bound).data)
    return np.array(out)


def kernel_matrix(qc: QuantumCircuit, A: np.ndarray, B: np.ndarray | None = None) -> np.ndarray:
    """k(a, b) = |<phi(a)|phi(b)>|^2 for all pairs."""
    SA = _states(qc, A)
    SB = SA if B is None else _states(qc, B)
    overlap = SA @ SB.conj().T
    return np.abs(overlap) ** 2


def compute_kernels(name: str, n_qubits: int, reps: int, X_train, X_test):
    """Return (K_train, K_test, seconds_taken)."""
    qc = build_feature_map(name, n_qubits, reps)
    t0 = time.perf_counter()
    K_train = kernel_matrix(qc, X_train)
    K_test = kernel_matrix(qc, X_test, X_train)  # shape (n_test, n_train)
    return K_train, K_test, time.perf_counter() - t0
