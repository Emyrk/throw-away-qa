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
    card.append(link);
  }
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
