const strategies = {
  bm25: ["Keyword (BM25)", "Matches query terms"],
  dense: ["Dense", "Matches meaning with embeddings"],
  hybrid: ["Hybrid", "Combines keyword and dense ranks"],
  hybrid_rerank: ["Hybrid + Rerank", "MiniLM reranks hybrid results"],
};
const profiles = {
  catalog: ["ARC Homewares", [
    ["Reading nook", "small brass reading lamp"],
    ["Blanket storage", "woven basket for extra blankets"],
    ["Soft textures", "soft green throw for a sofa"],
  ]],
  demo: ["ARC sample", [["BM25", "BM25"], ["Vector index", "vector index"], ["Rank fusion", "rank fusion"]]],
  playground: ["ARC field notes", [["BM25", "BM25"], ["Vector search", "dense vector search"], ["Rank fusion", "reciprocal rank fusion"]]],
  scifact: ["SciFact", [["Bone health", "vitamin D and bone fractures"], ["Exercise", "exercise and cardiovascular disease"]]],
  wands: ["WANDS", [["Office chair", "office chair"], ["Outdoor table", "outdoor dining table"], ["Wall mirror", "round wall mirror"]]],
};
const stages = {
  bm25: "Keyword", query_encode: "Encode query", faiss_search: "FAISS",
  rrf: "Rank fusion", minilm: "MiniLM", assemble: "Assemble results",
};
const get = (id) => document.getElementById(id);
const input = get("query");
const primary = get("primary");
const secondary = get("secondary");
const output = get("catalog");
const diagnostics = get("diagnostics");
const examples = get("examples");
const status = get("status");
const form = get("search-form");
const searchView = get("search-view");
const compareView = get("compare-view");
let config;
let available = [];
let comparing = false;
let busy = false;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function photo(hit) {
  const product = config.products?.[hit.entity_key.entity_id];
  if (!product) return null;
  const columns = product.sheet === "lighting" ? 2 : 3;
  const element = node("div", undefined, "photo sheet-" + product.sheet);
  element.style.backgroundSize = (100 * columns) + "% " + (100 * columns) + "%";
  const step = 100 / (columns - 1);
  element.style.backgroundPosition = (product.tile % columns * step) + "% " + (Math.floor(product.tile / columns) * step) + "%";
  element.setAttribute("aria-hidden", "true");
  return element;
}

function productCopy(hit) {
  const copy = node("div", undefined, "product-text");
  copy.append(node("h3", hit.title || hit.entity_key.entity_id));
  const attrs = config.products?.[hit.entity_key.entity_id]?.attributes;
  copy.append(node("p", attrs?.join(" · ") || hit.source_ref));
  return copy;
}

function card(hit, compact = false) {
  if (!hit) return node("div", "No hit at this rank", "ranked absent");
  const element = node(compact ? "div" : "li", undefined, compact ? "ranked" : "product");
  element.dataset.id = hit.entity_key.entity_id;
  element.dataset.rank = hit.rank;
  const picture = photo(hit);
  const rank = node("span", String(hit.rank).padStart(2, "0"), compact ? "row-rank" : "card-rank");
  rank.prepend(node("span", "Rank ", "sr-only"));
  if (compact) element.append(rank);
  if (picture) element.append(picture);
  element.classList.toggle("text-result", !picture);
  if (!compact) element.append(rank);
  element.append(productCopy(hit));
  return element;
}

function rankChange(hit, baseline, showChange) {
  if (!hit) return null;
  if (!baseline) return node("span", "Only here", "delta");
  if (!showChange) return null;
  const movement = baseline.rank - hit.rank;
  if (!movement) return null;
  const badge = node("span", (movement > 0 ? "↑ " : "↓ ") + Math.abs(movement), "delta");
  badge.setAttribute("aria-label", (movement > 0 ? "Up " : "Down ") + Math.abs(movement) + " from the left list");
  badge.classList.toggle("rise", movement > 0);
  return badge;
}

