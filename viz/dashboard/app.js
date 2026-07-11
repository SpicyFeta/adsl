/** ADSL Visualization Dashboard — ADR-009 exports + analytics overlay */

const RISK_RING_COLORS = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#64748b",
};

const state = {
  runs: [],
  payload: null,
  insights: null,
  comparison: null,
  highlightedEntity: null,
  transform: { x: 0, y: 0, scale: 1 },
  dragging: false,
  lastPointer: null,
};

async function fetchRuns() {
  const response = await fetch("/api/runs");
  if (!response.ok) throw new Error("Failed to load runs");
  return response.json();
}

async function fetchViz(runId) {
  const response = await fetch(`/api/viz/${runId}`);
  if (!response.ok) throw new Error(`Failed to load run ${runId}`);
  return response.json();
}

async function fetchInsights(runId) {
  const response = await fetch(`/api/insights/${runId}`);
  if (!response.ok) throw new Error(`Failed to load insights for ${runId}`);
  return response.json();
}

async function fetchAnnotations(runId) {
  const response = await fetch(`/api/annotations/${runId}`);
  if (!response.ok) throw new Error(`Failed to load annotations for ${runId}`);
  return response.json();
}

async function fetchComparison(baselineId, compareId) {
  const response = await fetch(
    `/api/compare?baseline=${encodeURIComponent(baselineId)}&compare=${encodeURIComponent(compareId)}`
  );
  if (!response.ok) throw new Error("Failed to load comparison");
  return response.json();
}

function getFilters() {
  return {
    contestedOnly: document.getElementById("filter-contested").checked,
    highlightBottlenecks: document.getElementById("filter-bottlenecks").checked,
    hideOpen: document.getElementById("filter-hide-open").checked,
    highRiskOnly: document.getElementById("filter-high-risk").checked,
    focusAreas: document.getElementById("filter-focus-areas").checked,
    redActivity: document.getElementById("filter-red-activity").checked,
    showRiskScores: document.getElementById("filter-show-risk-scores").checked,
  };
}

function projectNodes(nodes, bounds, width, height, padding = 48) {
  const latSpan = bounds.max_lat - bounds.min_lat || 1;
  const lngSpan = bounds.max_lng - bounds.min_lng || 1;
  const positions = {};

  nodes.forEach((node) => {
    const x = padding + ((node.longitude - bounds.min_lng) / lngSpan) * (width - 2 * padding);
    const y = padding + ((bounds.max_lat - node.latitude) / latSpan) * (height - 2 * padding);
    positions[node.id] = { x, y };
  });

  return positions;
}

function entityPassesRiskFilter(entity, filters) {
  if (!filters.highRiskOnly) return true;
  return (entity.risk_score || 0) >= 45;
}

function routeVisible(route, filters) {
  if (!entityPassesRiskFilter(route, filters)) return false;
  if (filters.hideOpen && route.status === "OPEN") return false;
  if (filters.contestedOnly && route.status !== "CONTESTED") return false;
  if (filters.focusAreas && !route.is_focus_area) return false;
  return true;
}

function nodeVisible(node, filters) {
  if (!entityPassesRiskFilter(node, filters)) return true;
  return true;
}

function isWorsened(kind, id) {
  if (!state.comparison) return false;
  const key = kind === "node" ? "worsened_node_ids" : "worsened_route_ids";
  return (state.comparison[key] || []).includes(id);
}

function appendRiskRing(g, pos, radius, severity) {
  if (!severity || severity === "low") return;
  const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  ring.setAttribute("cx", pos.x);
  ring.setAttribute("cy", pos.y);
  ring.setAttribute("r", radius + 7);
  ring.setAttribute("fill", "none");
  ring.setAttribute("stroke", RISK_RING_COLORS[severity] || RISK_RING_COLORS.low);
  ring.setAttribute("stroke-width", severity === "critical" ? 3 : 2);
  ring.setAttribute("stroke-opacity", "0.85");
  g.appendChild(ring);
}

