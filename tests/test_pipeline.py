import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.data import prepare_data
from backend.services.quantum import FEATURE_MAPS, build_feature_map, kernel_matrix

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_data_shapes_and_range():
    d = prepare_data("iris", n_qubits=3, max_samples=100)
    assert d.X_train.shape[1] == 3
    assert d.X_train.min() >= -1e-9 and d.X_train.max() <= np.pi + 1e-9


def test_kernel_properties():
    """A valid quantum kernel is symmetric, has 1s on the diagonal, and values in [0, 1]."""
    rng = np.random.default_rng(0)
    X = rng.uniform(0, np.pi, size=(8, 3))
    for name in FEATURE_MAPS:
        K = kernel_matrix(build_feature_map(name, 3, 2), X)
        assert np.allclose(K, K.T, atol=1e-9)
        assert np.allclose(np.diag(K), 1.0, atol=1e-9)
        assert K.min() >= -1e-9 and K.max() <= 1 + 1e-9
        assert np.linalg.eigvalsh(K).min() > -1e-8  # positive semi-definite


def test_run_endpoint():
    r = client.post("/api/run", json={"dataset": "iris", "n_qubits": 3, "feature_map": "angle"})
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["results"]["qsvm"]["accuracy"] <= 1
    assert "classical_rbf" in body["results"]


def test_bad_input_rejected():
    r = client.post("/api/run", json={"dataset": "iris", "n_qubits": 50})
    assert r.status_code == 422


def test_angle_map_matches_hand_formula():
    """Worked example from the docs: with 1 repeat, the angle map kernel is
    k(x, y) = product over qubits of cos^2((x_i - y_i) / 2)."""
    rng = np.random.default_rng(1)
    X = rng.uniform(0, np.pi, size=(6, 3))
    K = kernel_matrix(build_feature_map("angle", 3, reps=1), X)
    expected = np.prod(np.cos((X[:, None, :] - X[None, :, :]) / 2) ** 2, axis=2)
    assert np.allclose(K, expected, atol=1e-9)
