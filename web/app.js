"use strict";

const STATUSES = {
  pass: "Pass",
  fail: "Fail",
  blocked: "Blocked",
  "not-in-build": "Not in build",
  partial: "Partial / unrun",
};
const STATUS_ORDER = ["fail", "blocked", "not-in-build", "pass"];
const REPOSITORY_BLOB = "https://github.com/Emyrk/throw-away-qa/blob/";
const TIMER_PREFIX = "test-atlas:timer:v1:";
const state = { cases: [], runs: [], selectedCase: null, run: "", provider: "", pr: "", search: "", sourceRevision: "" };
let timerViews = [];

const list = document.querySelector("#case-list");
const detail = document.querySelector("#detail");
const summary = document.querySelector("#summary");
const announcement = document.querySelector("#announcement");

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = String(text);
  return element;
}

function valueText(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "string") return value;
  if (typeof value === "object") {
    try { return JSON.stringify(value, null, 2); } catch { return String(value); }
  }
  return String(value);
}

function values(value) {
  return (Array.isArray(value) ? value : value == null ? [] : [value])
    .filter((item) => item !== null && item !== undefined && item !== "")
    .map(String);
}

function listText(value) {
  return Array.isArray(value) ? value.map((item) => `• ${valueText(item)}`).join("\n") || "-" : valueText(value);
}

function formatDate(value) {
  const date = new Date(value);
  return !value || Number.isNaN(date.getTime()) ? valueText(value) : date.toISOString().replace("T", " ").replace(/\.\d{3}Z$/, " UTC").replace(/Z$/, " UTC");
}

function addField(container, label, value, code = false) {
  const row = node("div", "field");
  row.append(node("dt", "field-label", label), node("dd", code ? "field-value code-value" : "field-value", valueText(value)));
  container.append(row);
}

function badge(status, label) {
  return node("span", `badge badge-${status || "unrecorded"}`, label || STATUSES[status] || "Unrun");
}

function chosenRuns() {
  return state.run === "" ? state.runs : [state.runs[Number(state.run)]].filter(Boolean);
}

function runResults(testCase, run) {
  return (Array.isArray(run.results) ? run.results : [])
    .filter((result) => result && String(result.case_id) === String(testCase.id));
}

function resultsFor(testCase) {
  return chosenRuns().flatMap((run) => runResults(testCase, run)
    .map((result) => ({ result, path: run.path })));
}

function variantStatus(results, variant) {
  for (const status of STATUS_ORDER) {
    if (results.some((result) => String(result.variant_id) === String(variant.id) && result.status === status)) return status;
  }
  return null;
}

function runCoverage(testCase, run) {
  const variants = Array.isArray(testCase.variants) ? testCase.variants : [];
  const results = runResults(testCase, run);
  const statuses = variants.map((variant) => variantStatus(results, variant));
  const covered = statuses.filter(Boolean).length;
  let status = null;
  if (statuses.includes("fail")) status = "fail";
  else if (covered && covered < variants.length) status = "partial";
  else if (statuses.includes("blocked")) status = "blocked";
  else if (statuses.includes("not-in-build")) status = "not-in-build";
  else if (variants.length && statuses.every((item) => item === "pass")) status = "pass";
  return { status, covered, total: variants.length };
}

function caseBadge(testCase) {
  if (state.run !== "") return badge(runCoverage(testCase, chosenRuns()[0]).status);
  const count = state.runs.filter((run) => runResults(testCase, run).length).length;
  return count ? badge("history", `History · ${count} ${count === 1 ? "run" : "runs"}`) : badge(null);
}

function populateOptions(select, options, label) {
  for (const option of options) {
    const entry = node("option", "", option);
    entry.value = option;
    select.append(entry);
  }
  select.firstElementChild.textContent = label;
}

function initFilters() {
  const providers = new Set(state.cases.flatMap((testCase) => values(testCase.providers)));
  const prs = new Set(state.cases.flatMap((testCase) => values(testCase.prs)));
  populateOptions(document.querySelector("#provider"), [...providers].sort(), "All providers");
  populateOptions(document.querySelector("#pr"), [...prs].sort((a, b) => a.localeCompare(b, undefined, { numeric: true })), "All PRs");
  const runSelect = document.querySelector("#run");
  state.runs.forEach((run, index) => {
    const entry = node("option", "", valueText(run.path));
    entry.value = String(index);
    runSelect.append(entry);
  });
}