function appendFocusMarker(g, pos, radius) {
  const marker = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
  const size = radius + 10;
  const points = [
    `${pos.x},${pos.y - size}`,
    `${pos.x + size * 0.75},${pos.y}`,
    `${pos.x},${pos.y + size}`,
    `${pos.x - size * 0.75},${pos.y}`,
  ].join(" ");
  marker.setAttribute("points", points);
  marker.setAttribute("fill", "none");
  marker.setAttribute("stroke", "#a78bfa");
  marker.setAttribute("stroke-width", 2);
  marker.setAttribute("stroke-dasharray", "4 3");
  g.appendChild(marker);
}

function appendRiskBadge(g, pos, score, offsetY = -14) {
  const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
  text.setAttribute("x", pos.x);
  text.setAttribute("y", pos.y + offsetY);
  text.setAttribute("text-anchor", "middle");
  text.setAttribute("fill", "#f8fafc");
  text.setAttribute("font-size", "9");
  text.setAttribute("font-weight", "700");
  text.textContent = Math.round(score);
  g.appendChild(text);
}

function renderMap(payload) {
  const svg = document.getElementById("network-map");
  const container = document.getElementById("map-container");
  const width = container.clientWidth;
  const height = Math.max(container.clientHeight, 520);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = "";

  if (!payload) return;

  const filters = getFilters();
  const positions = projectNodes(payload.nodes, payload.bounds, width, height);
  const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("id", "map-layer");
  g.setAttribute(
    "transform",
    `translate(${state.transform.x}, ${state.transform.y}) scale(${state.transform.scale})`
  );
  svg.appendChild(g);

  const highlighted = state.highlightedEntity;

  payload.routes.forEach((route) => {
    if (!routeVisible(route, filters)) return;
    const source = positions[route.source_id];
    const target = positions[route.target_id];
    if (!source || !target) return;

    const riskWidth = 2 + Math.min((route.risk_score || 0) / 25, 4);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", source.x);
    line.setAttribute("y1", source.y);
    line.setAttribute("x2", target.x);
    line.setAttribute("y2", target.y);

    let stroke = route.color;
    if (route.risk_severity === "critical") stroke = "#ef4444";
    else if (route.risk_severity === "high" && route.status === "OPEN") stroke = "#fb923c";

    line.setAttribute("stroke", stroke);
    line.setAttribute(
      "stroke-width",
      filters.redActivity ? riskWidth + route.red_attacks * 0.3 : riskWidth
    );
    line.setAttribute("stroke-opacity", route.status === "CLOSED" ? 0.95 : 0.7);
    if (route.is_contested) line.setAttribute("stroke-dasharray", "6 4");
    if (isWorsened("route", route.id)) {
      line.setAttribute("stroke", "#c084fc");
      line.setAttribute("stroke-width", riskWidth + 2);
    }
    if (highlighted && highlighted.kind === "route" && highlighted.id === route.id) {
      line.setAttribute("stroke", "#38bdf8");
      line.setAttribute("stroke-width", riskWidth + 3);
    }

    line.dataset.kind = "route";
    line.dataset.id = route.id;
    line.style.cursor = "pointer";
    line.addEventListener("click", () => showSelection("route", route));
    g.appendChild(line);

    if (filters.showRiskScores && (route.risk_score || 0) >= 20) {
      const mid = { x: (source.x + target.x) / 2, y: (source.y + target.y) / 2 };
      appendRiskBadge(g, mid, route.risk_score, 0);
    }
  });

  payload.nodes.forEach((node) => {
    if (!nodeVisible(node, filters)) return;
    const pos = positions[node.id];
    if (!pos) return;

    if (filters.focusAreas && !node.is_focus_area && (node.risk_score || 0) < 45) return;

    const radius = filters.redActivity ? 8 + Math.min(node.red_attacks, 6) : 9;

    if (filters.highlightBottlenecks && node.is_bottleneck) {
      const ring = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      ring.setAttribute("cx", pos.x);
      ring.setAttribute("cy", pos.y);
      ring.setAttribute("r", radius + 5);
      ring.setAttribute("fill", "none");
      ring.setAttribute("stroke", "#38bdf8");
      ring.setAttribute("stroke-width", 2);
      g.appendChild(ring);
    }

    appendRiskRing(g, pos, radius, node.risk_severity);

    if ((filters.focusAreas || node.is_focus_area) && node.is_focus_area) {
      appendFocusMarker(g, pos, radius);
    }

    if (isWorsened("node", node.id)) {
      const worse = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      worse.setAttribute("cx", pos.x);
      worse.setAttribute("cy", pos.y);
      worse.setAttribute("r", radius + 9);
      worse.setAttribute("fill", "none");
      worse.setAttribute("stroke", "#c084fc");
      worse.setAttribute("stroke-width", 2.5);
      worse.setAttribute("stroke-dasharray", "3 2");
      g.appendChild(worse);
    }

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", radius);
    circle.setAttribute("fill", node.color);
    circle.setAttribute(
      "stroke",
      highlighted && highlighted.kind === "node" && highlighted.id === node.id
        ? "#38bdf8"
        : "#0f172a"
    );
    circle.setAttribute(
      "stroke-width",
      highlighted && highlighted.kind === "node" && highlighted.id === node.id ? 3 : 2
    );
    circle.dataset.kind = "node";
    circle.dataset.id = node.id;
    circle.style.cursor = "pointer";
    circle.addEventListener("click", () => showSelection("node", node));
    g.appendChild(circle);

    if (filters.showRiskScores && (node.risk_score || 0) >= 20) {
      appendRiskBadge(g, pos, node.risk_score, -radius - 6);
    }

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y - radius - (filters.showRiskScores ? 14 : 4));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "#cbd5e1");
    label.setAttribute("font-size", "10");
    label.textContent = node.name.split(" ").slice(0, 2).join(" ");
    g.appendChild(label);
  });
}

