# QSVM Capstone: Team Plan

Read this file top to bottom once. Then use it as a checklist.

---

## Part 1. Roles (3 people)

Each person owns one folder, so you almost never edit the same file at the same time.
This is how real teams avoid git conflicts.

| Person | Owns these files | Main job |
|---|---|---|
| Person A | `backend/services/data.py`, `classical.py`, `tests/` | Data pipeline, classical baselines, tests |
| Person B | `backend/services/quantum.py`, `evaluate.py`, `scripts/` | Quantum feature maps, kernel, experiments, graphs |
| Person C | `frontend/`, `backend/main.py`, `schemas.py`, `README.md` | Web app, API, report and slides |

Rule: everyone must be able to explain the whole pipeline. Viva questions can go to anyone.

---

## Part 2. Git and GitHub, step by step

### 2.1 One-time setup (Person C does this, about 10 minutes)

1. Go to github.com and select **New repository**.
2. Name it `qsvm-capstone`. Choose **Private**. Do NOT tick "Add a README".
3. In the repository, open **Settings > Collaborators** and invite the other two.
4. Put the project folder on your laptop and open a terminal inside it.
5. Run these commands one by one:

```bash
git init
git add .
git commit -m "chore: initial project structure"
git branch -M main
git remote add origin https://github.com/<your-username>/qsvm-capstone.git
git push -u origin main
```

6. Create the `develop` branch and push it:

```bash
git checkout -b develop
git push -u origin develop
```

### 2.2 Setup for the other two people

```bash
git clone https://github.com/<owner-username>/qsvm-capstone.git
cd qsvm-capstone
git checkout develop
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

If `pytest` shows `6 passed`, your setup is correct.

### 2.3 Branch rules

- `main` = the stable version you submit. Nobody commits to it directly.
- `develop` = where finished work is combined.
- `feature/<short-name>` = your own working branch. Examples: `feature/data-pipeline`, `feature/zz-map`, `feature/frontend-heatmap`.

### 2.4 Daily workflow (repeat for every task)

```bash
# 1. Get the latest code
git checkout develop
git pull

# 2. Start a new branch for your task
git checkout -b feature/zz-map

# 3. Work. Run tests often.
pytest -q

# 4. Save your work
git add .
git commit -m "feat: add ZZ feature map with bandwidth option"