function filteredCases() {
  return state.cases.filter((testCase) => {
    if (state.provider && !values(testCase.providers).includes(state.provider)) return false;
    if (state.pr && !values(testCase.prs).includes(state.pr)) return false;
    const searchable = [testCase.id, testCase.title, testCase.summary, testCase.notes, ...values(testCase.providers), ...values(testCase.prs)]
      .map(valueText).join(" ").toLocaleLowerCase();
    return searchable.includes(state.search);
  });
}

function renderSummary() {
  const scope = document.querySelector("#result-scope");
  const run = chosenRuns()[0];
  scope.textContent = state.run === ""
    ? "Historical overview · results from different runs are not combined into a case verdict. Select a run to see its coverage."
    : `Selected run: ${valueText(run?.path)} · a case passes only when every variant passes in this run. Check the manifest for the tested revision.`;
  const counts = state.run === ""
    ? { history: 0, unrecorded: 0 }
    : { pass: 0, fail: 0, partial: 0, blocked: 0, "not-in-build": 0, unrecorded: 0 };
  for (const testCase of state.cases) {
    const status = state.run === ""
      ? state.runs.some((item) => runResults(testCase, item).length) ? "history" : "unrecorded"
      : runCoverage(testCase, run).status || "unrecorded";
    counts[status]++;
  }
  summary.replaceChildren();
  for (const [status, count] of Object.entries(counts)) {
    const tile = node("div", `summary-tile summary-${status}`);
    tile.append(node("span", "summary-label", STATUSES[status] || { history: "Cases with history", partial: "Partial / unrun", unrecorded: "Unrun" }[status]), node("strong", "summary-number", count));
    summary.append(tile);
  }
}

function renderList() {
  const cases = filteredCases();
  document.querySelector("#case-count").textContent = `${cases.length} / ${state.cases.length}`;
  list.replaceChildren();
  if (!cases.length) {
    list.append(node("p", "placeholder", "No cases match these filters."));
    return;
  }
  for (const testCase of cases) {
    const button = node("button", "case-item");
    button.type = "button";
    button.setAttribute("aria-pressed", String(state.selectedCase === testCase));
    const upper = node("span", "case-item-top");
    upper.append(node("span", "case-id", valueText(testCase.id)), caseBadge(testCase));
    button.append(upper, node("span", "case-title", valueText(testCase.title)));
    if (testCase.summary) button.append(node("span", "case-summary", testCase.summary));
    const meta = node("span", "case-meta", `${values(testCase.providers).join(" · ") || "No provider"}  /  ${values(testCase.prs).map((pr) => `PR ${pr}`).join(", ") || "No PR"}`);
    button.append(meta);
    button.addEventListener("click", () => { state.selectedCase = testCase; renderList(); renderDetail(); });
    list.append(button);
  }
}

function sectionHeading(title, kicker) {
  const heading = node("div", "section-heading");
  heading.append(node("p", "eyebrow", kicker), node("h3", "", title));
  return heading;
}

function renderPills(container, items, prefix) {
  for (const item of values(items)) container.append(node("span", "pill", `${prefix}${item}`));
}

function renderOverview(testCase) {
  const header = node("header", "detail-header");
  const top = node("div", "detail-top");
  top.append(node("span", "eyebrow", `CASE ${valueText(testCase.id)}`), caseBadge(testCase));
  header.append(top, node("h2", "", valueText(testCase.title)));
  if (testCase.summary) header.append(node("p", "case-description", testCase.summary));
  const pills = node("div", "pills");
  renderPills(pills, testCase.providers, "");
  renderPills(pills, testCase.prs, "PR ");
  if (testCase.priority !== undefined) pills.append(node("span", "pill", `Priority ${valueText(testCase.priority)}`));
  if (testCase.estimated_minutes !== undefined) pills.append(node("span", "pill", `${valueText(testCase.estimated_minutes)} min estimated`));
  header.append(pills);
  if (state.run !== "") {
    const coverage = runCoverage(testCase, chosenRuns()[0]);
    header.append(node("p", "coverage-note", `${coverage.covered} / ${coverage.total} variants recorded in this run.`));
  } else {
    header.append(node("p", "coverage-note", "Historical results only. Select a run for a case verdict."));
  }
  return header;
}