function renderBarChart(containerId, counts) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  const max = Math.max(...Object.values(counts), 1);
  const colors = {
    OPEN: "#22c55e",
    CONTESTED: "#f97316",
    CLOSED: "#ef4444",
    OPERATIONAL: "#22c55e",
    DEGRADED: "#eab308",
    DESTROYED: "#ef4444",
  };

  Object.entries(counts).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    const color = colors[label] || "#64748b";
    row.innerHTML = `
      <span class="bar-label">${label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(value / max) * 100}%; background:${color}"></div></div>
      <span class="bar-value">${value}</span>
    `;
    container.appendChild(row);
  });
}

function renderTopRisks(payload) {
  const container = document.getElementById("top-risks");
  const overlay = payload.analytics_overlay || {};
  const items = [
    ...(overlay.top_route_risks || []).map((r) => ({ ...r, kind: "route" })),
    ...(overlay.top_node_risks || []).map((n) => ({ ...n, kind: "node" })),
  ].sort((a, b) => b.risk_score - a.risk_score);

  if (!items.length) {
    container.innerHTML = '<div class="insight-empty">No elevated risks detected.</div>';
    return;
  }

  container.innerHTML = items
    .slice(0, 6)
    .map(
      (item) => `
      <div class="risk-item" data-kind="${item.kind}" data-id="${item.id}">
        <span class="risk-score">${Math.round(item.risk_score)}</span>
        <span class="risk-name">${item.name}</span>
        <span class="risk-kind">${item.kind}</span>
      </div>`
    )
    .join("");

  container.querySelectorAll(".risk-item").forEach((el) => {
    el.addEventListener("click", () => {
      const kind = el.dataset.kind;
      const id = el.dataset.id;
      highlightEntity(kind, id);
      const entity =
        kind === "node"
          ? payload.nodes.find((n) => n.id === id)
          : payload.routes.find((r) => r.id === id);
      if (entity) showSelection(kind, entity);
    });
  });
}

function highlightEntity(kind, id) {
  state.highlightedEntity = { kind, id };
  if (state.payload) renderMap(state.payload);
}