# 5. Upload your branch
git push -u origin feature/zz-map
```

6. On GitHub, open a **Pull Request** from your branch into `develop`.
7. A teammate reads it, leaves comments, and presses **Approve**.
8. Merge the pull request. Then locally run `git checkout develop` and `git pull`.

### 2.5 Commit message style

Start with a word that says what kind of change it is:

| Start with | Meaning | Example |
|---|---|---|
| `feat:` | new feature | `feat: add kernel heatmap to frontend` |
| `fix:` | bug fix | `fix: handle 2 qubit case in ring entanglement` |
| `test:` | tests | `test: check kernel is symmetric` |
| `docs:` | documentation | `docs: add worked kernel example` |
| `chore:` | setup, cleanup | `chore: update requirements` |

### 2.6 If you get a merge conflict

1. Run `git pull origin develop` on your branch.
2. Git marks the clashing lines with `<<<<<<<`, `=======`, `>>>>>>>`.
3. Open the file, keep the correct lines, delete the markers.
4. Run `git add <file>`, then `git commit`, then `pytest -q`.

### 2.7 Release

When the project is finished and tests pass:

```bash
git checkout main
git merge develop
git tag v1.0
git push origin main --tags
```

The file `.github/workflows/ci.yml` runs `pytest` automatically on every push. A green tick on
GitHub means the tests pass. Show this in your viva.

---

## Part 3. Timeline (6 weeks)

| Week | Goal | Person A | Person B | Person C |
|---|---|---|---|---|
| 1 | Setup and understand | Clone, run, read `data.py` | Read `quantum.py`, explain feature maps to team | Create repo, run web app |
| 2 | Baselines | Add a new dataset or change preprocessing | Check kernel by hand (Part 4) | Customise frontend text and colours |
| 3 | Quantum experiments | Write extra tests | Add your own feature map | Add a new chart to the frontend |
| 4 | Full comparison | Run sweeps on all 3 datasets | Run sweeps on 4, 6 qubits | Collect screenshots and tables |
| 5 | Analysis and report | Write the Data and Baseline sections | Write the Method and Results sections | Write Intro, Limitations, Conclusion |
| 6 | Polish and viva | Practise viva questions | Practise viva questions | Make slides and rehearse the live demo |

Tip: the code in this folder already works. Your job is to understand it, extend it, run proper
experiments, and explain the results. Evaluators care most about the analysis.

---

## Part 4. Worked example: calculating a quantum kernel by hand

Use this in your report and viva. It shows you understand the maths, not just the code.

**Setup:** 1 qubit, angle feature map with 1 repeat. The circuit is a single `RY(x)` gate.

**Step 1. State for input x.**
`|phi(x)> = RY(x)|0> = cos(x/2)|0> + sin(x/2)|1>`

**Step 2. State for input y.**
`|phi(y)> = cos(y/2)|0> + sin(y/2)|1>`

**Step 3. Inner product.**
`<phi(x)|phi(y)> = cos(x/2)cos(y/2) + sin(x/2)sin(y/2) = cos((x - y)/2)`

(This uses the identity cos(A - B) = cos A cos B + sin A sin B.)

**Step 4. Kernel is the squared magnitude.**
`k(x, y) = cos^2((x - y)/2)`

**Step 5. Plug in numbers.**

| x | y | x - y | k(x, y) | Meaning |
|---|---|---|---|---|
| 0 | 0 | 0 | cos^2(0) = **1.0** | Identical points |
| 0 | pi/2 | -pi/2 | cos^2(pi/4) = **0.5** | Partly similar |
| 0 | pi | -pi | cos^2(pi/2) = **0.0** | Completely different |

**Step 6. For n qubits** (no entanglement, 1 repeat), the kernel is a product:
`k(x, y) = product over i of cos^2((x_i - y_i)/2)`.

The test `test_angle_map_matches_hand_formula` in `tests/test_pipeline.py` checks that the
code agrees with this formula. Run it and show it to your examiner.

---

## Part 5. Experiments to run for the report

Run each one with `python scripts/run_experiments.py` or with the web app.

1. **Feature map comparison.** All 4 maps, same dataset, same qubits. Record accuracy and circuit depth.
2. **Bandwidth study.** Accuracy against bandwidth (0.1, 0.25, 0.5, 1.0). In our own test runs, the ZZ map
   scored high at small bandwidth and dropped sharply at bandwidth 1.0. Check whether you see the same.
   A likely reason: large angles make all states nearly orthogonal, so every pair looks "different"
   and the kernel stops carrying useful information.
3. **Qubit count study.** 2, 4, 6 qubits on one dataset. Record accuracy and kernel time. Time grows quickly with qubits.
4. **Dataset comparison.** Iris, wine, breast cancer.
5. **Repeats study.** 1, 2, 3 repeats of the circuit.

For every experiment, record **accuracy, F1, circuit depth, gate count and kernel time**.

Extensions if you have time (pick at most one):

- Add a noisy simulator with Qiskit Aer and show how accuracy drops (links to Module III, decoherence).
- Cross-check one result using `FidelityQuantumKernel` and `QSVC` from `qiskit-machine-learning`.
- Repeat with 5 different random seeds and report mean and standard deviation.

---

## Part 6. Report outline

1. **Introduction.** Problem, motivation, objectives.
2. **Background.** Qubits, superposition, entanglement, feature maps, kernels, SVM.
3. **Method.** Dataset, preprocessing, circuits, kernel formula, SVM, evaluation metrics.
4. **Implementation.** Architecture diagram (frontend, API, services), tools used, git workflow.
5. **Results.** Tables and graphs from Part 5. Quantum against classical.
6. **Discussion.** Why results look the way they do. Be honest if quantum did not win.
7. **Limitations and future work.** Simulator only, small qubit counts, small datasets, noise.
8. **Conclusion.**
9. **References.** Nielsen and Chuang; Schuld and Petruccione; Qiskit documentation.

---

## Part 7. Viva questions with worked answers

**Q1. What is a quantum kernel?**
A. It is a similarity score between two data points, computed with a quantum circuit.
We encode each point x into a state |phi(x)> and compute k(x, y) = |<phi(x)|phi(y)>|^2.
The value is 1 for identical states and 0 for orthogonal states.

**Q2. Why do we use PCA before the circuit?**
A. Our feature maps use one qubit per feature. Breast cancer has 30 features, which would need
30 qubits. PCA keeps the most informative directions in just 4 features, so the circuit stays small enough to simulate.

**Q3. Why do you scale data to the range 0 to pi?**
A. Features become rotation angles. Angles repeat every 2 pi, so unscaled data could map two different
values to the same state. Scaling to [0, pi] keeps different values distinguishable.

**Q4. Where is superposition used in your project?**
A. The Hadamard gate in the Z and ZZ feature maps puts each qubit into an equal superposition of |0> and |1>.
Phase gates then rotate each amplitude depending on the data value.

**Q5. Where is entanglement used?**
A. In the ZZ map (CNOT, phase, CNOT blocks) and the entangled RY map (CNOT ring). These create
correlations between qubits, so the kernel depends on products of features, not on each feature alone.
The angle and Z maps have no entanglement.

**Q6. Why can the quantum model score lower than the classical RBF SVM?**
A. The choice of feature map and bandwidth strongly affects the kernel. With a poorly matched map the
kernel is either too flat or too sharp. Also, the datasets are small and low-dimensional,
which is exactly where a classical RBF kernel already does very well. We do not claim quantum advantage.

**Q7. Is your simulation real quantum computing?**
A. No. It is an exact classical simulation of an ideal quantum circuit (Qiskit `Statevector`). It
shows what a noiseless quantum computer would compute. On real hardware we would estimate each kernel value
from many measurements (shots) and deal with noise.

**Q8. Why does the simulation get slow with more qubits?**
A. A state of n qubits has 2^n amplitudes. 4 qubits need 16 numbers; 20 qubits need over a million.
We stay at 2 to 8 qubits.

**Q9. How does the SVM use the kernel matrix?**
A. We pass `kernel="precomputed"` to scikit-learn `SVC`. Training uses the matrix of
train-by-train similarities. Prediction uses the test-by-train similarities.

**Q10. How do you prevent data leakage?**
A. The scaler and PCA are fitted on training data only, then applied to test data. Test data never influences preprocessing.

**Q11. What is the role of the API (backend)?**
A. The frontend never runs quantum code. It sends settings as JSON to `/api/run`. The backend
validates them, runs the experiment, and returns results as JSON. This separation is how real web applications are built.

**Q12. What does the kernel heatmap show?**
A. Pairwise similarity of training samples, sorted by class. Bright blocks on the diagonal mean
samples of the same class look similar to the circuit, which is what an SVM needs.

---

## Part 8. Final checklist before submission

- [ ] `pytest -q` shows all tests passing
- [ ] GitHub shows a green tick for the latest commit
- [ ] Every team member has at least 5 commits and 1 pull request
- [ ] `README.md` has your names and roles
- [ ] Graphs and CSVs from Part 5 are in `results/`
- [ ] Report and slides are done
- [ ] The web app starts with one command and the demo is rehearsed
- [ ] Each person can explain the whole pipeline
