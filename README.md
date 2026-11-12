# QSVM Lab: Quantum Kernel SVM for Classification

Capstone project for **Quantum Computing for AI (AIM3001 / AIM3001P)**, D Y Patil International University.

**Question we answer:** can a quantum feature map (a circuit that turns data into a quantum state) give
a better SVM kernel than a classical RBF kernel, and how do the choice of feature map and the data
scaling (bandwidth) change the answer?

Syllabus coverage: quantum feature maps, kernel methods, QSVM (Module IV); superposition and
entanglement, gates and circuits (Modules I, II); lab experiment 7 (quantum kernel classifier).

---

## 1. Project structure

```
qsvm-capstone/
├── backend/                 FastAPI server (the "brain")
│   ├── main.py              API routes + serves the frontend
│   ├── schemas.py           input validation
│   ├── storage.py           saves run history to results/runs.jsonl
│   └── services/
│       ├── data.py          load dataset, scale, PCA, map to angles
│       ├── classical.py     classical SVM baselines
│       ├── quantum.py       feature-map circuits + quantum kernel
│       └── evaluate.py      runs a full experiment / a sweep
├── frontend/                Web page (HTML + CSS + JavaScript)
├── scripts/run_experiments.py   Command-line sweep -> CSV + graph for the report
├── tests/                   Automated tests (pytest)
├── results/                 Generated CSVs and graphs
├── docs/PLAN.md             Team plan, timeline, git workflow, viva questions
└── .github/workflows/ci.yml Runs the tests on every push
```

## 2. Setup (do this once per person)

Needs **Python 3.10 or newer**.

```bash
git clone <your-repo-url>
cd qsvm-capstone

python -m venv .venv
# Windows:   .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
pytest -q            # should print: 6 passed
```

## 3. Run the web app

```bash
uvicorn backend.main:app --reload
```

- App: http://127.0.0.1:8000
- API docs (auto-generated): http://127.0.0.1:8000/docs

## 4. Run experiments without the web app

```bash
python scripts/run_experiments.py --dataset breast_cancer --qubits 4
```

This writes `results/sweep_breast_cancer_4q.csv` and a `.png` graph for the report.

## 5. API summary

| Method | Route | What it does |
|---|---|---|
| GET | `/api/health` | Check the server is alive |
| GET | `/api/options` | Datasets and feature maps available |
| POST | `/api/run` | One experiment: quantum SVM vs classical SVMs |
| POST | `/api/sweep` | All feature maps at several bandwidths |
| GET | `/api/history` | Last saved runs |

## 6. How it works (short version)

1. **Prepare data.** Scale, reduce with PCA to one feature per qubit, map to angles in [0, pi].
2. **Encode.** A feature-map circuit turns each sample `x` into a quantum state `|phi(x)>`.
3. **Kernel.** `k(x, y) = |<phi(x)|phi(y)>|^2` measures how similar two samples look to the circuit.
4. **Classify.** A classical SVM uses the kernel matrix to find the decision boundary.
5. **Compare.** Same data, same split, classical RBF and linear SVMs as baselines.

## 7. Using Google Colab instead of a laptop

```python
!git clone <your-repo-url>
%cd qsvm-capstone
!pip install -r requirements.txt
!python scripts/run_experiments.py --dataset iris --qubits 4
```

## 8. Team

Add names, roll numbers and roles here.