function renderMetrics(payload) {
  const m = payload.metrics;
  const cards = [
    { label: "Destroyed Nodes", value: m.destroyed_node_count },
    { label: "Closed Routes", value: m.route_status_counts.CLOSED || 0 },
    { label: "ATTACK_ROUTE", value: m.attack_route_count },
    { label: "NO_ACTION (Red)", value: m.no_action_count },
    { label: "HARDEN", value: m.harden_count },
    { label: "REROUTE", value: m.reroute_count },
  ];

  document.getElementById("metric-cards").innerHTML = cards
    .map(
      (card) => `
      <div class="metric-card">
        <div class="value">${card.value}</div>
        <div class="label">${card.label}</div>
      </div>`
    )
    .join("");

  renderBarChart("route-chart", m.route_status_counts);
  renderBarChart("node-chart", m.node_status_counts);
  renderTopRisks(payload);

  const red = payload.red_activity;
  document.getElementById("red-activity").innerHTML = `
    <div><strong>Total attacks:</strong> ${red.total_attacks}</div>
    <div><strong>By action:</strong> ${JSON.stringify(red.by_action)}</div>
    <div><strong>Top route targets:</strong> ${topEntries(red.route_attacks, 3)}</div>
    <div><strong>Top node targets:</strong> ${topEntries(red.node_attacks, 3)}</div>
  `;
}

function topEntries(map, limit) {
  const entries = Object.entries(map || {}).sort((a, b) => b[1] - a[1]).slice(0, limit);
  if (!entries.length) return "—";
  return entries.map(([k, v]) => `${k} (${v})`).join(", ");
}

function renderAnnotations(doc) {
  const container = document.getElementById("annotations-list");
  const items = doc.annotations || [];
  if (!items.length) {
    container.innerHTML = '<div class="annotation-empty">No team annotations for this run.</div>';
    return;
  }
  container.innerHTML = items
    .map((item) => {
      const target = item.target_kind || "run";
      const targetId = item.target_id || "—";
      const tick = item.simulation_tick != null ? ` · tick ${item.simulation_tick}` : "";
      return `<div class="annotation-item">
        <div class="annotation-meta"><strong>${item.author}</strong> · ${item.created_at}</div>
        <div class="annotation-target">${target}/${targetId}${tick}</div>
        <div class="annotation-text">${item.text}</div>
      </div>`;
    })
    .join("");
}

function renderInsights(report) {
  const renderList = (container, items, emptyText) => {
    if (!items || !items.length) {
      container.innerHTML = `<div class="insight-empty">${emptyText}</div>`;
      return;
    }
    container.innerHTML = items
      .map((item) => {
        if (typeof item === "string") {
          return `<div class="insight-item">${item}</div>`;
        }
        const severity = item.severity
          ? `<span class="severity ${item.severity}">${item.severity}</span>`
          : "";
        return `<div class="insight-item">${severity}${item.summary}</div>`;
      })
      .join("");
  };

  renderList(
    document.getElementById("key-insights"),
    report.key_insights,
    "No key insights generated."
  );
  renderList(
    document.getElementById("critical-highlights"),
    report.findings?.critical_highlights,
    "No critical highlights."
  );
  renderList(
    document.getElementById("corridor-risks"),
    report.findings?.corridor_risks?.slice(0, 4),
    "No corridor risk data."
  );

  const focusContainer = document.getElementById("focus-areas");
  const focusAreas = report.recommended_focus_areas || [];
  if (!focusAreas.length) {
    focusContainer.innerHTML = '<div class="insight-empty">No focus areas identified.</div>';
  } else {
    focusContainer.innerHTML = focusAreas
      .map(
        (item) =>
          `<div class="insight-item focus-item" data-entity-id="${item.entity_id}" data-entity-kind="${item.entity_kind}">
            <strong>${item.area}</strong> — ${item.rationale}
          </div>`
      )
      .join("");
    focusContainer.querySelectorAll(".focus-item").forEach((el) => {
      el.addEventListener("click", () => {
        const kind = el.dataset.entityKind === "route" ? "route" : "node";
        highlightEntity(kind, el.dataset.entityId);
      });
    });
  }

  renderList(
    document.getElementById("node-risks"),
    report.findings?.node_risks?.slice(0, 4),
    "No elevated node risk."
  );
}

