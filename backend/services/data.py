"""Step 1 of the pipeline: load a dataset and prepare it for a quantum circuit.

Why each step exists (good viva answers):
  - StandardScaler : puts every feature on the same scale.
  - PCA            : a circuit needs 1 qubit per feature, so we shrink the
                     data down to `n_qubits` features.
  - MinMaxScaler   : rotation gates take angles, so we map features to [0, pi].
  - Scalers/PCA are fitted on TRAIN data only, to avoid data leakage.
"""
from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_breast_cancer, load_iris, load_wine
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler

DATASETS = {
    "iris": {
        "loader": load_iris,
        "description": "3 flower species, 4 features, 150 samples",
    },
    "wine": {
        "loader": load_wine,
        "description": "3 wine classes, 13 features, 178 samples",
    },
    "breast_cancer": {
        "loader": load_breast_cancer,
        "description": "Benign vs malignant tumour, 30 features, 569 samples",
    },
}


@dataclass
class PreparedData:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    class_names: list
    explained_variance: float


def list_datasets() -> list[dict]:
    return [{"name": k, "description": v["description"]} for k, v in DATASETS.items()]


def prepare_data(
    dataset: str,
    n_qubits: int = 4,
    test_size: float = 0.25,
    max_samples: int = 120,
    seed: int = 42,
) -> PreparedData:
    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset '{dataset}'. Choose from {list(DATASETS)}")

    raw = DATASETS[dataset]["loader"]()
    X, y = raw.data, raw.target
    class_names = [str(c) for c in raw.target_names]

    # Keep runs fast: take a stratified subset if the dataset is large.
    if max_samples and len(X) > max_samples:
        X, _, y, _ = train_test_split(
            X, y, train_size=max_samples, stratify=y, random_state=seed
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )

    n_components = min(n_qubits, X_train.shape[1])
    scaler = StandardScaler().fit(X_train)
    pca = PCA(n_components=n_components, random_state=seed).fit(scaler.transform(X_train))
    angle_scaler = MinMaxScaler(feature_range=(0, np.pi))

    def transform(A):
        return pca.transform(scaler.transform(A))

    X_train_p = angle_scaler.fit_transform(transform(X_train))
    # Test values can fall slightly outside [0, pi]; that is fine and realistic.
    X_test_p = angle_scaler.transform(transform(X_test))

    return PreparedData(
        X_train=X_train_p,
        X_test=X_test_p,
        y_train=y_train,
        y_test=y_test,
        class_names=class_names,
        explained_variance=float(pca.explained_variance_ratio_.sum()),
    )
