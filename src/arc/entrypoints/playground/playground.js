const strategies = {
  bm25: ["BM25", "Keyword retrieval using term statistics."],
  dense: ["Dense", "BGE query embedding and exact FAISS vector search."],
  hybrid: ["Hybrid", "BM25 and Dense fused by reciprocal rank."],
  hybrid_rerank: ["Hybrid + Rerank", "MiniLM rescores up to 50 fused candidates."],
};
const examples = {
  demo: ["BM25", "vector index", "rank fusion"],
  playground: ["BM25", "dense vector search", "reciprocal rank fusion"],
  scifact: ["vitamin D and bone fractures", "exercise and cardiovascular disease", "antibiotic resistance"],
  wands: ["office chair", "outdoor dining table", "round wall mirror"],
};
const corpusLabels = { demo: "ARC demo", playground: "ARC field notes", scifact: "SciFact", wands: "WANDS" };
const stageLabels = {
  bm25: "BM25",
  query_encode: "Encode query",
  faiss_search: "FAISS",
  rrf: "Rank fusion",
  minilm: "MiniLM",
  assemble: "Assemble hits",
};
const form = document.querySelector("#search");
const query = document.querySelector("#query");
const primary = document.querySelector("#primary");
const compare = document.querySelector("#compare");
const limit = document.querySelector("#limit");
const submit = document.querySelector("#submit");
const results = document.querySelector("#results");
const status = document.querySelector("#status");
const exampleList = document.querySelector("#examples");
let config;

function node(tag, content, className) {
  const element = document.createElement(tag);
  if (content !== undefined) element.textContent = content;
  if (className) element.className = className;
  return element;
}

function message(text, isError = false) {
  status.textContent = text;
  status.classList.toggle("error", isError);
}

function timing(ms) {
  return ms > 0 && ms < 0.01 ? "<0.01 ms" : ms.toFixed(2) + " ms";
}

function updateCompare() {
  const selection = compare.value;
  const alternatives = Object.keys(config.snapshots).filter((id) => id !== primary.value);
  compare.replaceChildren(new Option(alternatives.length ? "None" : "Unavailable", ""));
  for (const id of alternatives) compare.add(new Option(strategies[id][0], id));
  if (alternatives.includes(selection)) compare.value = selection;
  compare.disabled = alternatives.length === 0;
}

function render(body) {
  const [title, description] = strategies[body.strategy_id];
  const panel = node("article", undefined, "panel result");
  const heading = node("header", undefined, "result-head");
  heading.append(
    node("h2", title),
    node("p", description, "muted"),
    node("p", body.hits.length + " hits · " + timing(body.elapsed_ms) + " in ARC"),
  );
  panel.append(heading);

  if (body.hits.length) {
    const hits = node("ol", undefined, "hits");
    for (const hit of body.hits) {
      const row = node("li", undefined, "hit");
      const label = node("div");
      label.append(
        node("p", hit.title || hit.entity_key.entity_id, "hit-title"),
        node("p", hit.source_ref, "hit-meta"),
      );
      const score = node("p", undefined, "score");
      score.append(node("b", Number(hit.score.toPrecision(4))), document.createTextNode(hit.score_type));
      row.append(node("span", hit.rank, "rank"), label, score);
      hits.append(row);
    }
    panel.append(hits);
  } else {
    panel.append(node("p", "ARC returned no hits for this query.", "empty muted"));
  }

  const trace = node("section", undefined, "trace");
  trace.append(node("h3", "Stage trace"));
  const table = node("table");
  const header = table.createTHead().insertRow();
  for (const label of ["Stage", "Count", "Elapsed"]) {
    const cell = node("th", label);
    cell.scope = "col";
    header.append(cell);
  }
  const rows = table.createTBody();
  for (const stage of body.trace) {
    const row = rows.insertRow();
    for (const value of [stageLabels[stage.name] || stage.name, stage.count, timing(stage.elapsed_ms)]) {
      row.insertCell().textContent = value;
    }
  }
  const identifiers = node("details");
  identifiers.append(
    node("summary", "Snapshot and trace IDs"),
    node("p", "Snapshot " + body.snapshot_id),
    node("p", "Trace " + body.trace_id),
  );
  trace.append(table, identifiers);
  panel.append(trace);
  return panel;
}

async function search(id, text) {
  const response = await fetch("../search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: text,
      domain: config.domain,
      top_k: Number(limit.value),
      strategy_id: id,
      snapshot_id: config.snapshots[id],
      trace_level: "summary",
    }),
  });
  if (response.status === 409) throw new Error("The snapshot changed. Reload to reconnect.");
  if (!response.ok) throw new Error("ARC search failed (HTTP " + response.status + ").");
  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (submit.disabled) return;
  const text = query.value.trim();
  if (!text) {
    message("Enter a query to run a search.", true);
    query.focus();
    return;
  }
  const selected = [primary.value, compare.value].filter(Boolean);
  const controls = [query, submit, primary, compare, limit, ...exampleList.children];
  for (const control of controls) control.disabled = true;
  results.replaceChildren();
  results.setAttribute("aria-busy", "true");
  message("Running " + (selected.length === 1 ? strategies[selected[0]][0] + "…" : "both strategies in sequence…"));
  try {
    const panels = [];
    for (const id of selected) panels.push(render(await search(id, text)));
    results.replaceChildren(...panels);
    message(selected.length === 1 ? "Live search complete" : "Live comparison complete");
  } catch (error) {
    message(error.message, true);
  } finally {
    results.setAttribute("aria-busy", "false");
    for (const control of controls) control.disabled = false;
    compare.disabled = Object.keys(config.snapshots).length < 2;
  }
});

primary.addEventListener("change", updateCompare);

async function connect() {
  try {
    const response = await fetch("config", { cache: "no-store" });
    if (!response.ok) throw new Error();
    config = await response.json();
    const available = Object.keys(config.snapshots);
    for (const id of available) primary.add(new Option(strategies[id][0], id));
    updateCompare();
    for (const text of examples[config.corpus] || []) {
      const button = node("button", text);
      button.type = "button";
      button.addEventListener("click", () => {
        query.value = text;
        form.requestSubmit();
      });
      exampleList.append(button);
    }
    const badge = document.querySelector("#capabilities");
    badge.textContent = (corpusLabels[config.corpus] || config.domain) + " · " + (available.length === 1
      ? strategies[available[0]][0] + " only"
      : available.length + " live strategies");
    badge.hidden = false;
    primary.disabled = false;
    submit.disabled = false;
    message("Ready for a live search");
  } catch {
    message("Could not connect to ARC. Check the server and reload this page.", true);
  }
}

connect();
