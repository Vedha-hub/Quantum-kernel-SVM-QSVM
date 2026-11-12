"""Request/response shapes. FastAPI uses these to validate input automatically."""
from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    dataset: Literal["iris", "wine", "breast_cancer"] = "iris"
    n_qubits: int = Field(4, ge=2, le=8)
    feature_map: Literal["angle", "z", "zz", "entangled_ry"] = "zz"
    reps: int = Field(2, ge=1, le=4)
    bandwidth: float = Field(0.5, gt=0, le=2)
    test_size: float = Field(0.25, gt=0.05, lt=0.5)
    max_samples: int = Field(120, ge=30, le=300)
    C: float = Field(1.0, gt=0, le=100)
    seed: int = 42


class SweepRequest(BaseModel):
    dataset: Literal["iris", "wine", "breast_cancer"] = "iris"
    n_qubits: int = Field(4, ge=2, le=6)
    reps: int = Field(2, ge=1, le=3)
    max_samples: int = Field(120, ge=30, le=200)
    seed: int = 42