function renderContext(testCase) {
  const section = node("section", "detail-section");
  section.append(sectionHeading("Before you begin", "01 / CONTEXT"));
  const fields = node("dl", "fields");
  addField(fields, "Prerequisites", listText(testCase.prerequisites));
  addField(fields, "Baseline configuration", testCase.config?.baseline, true);
  addField(fields, "Configuration overrides", testCase.config?.overrides, true);
  if (testCase.notes !== undefined) addField(fields, "Notes", listText(testCase.notes));
  section.append(fields);
  return section;
}

function timerKey(testCase, variant, stepIndex) {
  return TIMER_PREFIX + JSON.stringify([testCase.id, variant.id, stepIndex]);
}

function readStart(key) {
  try {
    const start = localStorage.getItem(key);
    const parsed = Date.parse(start);
    return start && Number.isFinite(parsed) && parsed <= Date.now() ? parsed : null;
  } catch { return null; }
}

function duration(seconds) {
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor(total % 3600 / 60);
  const remainder = total % 60;
  return hours ? `${hours}h ${String(minutes).padStart(2, "0")}m ${String(remainder).padStart(2, "0")}s` : `${minutes}m ${String(remainder).padStart(2, "0")}s`;
}

function renderTimer(container, testCase, variant, step, index) {
  const key = timerKey(testCase, variant, index);
  const timer = node("div", "timer");
  const readout = node("span", "timer-readout");
  readout.setAttribute("role", "timer");
  const started = node("span", "timer-started");
  const start = node("button", "button button-primary", "Start timer");
  const reset = node("button", "button button-quiet", "Reset");
  start.type = reset.type = "button";
  start.setAttribute("aria-label", `Start timer for ${valueText(variant.title)} step ${index + 1}`);
  reset.setAttribute("aria-label", `Reset timer for ${valueText(variant.title)} step ${index + 1}`);
  const update = () => {
    const startMs = readStart(key);
    start.disabled = startMs !== null;
    reset.disabled = startMs === null;
    if (startMs === null) {
      readout.textContent = "Not started";
      started.textContent = "";
      return;
    }
    const elapsed = Math.max(0, Math.floor((Date.now() - startMs) / 1000));
    const wait = Number(step.wait_seconds);
    readout.textContent = Number.isFinite(wait) && wait > 0
      ? elapsed >= wait ? `${duration(elapsed)} elapsed · wait complete` : `${duration(elapsed)} elapsed · ${duration(wait - elapsed)} to wait`
      : `${duration(elapsed)} elapsed`;
    started.textContent = `Started ${new Date(startMs).toISOString()} (UTC)`;
  };
  start.addEventListener("click", () => {
    try { localStorage.setItem(key, new Date().toISOString()); update(); }
    catch { announcement.textContent = "Browser storage is unavailable. This timer could not be started."; }
  });
  reset.addEventListener("click", () => {
    try { localStorage.removeItem(key); update(); }
    catch { announcement.textContent = "Browser storage is unavailable. This timer could not be reset."; }
  });
  timer.append(readout, started, start, reset);
  container.append(timer);
  timerViews.push({ element: timer, update });
  update();
}

function agentInstructions(testCase, variant) {
  const lines = [
    `Case ${valueText(testCase.id)}: ${valueText(testCase.title)}`,
    `Summary: ${valueText(testCase.summary)}`,
    `Variant ${valueText(variant.id)}: ${valueText(variant.title)}`,
    `Variant summary: ${valueText(variant.summary)}`,
    `Providers: ${values(testCase.providers).join(", ") || "-"}`,
    `Prerequisites:\n${listText(testCase.prerequisites)}`,
    `Baseline configuration: ${valueText(testCase.config?.baseline)}`,
    `Configuration overrides: ${valueText(testCase.config?.overrides)}`,
    "Steps:",
  ];
  for (const [index, step] of (Array.isArray(variant.steps) ? variant.steps : []).entries()) {
    lines.push(`${index + 1}. ${valueText(step.action)}`);
    for (const [key, label] of [["wait_seconds", "Wait (seconds)"], ["poll_seconds", "Poll every (seconds)"], ["timeout_seconds", "Timeout (seconds)"], ["expected", "Expected"], ["evidence", "Evidence"]]) {
      if (step[key] !== undefined) lines.push(`   ${label}: ${valueText(step[key])}`);
    }
  }
  lines.push(`Cleanup:\n${listText(variant.cleanup)}`);
  if (testCase.notes !== undefined) lines.push(`Notes:\n${listText(testCase.notes)}`);
  return lines.join("\n");
}