function renderComparisonSummary() {
  const panel = document.getElementById("comparison-summary");
  const comp = state.comparison;
  if (!comp) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }

  panel.classList.remove("hidden");
  const baseLabel = comp.baseline.label || comp.baseline.run_id.slice(0, 8);
  const compareLabel = comp.compare.label || comp.compare.run_id.slice(0, 8);
  const deltas = comp.metric_deltas;

  panel.innerHTML = `
    <div class="compare-header">${compareLabel} vs ${baseLabel}</div>
    <div>Destroyed nodes: <strong>${deltas.destroyed_nodes >= 0 ? "+" : ""}${deltas.destroyed_nodes}</strong></div>
    <div>Closed routes: <strong>${deltas.closed_routes >= 0 ? "+" : ""}${deltas.closed_routes}</strong></div>
    <div>Worsened nodes: <strong>${comp.worsened_node_ids.length}</strong></div>
    <div>Worsened routes: <strong>${comp.worsened_route_ids.length}</strong></div>
  `;
}

function renderRunDetails(payload) {
  document.getElementById("scenario-title").textContent =
    `${payload.scenario_name} — seed ${payload.seed}`;
  document.getElementById("data-provenance").textContent =
    `Run ${payload.run_id} · schema ${payload.schema_version}`;
  document.getElementById("run-details").innerHTML = `
    <dt>Scenario</dt><dd>${payload.scenario_id}</dd>
    <dt>Status</dt><dd>${payload.status}</dd>
    <dt>Ticks</dt><dd>${payload.ticks_executed}</dd>
    <dt>Seed</dt><dd>${payload.seed}</dd>
    <dt>Traces</dt><dd>${payload.metrics.audit_trace_count}</dd>
    <dt>Destroyed</dt><dd>${(payload.metrics.destroyed_node_fraction * 100).toFixed(1)}%</dd>
    <dt>Focus areas</dt><dd>${(payload.analytics_overlay?.recommended_focus_areas || []).length}</dd>
  `;
}

function showSelection(kind, item) {
  const panel = document.getElementById("selection-detail");
  panel.classList.remove("hidden");
  const risk = item.risk_score != null ? ` · risk ${Math.round(item.risk_score)}/100` : "";
  const focus = item.is_focus_area ? " · focus area" : "";
  if (kind === "node") {
    panel.innerHTML = `<strong>${item.name}</strong> (${item.id}) · ${item.node_type} · ${item.status}
      · degree ${item.degree}${item.is_bottleneck ? " · bottleneck" : ""}
      · Red attacks: ${item.red_attacks}${risk}${focus}`;
  } else {
    panel.innerHTML = `<strong>${item.name}</strong> (${item.id}) · ${item.status}
      ${item.is_chokepoint ? "· chokepoint" : ""}${item.corridor ? ` · ${item.corridor}` : ""}
      · Red attacks: ${item.red_attacks}${risk}${focus}`;
  }
  highlightEntity(kind, item.id);
}

function populateRunSelects(runs) {
  const runSelect = document.getElementById("run-select");
  const compareSelect = document.getElementById("compare-select");
  runSelect.innerHTML = "";
  compareSelect.innerHTML = "";

  runs.forEach((run) => {
    const label = run.label || run.scenario_id;
    const text = `${label} · ${run.scenario_id} · seed ${run.seed ?? "?"}`;

    const option = document.createElement("option");
    option.value = run.run_id;
    option.textContent = text;
    runSelect.appendChild(option);

    const compareOption = option.cloneNode(true);
    compareSelect.appendChild(compareOption);
  });
}

