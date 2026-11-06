"use strict";

const results = document.querySelector("#results");
const error = document.querySelector("#error");

function imageURL(revision, path) {
  if (!/^[a-f0-9]{40}$/i.test(revision) || !path.startsWith("runs/")) return null;
  const parts = path.split("/");
  if (parts.some((part) => !part || part === "." || part === ".." || /[\\%\u0000-\u001f\u007f]/.test(part))) return null;
  return `https://raw.githubusercontent.com/Emyrk/throw-away-qa/${revision}/${parts.map(encodeURIComponent).join("/")}`;
}

function renderResult(result, revision) {
  const card = document.createElement("article");
  card.className = "result";
  const heading = document.createElement("h2");
  heading.textContent = result.variant_id;
  const status = document.createElement("span");
  status.className = `status status-${result.status}`;
  status.textContent = result.status;
  const title = document.createElement("div");
  title.className = "result-title";
  title.append(heading, status);
  card.append(title);

  const details = document.createElement("dl");
  for (const [label, key] of [["Tried", "tried"], ["Happened", "happened"], ["Wanted", "wanted"]]) {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = result[key];
    row.append(term, description);
    details.append(row);
  }
  card.append(details);

  if (result.timeline?.length) {
    const timeline = document.createElement("section");
    timeline.className = "timeline";
    const subtitle = document.createElement("h3");
    subtitle.textContent = `Step by step (${result.timeline_date} UTC)`;
    const table = document.createElement("table");
    const header = document.createElement("thead");
    const labels = document.createElement("tr");
    for (const label of ["UTC", "Action or event"]) {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = label;
      labels.append(cell);
    }
    header.append(labels);
    const body = document.createElement("tbody");
    for (const item of result.timeline) {
      const row = document.createElement("tr");
      for (const value of [item.utc, item.event]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      body.append(row);
    }
    table.append(header, body);
    timeline.append(subtitle, table);
    card.append(timeline);
  }

  const gallery = document.createElement("div");
  gallery.className = "screenshots";
  for (const path of result.images || []) {
    const url = imageURL(revision, path);
    if (!url) continue;
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    const image = document.createElement("img");
    image.src = url;
    image.alt = `Screenshot of ${result.variant_id} outcome`;
    image.loading = "lazy";
    link.append(image);
    gallery.append(link);
  }
  if (gallery.childElementCount) card.append(gallery);
  return card;
}

async function load() {
  try {
    const response = await fetch("./data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (!Array.isArray(data.results)) throw new Error("Invalid results");
    results.replaceChildren(...data.results.map((result) => renderResult(result, data.source_revision)));
  } catch {
    error.textContent = "Results could not be loaded.";
    error.hidden = false;
  }
}

load();
