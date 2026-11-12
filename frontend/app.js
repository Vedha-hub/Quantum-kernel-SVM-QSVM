// Frontend logic. No build tools needed: the browser talks to the FastAPI backend with fetch().

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const MAP_COLORS = { angle: "#5b3fd9", z: "#0f7f72", zz: "#c97b00", entangled_ry: "#c2377a" };

let options = null;

// ---------- Talking to the backend ----------
async function api(path, body) {
  const res = await fetch(path, body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    : undefined);
  if (!res.ok) {
    let msg = `Request failed (${res.status}).`;
    try { const e = await res.json(); msg = typeof e.detail === "string" ? e.detail : "Some settings are out of range. Check the sliders and try again."; } catch (_) {}
    throw new Error(msg);
  }
  return res.json();
}

function setBusy(busy, text = "") {
  $("run-btn").disabled = busy;
  $("sweep-btn").disabled = busy;
  $("status").className = "";
  $("status").textContent = text;
}
function showError(err) {
  $("status").className = "error";
  $("status").textContent = `${err.message} Make sure the backend is running (uvicorn backend.main:app --reload).`;
  $("run-btn").disabled = false;
  $("sweep-btn").disabled = false;
}

// ---------- Controls ----------
function readSettings() {
  return {
    dataset: $("dataset").value,
    feature_map: $("feature_map").value,
    n_qubits: +$("n_qubits").value,
    reps: +$("reps").value,
    bandwidth: +$("bandwidth").value,
    max_samples: +$("max_samples").value,
    test_size: +$("test_size").value,
  };
}

function bindSliders() {
  for (const id of ["n_qubits", "reps", "bandwidth", "max_samples", "test_size"]) {
    const update = () => ($(id + "_out").textContent = $(id).value);
    $(id).addEventListener("input", update);
    update();
  }
}

async function init() {
  bindSliders();
  try {
    options = await api("/api/options");
  } catch (e) { return showError(e); }
  $("dataset").innerHTML = options.datasets.map((d) => `<option value="${esc(d.name)}">${esc(d.name.replace("_", " "))}</option>`).join("");
  $("feature_map").innerHTML = options.feature_maps.map((m) => `<option value="${esc(m.name)}" ${m.name === "angle" ? "selected" : ""}>${esc(m.name)}</option>`).join("");
  const showHints = () => {
    $("dataset-hint").textContent = options.datasets.find((d) => d.name === $("dataset").value).description;
    $("map-hint").textContent = options.feature_maps.find((m) => m.name === $("feature_map").value).description;
  };
  $("dataset").addEventListener("change", showHints);
  $("feature_map").addEventListener("change", showHints);
  showHints();
  refreshHistory();
}

// ---------- Single run ----------
async function runExperiment() {
  setBusy(true, "Running the circuit for every sample...");
  try {
    const r = await api("/api/run", readSettings());
    renderRun(r);
    setBusy(false, "Done.");
    refreshHistory();
  } catch (e) { showError(e); }
}

function renderRun(r) {
  $("empty").hidden = true;
  $("output").hidden = false;
  const res = r.results;

  const rows = [
    ["Quantum SVM", res.qsvm.accuracy, css("--quantum")],
    ["Classical RBF", res.classical_rbf.accuracy, css("--classical")],
    ["Classical linear", res.classical_linear.accuracy, css("--linear")],
  ];
  $("bars").innerHTML = rows.map(([name, v, color]) => `
    <div class="bar-row"><span>${name}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(v * 100).toFixed(1)}%;background:${color}"></div></div>
      <span class="bar-val">${(v * 100).toFixed(1)}%</span></div>`).join("");

  const diff = (res.qsvm.accuracy - res.classical_rbf.accuracy) * 100;
  $("verdict").textContent = diff > 0.5
    ? `The quantum kernel beat the classical RBF kernel by ${diff.toFixed(1)} points on this split.`
    : diff < -0.5
      ? `The classical RBF kernel scored ${(-diff).toFixed(1)} points higher. Try a smaller bandwidth or a different feature map.`
      : "The quantum and classical kernels scored about the same on this split.";

  drawHeatmap(r.kernel_heatmap);

  const metric = (m) => `<tr><td>${m.name}</td><td>${m.d.accuracy}</td><td>${m.d.precision}</td><td>${m.d.recall}</td><td>${m.d.f1}</td><td>${m.d.fit_time_s}s${m.d.kernel_time_s !== undefined ? ` + ${m.d.kernel_time_s}s kernel` : ""}</td></tr>`;
  $("metrics").innerHTML = `<tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Time</th></tr>` +
    metric({ name: "Quantum SVM", d: res.qsvm }) + metric({ name: "Classical RBF", d: res.classical_rbf }) + metric({ name: "Classical linear", d: res.classical_linear });

  $("confusions").innerHTML = [["Quantum SVM", res.qsvm], ["Classical RBF", res.classical_rbf]].map(([title, d]) => `
    <div class="conf"><h3>${title}</h3><table>${d.confusion_matrix.map((row) =>
      `<tr>${row.map((v) => `<td>${v}</td>`).join("")}</tr>`).join("")}</table>
      <p class="hint">Rows are true classes, columns are predictions.</p></div>`).join("");

  $("circuit-stats").textContent = `${r.circuit.qubits} qubits, depth ${r.circuit.depth}, ${r.circuit.gate_count} gates. PCA kept ${(r.data.pca_explained_variance * 100).toFixed(0)}% of the data variance. Trained on ${r.data.n_train} samples, tested on ${r.data.n_test}.`;
  $("diagram").textContent = r.circuit.diagram;
}