function renderStep(testCase, variant, step, index) {
  const item = node("li", "step");
  const title = node("div", "step-heading");
  title.append(node("span", "step-number", String(index + 1)), node("span", "step-action", valueText(step.action)));
  item.append(title);
  const fields = node("dl", "step-fields");
  for (const [key, label] of [["wait_seconds", "Wait"], ["poll_seconds", "Poll every"], ["timeout_seconds", "Timeout"]]) {
    if (step[key] !== undefined && step[key] !== null) addField(fields, label, `${valueText(step[key])}s`);
  }
  if (step.expected !== undefined) addField(fields, "Expected", step.expected);
  if (step.evidence !== undefined) addField(fields, "Evidence to capture", step.evidence);
  if (fields.childElementCount) item.append(fields);
  renderTimer(item, testCase, variant, step, index);
  return item;
}

function renderVariants(testCase) {
  const section = node("section", "detail-section");
  section.append(sectionHeading("Run the procedure", "02 / VARIANTS"));
  const variants = Array.isArray(testCase.variants) ? testCase.variants : [];
  if (!variants.length) section.append(node("p", "muted", "No variants recorded."));
  for (const variant of variants) {
    const card = node("section", "variant");
    const heading = node("div", "variant-heading");
    const name = node("div");
    name.append(node("p", "eyebrow", `VARIANT ${valueText(variant.id)}`), node("h4", "", valueText(variant.title)));
    if (variant.summary) name.append(node("p", "variant-summary", variant.summary));
    if (state.run !== "") name.append(badge(variantStatus(runResults(testCase, chosenRuns()[0]), variant)));
    else {
      const count = state.runs.filter((run) => variantStatus(runResults(testCase, run), variant)).length;
      name.append(count ? badge("history", `History · ${count} ${count === 1 ? "run" : "runs"}`) : badge(null));
    }
    const copy = node("button", "button button-outline", "Copy agent instructions");
    copy.type = "button";
    copy.setAttribute("aria-label", `Copy agent instructions for ${valueText(variant.title)}`);
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(agentInstructions(testCase, variant));
        announcement.textContent = `Instructions copied for ${valueText(variant.title)}.`;
      } catch { announcement.textContent = "Could not copy instructions. Check clipboard permission or use a secure origin."; }
    });
    heading.append(name, copy);
    card.append(heading);
    const steps = node("ol", "steps");
    for (const [index, step] of (Array.isArray(variant.steps) ? variant.steps : []).entries()) {
      steps.append(renderStep(testCase, variant, step, index));
    }
    card.append(steps);
    if (variant.cleanup !== undefined) {
      const cleanup = node("div", "cleanup");
      cleanup.append(node("strong", "", "Cleanup"), node("p", "", listText(variant.cleanup)));
      card.append(cleanup);
    }
    section.append(card);
  }
  return section;
}

function evidenceURL(runPath, relativePath) {
  if (!/^[a-f0-9]{40}$/i.test(state.sourceRevision) || typeof runPath !== "string" || typeof relativePath !== "string") return null;
  const runParts = runPath.split("/");
  const evidenceParts = relativePath.split("/");
  const safe = (part) => part && part !== "." && part !== ".." && !/[\\%\u0000-\u001f\u007f]/.test(part);
  if (runParts[0] !== "runs" || !runParts.every(safe) || !evidenceParts.every(safe)) return null;
  try {
    return `${REPOSITORY_BLOB}${state.sourceRevision}/${[...runParts, ...evidenceParts].map(encodeURIComponent).join("/")}`;
  } catch { return null; }
}

function renderEvidence(container, evidence, runPath) {
  if (!Array.isArray(evidence)) { addField(container, "Evidence", evidence); return; }
  const field = node("div", "field");
  const content = node("dd", "field-value evidence-links");
  if (!evidence.length) content.textContent = "-";
  for (const path of evidence) {
    const url = evidenceURL(runPath, path);
    if (!url) { content.append(node("span", "", valueText(path))); continue; }
    const link = node("a", "", path);
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.setAttribute("aria-label", `Open evidence ${path} on GitHub (new tab)`);
    content.append(link);
  }
  field.append(node("dt", "field-label", "Evidence"), content);
  container.append(field);
}