function compareResults(left, right) {
  const headers = node("div", undefined, "compare-labels");
  for (const response of [left, right]) {
    const [title, detail] = strategies[response.strategy_id];
    const heading = node("div");
    heading.append(node("h3", title), node("p", detail));
    headers.append(heading);
  }
  output.append(headers);
  const hitMap = (response) => new Map(response.hits.map((hit) => [hit.entity_key.entity_id, hit]));
  const baseline = hitMap(left);
  const alternative = hitMap(right);
  for (let i = 0; i < Math.max(left.hits.length, right.hits.length); i++) {
    const pair = node("div", undefined, "rank-pair");
    for (const [response, other] of [[left, alternative], [right, baseline]]) {
      const hit = response.hits[i];
      const tile = card(hit, true);
      tile.dataset.strategy = response.strategy_id;
      const badge = rankChange(hit, other.get(hit?.entity_key.entity_id), response === right);
      if (badge) tile.append(badge);
      pair.append(tile);
    }
    output.append(pair);
  }
  output.append(node("p", "Arrows show movement from the left list. “Only here” means absent from the other returned list.", "compare-key"));
}

function timing(ms) {
  return ms > 0 && ms < 0.01 ? "<0.01 ms" : ms.toFixed(2) + " ms";
}

function showDiagnostics(responses) {
  const trace = get("trace");
  for (const body of responses) {
    const section = node("section", undefined, "trace-block");
    section.append(
      node("h3", strategies[body.strategy_id][0]),
      node("p", "Total in ARC: " + timing(body.elapsed_ms)),
    );
    const list = node("ul");
    for (const step of body.trace) {
      list.append(node("li", (stages[step.name] ?? step.name) + " · " + step.count + " items · " + timing(step.elapsed_ms)));
    }
    section.append(list, node("p", "Snapshot " + body.snapshot_id), node("p", "Trace " + body.trace_id));
    if (body.hits.length) section.append(node("p", "Score type: " + body.hits[0].score_type));
    trace.append(section);
  }
  if (responses.length > 1) trace.append(node("p", "Scores use strategy-specific scales."));
  diagnostics.hidden = false;
}

function message(text, error = false) {
  status.textContent = text;
  status.classList.toggle("error", error);
}

async function request(id, query, topK) {
  let response;
  try {
    response = await fetch("../search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query, domain: config.domain, top_k: topK, strategy_id: id,
        snapshot_id: config.snapshots[id], trace_level: "summary",
      }),
    });
  } catch {
    throw new Error("Could not reach ARC. Check the server and try again.");
  }
  if (response.status === 409) throw new Error("The search snapshot changed. Reload to reconnect.");
  if (!response.ok) throw new Error("ARC could not run this search (HTTP " + response.status + "). Try again.");
  return response.json();
}

function syncControls() {
  input.disabled = get("submit").disabled = searchView.disabled = busy;
  compareView.disabled = busy || available.length < 2;
  primary.disabled = secondary.disabled = busy;
  for (const button of examples.querySelectorAll("button")) button.disabled = busy;
}

function setAlternatives() {
  const previous = secondary.value;
  const alternatives = available.filter((id) => id !== primary.value);
  secondary.replaceChildren(...alternatives.map((id) => new Option(strategies[id][0], id)));
  if (alternatives.includes(previous)) secondary.value = previous;
  else if (alternatives.includes("hybrid")) secondary.value = "hybrid";
}