function drawHeatmap({ values }) {
  const canvas = $("heat");
  const ctx = canvas.getContext("2d");
  const n = values.length;
  const cell = canvas.width / n;
  const lo = hexToRgb(css("--canvas")), hi = hexToRgb(css("--quantum"));
  values.forEach((row, i) => row.forEach((v, j) => {
    const t = Math.min(1, Math.max(0, v));
    ctx.fillStyle = `rgb(${lerp(lo[0], hi[0], t)},${lerp(lo[1], hi[1], t)},${lerp(lo[2], hi[2], t)})`;
    ctx.fillRect(j * cell, i * cell, Math.ceil(cell), Math.ceil(cell));
  }));
}
const lerp = (a, b, t) => Math.round(a + (b - a) * t);
function hexToRgb(h) { const n = parseInt(h.replace("#", ""), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }

// ---------- Sweep (compare all feature maps) ----------
async function runSweep() {
  const s = readSettings();
  setBusy(true, "Testing 4 feature maps at 4 bandwidths. This takes a few seconds...");
  try {
    const r = await api("/api/sweep", { dataset: s.dataset, n_qubits: Math.min(s.n_qubits, 6), reps: Math.min(s.reps, 3), max_samples: Math.min(s.max_samples, 200) });
    renderSweep(r);
    setBusy(false, "Comparison finished.");
  } catch (e) { showError(e); }
}

function renderSweep(r) {
  $("sweep-panel").hidden = false;
  $("sweep-note").textContent = `Dashed line: classical RBF SVM at ${(r.classical_rbf_accuracy * 100).toFixed(1)}%. Each line is one quantum feature map. Highest accuracy per map is in bold.`;
  const bws = [...new Set(r.rows.map((x) => x.bandwidth))];
  const maps = [...new Set(r.rows.map((x) => x.feature_map))];

  const W = 640, H = 320, L = 52, R = 20, T = 20, B = 48;
  const x = (i) => L + (i * (W - L - R)) / (bws.length - 1);
  const y = (v) => T + (1 - v) * (H - T - B);
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Accuracy by bandwidth for each feature map">`;
  for (let v = 0; v <= 1.001; v += 0.25) svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="${css("--line")}"/><text class="chart-label" x="${L - 8}" y="${y(v) + 4}" text-anchor="end">${(v * 100).toFixed(0)}%</text>`;
  bws.forEach((b, i) => (svg += `<text class="chart-label" x="${x(i)}" y="${H - 22}" text-anchor="middle">${b}</text>`));
  svg += `<text class="chart-label" x="${(L + W - R) / 2}" y="${H - 4}" text-anchor="middle">Bandwidth</text>`;
  svg += `<line x1="${L}" x2="${W - R}" y1="${y(r.classical_rbf_accuracy)}" y2="${y(r.classical_rbf_accuracy)}" stroke="${css("--ink")}" stroke-dasharray="6 5"/>`;
  maps.forEach((m) => {
    const pts = bws.map((b, i) => [x(i), y(r.rows.find((q) => q.feature_map === m && q.bandwidth === b).accuracy)]);
    svg += `<polyline fill="none" stroke="${MAP_COLORS[m]}" stroke-width="2.5" points="${pts.map((p) => p.join(",")).join(" ")}"/>`;
    pts.forEach((p) => (svg += `<circle cx="${p[0]}" cy="${p[1]}" r="4" fill="${MAP_COLORS[m]}"/>`));
  });
  svg += "</svg>";
  const legend = maps.map((m) => `<span style="color:${MAP_COLORS[m]};font-weight:600;margin-right:1.2rem">${m}</span>`).join("");
  $("sweep-chart").innerHTML = legend + svg;

  const best = {};
  r.rows.forEach((row) => { if (!best[row.feature_map] || row.accuracy > best[row.feature_map]) best[row.feature_map] = row.accuracy; });
  $("sweep-table").innerHTML = `<tr><th>Feature map</th><th>Bandwidth</th><th>Accuracy</th><th>F1</th><th>Depth</th><th>Gates</th><th>Kernel time</th></tr>` +
    r.rows.map((q) => `<tr><td>${esc(q.feature_map)}</td><td>${q.bandwidth}</td><td class="${q.accuracy === best[q.feature_map] ? "best" : ""}">${q.accuracy}</td><td>${q.f1}</td><td>${q.depth}</td><td>${q.gate_count}</td><td>${q.kernel_time_s}s</td></tr>`).join("");
  $("sweep-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- History ----------
async function refreshHistory() {
  try {
    const h = await api("/api/history?limit=10");
    $("history").innerHTML = h.length === 0
      ? `<tr><td>No runs saved yet. Run an experiment and it will appear here.</td></tr>`
      : `<tr><th>Time (UTC)</th><th>Dataset</th><th>Map</th><th>Qubits</th><th>Bandwidth</th><th>Quantum</th><th>RBF</th></tr>` +
        h.map((x) => `<tr><td>${esc(x.timestamp.replace("T", " ").slice(0, 16))}</td><td>${esc(x.config.dataset)}</td><td>${esc(x.config.feature_map)}</td><td>${x.config.n_qubits}</td><td>${x.config.bandwidth}</td><td>${x.qsvm_accuracy}</td><td>${x.rbf_accuracy}</td></tr>`).join("");
  } catch (_) { /* history is optional */ }
}

$("run-btn").addEventListener("click", runExperiment);
$("sweep-btn").addEventListener("click", runSweep);
init();