function renderRunCoverage(section, testCase) {
  if (state.run !== "") return;
  const group = node("div", "run-coverage");
  group.append(node("h4", "", "Coverage by run"));
  const runs = state.runs.filter((run) => runResults(testCase, run).length);
  if (!runs.length) group.append(node("p", "muted", "No runs recorded for this case."));
  for (const run of runs) {
    const coverage = runCoverage(testCase, run);
    const row = node("div", "run-coverage-row");
    row.append(node("span", "", valueText(run.path)), node("span", "coverage-count", `${coverage.covered} / ${coverage.total} variants`), badge(coverage.status));
    group.append(row);
  }
  section.append(group);
}

function renderResults(testCase) {
  const section = node("section", "detail-section");
  section.append(sectionHeading("Recorded evidence", "03 / RESULTS"));
  renderRunCoverage(section, testCase);
  const matches = resultsFor(testCase);
  if (matches.some(({ result }) => Array.isArray(result.evidence) && result.evidence.length) && !/^[a-f0-9]{40}$/i.test(state.sourceRevision)) {
    section.append(node("p", "muted", "Evidence paths are not linked until the snapshot has a committed source revision."));
  }
  if (!matches.length) section.append(node("p", "muted", "No results recorded for this case in the selected result set."));
  for (const { result, path } of matches) {
    const card = node("div", "result-card");
    const head = node("div", "result-heading");
    head.append(node("strong", "", valueText(path)), badge(STATUS_ORDER.includes(result.status) ? result.status : null));
    card.append(head);
    const fields = node("dl", "fields result-fields");
    for (const [key, value] of Object.entries(result)) {
      if (key === "case_id" || key === "status" || value === undefined) continue;
      if (key === "evidence") { renderEvidence(fields, value, path); continue; }
      const label = key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
      addField(fields, label, /(?:^|_)(?:at|timestamp|time)$/.test(key) && typeof value === "string" ? formatDate(value) : value, typeof value === "object");
    }
    card.append(fields);
    section.append(card);
  }
  if (state.run !== "") {
    const manifest = chosenRuns()[0]?.manifest;
    if (manifest !== null && manifest !== undefined) {
      const disclosure = node("details", "manifest");
      disclosure.append(node("summary", "", "Run manifest"), node("pre", "", valueText(manifest)));
      section.append(disclosure);
    }
  }
  return section;
}

function renderDetail() {
  timerViews = [];
  detail.replaceChildren();
  if (!state.selectedCase) {
    const empty = node("div", "detail-empty");
    empty.append(node("h2", "", "No case selected"), node("p", "", "Choose a case from the list to view its procedure and results."));
    detail.append(empty);
    return;
  }
  const testCase = state.selectedCase;
  detail.append(renderOverview(testCase), renderContext(testCase), renderVariants(testCase), renderResults(testCase));
}

function render() { renderSummary(); renderList(); renderDetail(); }

for (const [id, key] of [["#provider", "provider"], ["#pr", "pr"], ["#run", "run"]]) {
  document.querySelector(id).addEventListener("change", (event) => { state[key] = event.target.value; render(); });
}
document.querySelector("#search").addEventListener("input", (event) => {
  state.search = event.target.value.trim().toLocaleLowerCase();
  renderList();
});
setInterval(() => {
  timerViews = timerViews.filter(({ element }) => element.isConnected);
  for (const { update } of timerViews) update();
}, 1000);

async function load() {
  try {
    const response = await fetch("./data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!data || !Array.isArray(data.cases) || !Array.isArray(data.runs)) throw new Error("Invalid data format");
    state.cases = data.cases.filter((item) => item && typeof item === "object");
    state.runs = data.runs.filter((item) => item && typeof item === "object");
    state.sourceRevision = data.source_revision;
    document.querySelector("#source-revision").textContent = valueText(data.source_revision);
    const generated = document.querySelector("#generated-at");
    generated.textContent = formatDate(data.generated_at);
    document.querySelector("#run-count").textContent = String(state.runs.length);
    initFilters();
    state.selectedCase = state.cases[0] || null;
    render();
  } catch (error) {
    const message = document.querySelector("#load-error");
    message.hidden = false;
    message.textContent = `Could not load web/data.json (${error.message}). Serve this directory over HTTP after generating the snapshot; opening index.html directly may block local fetches.`;
    list.replaceChildren(node("p", "placeholder", "No test data available."));
    summary.replaceChildren();
  }
}
load();