async function loadComparison() {
  const enabled = document.getElementById("compare-enabled").checked;
  const compareSelect = document.getElementById("compare-select");
  compareSelect.disabled = !enabled;

  if (!enabled) {
    state.comparison = null;
    renderComparisonSummary();
    if (state.payload) renderMap(state.payload);
    return;
  }

  const baselineId = compareSelect.value;
  const compareId = document.getElementById("run-select").value;
  if (!baselineId || !compareId || baselineId === compareId) {
    state.comparison = null;
    renderComparisonSummary();
    return;
  }

  try {
    state.comparison = await fetchComparison(baselineId, compareId);
    renderComparisonSummary();
    if (state.payload) renderMap(state.payload);
  } catch (error) {
    state.comparison = null;
    document.getElementById("comparison-summary").innerHTML =
      `<div class="insight-empty">Comparison error: ${error.message}</div>`;
    document.getElementById("comparison-summary").classList.remove("hidden");
  }
}

async function loadSelectedRun() {
  const runId = document.getElementById("run-select").value;
  if (!runId) return;

  const [payload, insights, annotations] = await Promise.all([
    fetchViz(runId),
    fetchInsights(runId),
    fetchAnnotations(runId),
  ]);

  state.payload = payload;
  state.insights = insights;
  state.highlightedEntity = null;
  state.transform = { x: 0, y: 0, scale: 1 };

  renderRunDetails(payload);
  renderMetrics(payload);
  renderInsights(insights);
  renderAnnotations(annotations);
  renderMap(payload);
  await loadComparison();
}

function setupPanZoom() {
  const svg = document.getElementById("network-map");

  svg.addEventListener("wheel", (event) => {
    event.preventDefault();
    const delta = event.deltaY > 0 ? 0.9 : 1.1;
    state.transform.scale = Math.min(3, Math.max(0.4, state.transform.scale * delta));
    renderMap(state.payload);
  });

  svg.addEventListener("pointerdown", (event) => {
    if (event.target.dataset.kind) return;
    state.dragging = true;
    state.lastPointer = { x: event.clientX, y: event.clientY };
    svg.setPointerCapture(event.pointerId);
  });

  svg.addEventListener("pointermove", (event) => {
    if (!state.dragging || !state.lastPointer) return;
    state.transform.x += event.clientX - state.lastPointer.x;
    state.transform.y += event.clientY - state.lastPointer.y;
    state.lastPointer = { x: event.clientX, y: event.clientY };
    renderMap(state.payload);
  });

  svg.addEventListener("pointerup", () => {
    state.dragging = false;
    state.lastPointer = null;
  });
}

function bindFilters() {
  const filterIds = [
    "filter-contested",
    "filter-bottlenecks",
    "filter-hide-open",
    "filter-high-risk",
    "filter-focus-areas",
    "filter-red-activity",
    "filter-show-risk-scores",
  ];
  filterIds.forEach((id) => {
    document.getElementById(id).addEventListener("change", () => {
      if (state.payload) renderMap(state.payload);
    });
  });
}

function bindComparison() {
  document.getElementById("compare-enabled").addEventListener("change", loadComparison);
  document.getElementById("compare-select").addEventListener("change", loadComparison);
}

function bindPresentationMode() {
  document.getElementById("presentation-btn").addEventListener("click", () => {
    document.body.classList.toggle("presentation-mode");
  });
}

async function init() {
  setupPanZoom();
  bindFilters();
  bindComparison();
  bindPresentationMode();

  document.getElementById("reload-btn").addEventListener("click", loadSelectedRun);
  document.getElementById("run-select").addEventListener("change", loadSelectedRun);

  try {
    const data = await fetchRuns();
    state.runs = data.runs || [];
    if (!state.runs.length) {
      document.getElementById("scenario-title").textContent = "No exported runs found";
      return;
    }
    populateRunSelects(state.runs);
    if (state.runs.length > 1) {
      document.getElementById("compare-select").selectedIndex = 0;
    }
    await loadSelectedRun();
  } catch (error) {
    document.getElementById("scenario-title").textContent = `Error: ${error.message}`;
  }
}

init();