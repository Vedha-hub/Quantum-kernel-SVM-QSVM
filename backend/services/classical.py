"""Step 2: classical baselines. Without these, a quantum score means nothing."""
import time

from sklearn.svm import SVC


def run_classical(X_train, y_train, X_test, kernel: str = "rbf", C: float = 1.0):
    t0 = time.perf_counter()
    model = SVC(kernel=kernel, C=C, gamma="scale")
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - t0
    return model.predict(X_test), train_time