async function search() {
  if (busy || !available.length) return;
  const query = input.value.trim();
  output.replaceChildren();
  get("trace").replaceChildren();
  diagnostics.open = false;
  diagnostics.hidden = true;
  if (!query) {
    message("Enter a query to search.", true);
    input.focus();
    return;
  }
  const focus = document.activeElement;
  const topK = config.corpus === "catalog" ? 4 : 5;
  for (const button of examples.querySelectorAll("button")) {
    button.setAttribute("aria-pressed", String(button.dataset.query === query));
  }
  busy = true;
  syncControls();
  output.setAttribute("aria-busy", "true");
  message("Searching…");
  try {
    const left = await request(primary.value, query, topK);
    const responses = [left];
    if (comparing) {
      const right = await request(secondary.value, query, topK);
      responses.push(right);
      message(left.hits.length + " vs. " + right.hits.length + " results · Same query");
      if (left.hits.length || right.hits.length) compareResults(left, right);
    } else {
      const count = left.hits.length;
      message(count + (count === 1 ? " result" : " results") + " · " + strategies[left.strategy_id][0]);
      if (count) {
        const grid = node("ol", undefined, "product-grid");
        grid.append(...left.hits.map((hit) => card(hit)));
        output.append(grid);
      }
    }
    if (!output.children.length) {
      output.append(node("p", "No results for this query. Try a different phrase or one of the examples.", "empty"));
    }
    showDiagnostics(responses);
  } catch (error) {
    message(error.message, true);
  } finally {
    busy = false;
    output.setAttribute("aria-busy", "false");
    syncControls();
    if (document.activeElement === document.body && focus instanceof HTMLElement) focus.focus();
  }
}

function switchView(next) {
  if (busy || comparing === next || (next && available.length < 2)) return;
  comparing = next;
  document.body.classList.toggle("is-compare", comparing);
  searchView.setAttribute("aria-pressed", String(!comparing));
  compareView.setAttribute("aria-pressed", String(comparing));
  get("second-control").hidden = !comparing;
  get("page-title").textContent = comparing ? "Compare strategies." : "Find the right match.";
  get("results-title").textContent = comparing ? "Rank comparison" : "Search results";
  get("lead").textContent = comparing ? "One query, two ways to rank the same corpus." : leadText();
  search();
}

function leadText() {
  return config.corpus === "catalog"
    ? "Search a homewares catalog in your own words."
    : "Search the active ARC corpus in your own words.";
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});
searchView.addEventListener("click", () => switchView(false));
compareView.addEventListener("click", () => switchView(true));
primary.addEventListener("change", () => {
  setAlternatives();
  search();
});
secondary.addEventListener("change", search);

async function connect() {
  try {
    const response = await fetch("config", { cache: "no-store" });
    if (!response.ok) throw new Error();
    config = await response.json();
    available = Object.keys(strategies).filter((id) => Object.hasOwn(config.snapshots, id));
    if (!available.length) throw new Error();
    primary.replaceChildren(...available.map((id) => new Option(strategies[id][0], id)));
    setAlternatives();
    const [label, queries] = profiles[config.corpus] ?? [config.domain, []];
    get("corpus").textContent = label;
    get("corpus").hidden = false;
    get("lead").textContent = leadText();
    get("vertical").textContent = config.domain === "product" ? "PRODUCT SEARCH" : "SEARCH PLAYGROUND";
    get("strategies").hidden = available.length < 2;
    get("availability").hidden = available.length > 1;
    if (config.corpus === "catalog") {
      get("availability").textContent = "Compare needs a second strategy. Set ARC_BGE_MODEL to enable Dense and Hybrid.";
    }
    get("provenance").textContent = config.corpus === "catalog"
      ? Object.keys(config.products).length + " fictional products · Generated photography · Live ARC search"
      : "Live ARC search · " + label;
    for (const [title, query] of queries) {
      const button = node("button", title);
      button.type = "button";
      button.dataset.query = query;
      button.addEventListener("click", () => {
        input.value = query;
        search();
      });
      examples.append(button);
    }
    examples.hidden = !queries.length;
    syncControls();
    if (queries.length) {
      input.value = queries[0][1];
      await search();
    } else message("Ready for a live search");
  } catch {
    message("Could not connect to ARC. Check the server and reload.", true);
  }
}

connect();
