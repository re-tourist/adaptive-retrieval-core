const products = {
  luma: { name: "Luma task lamp", material: "Aged brass", detail: "Adjustable arm" },
  studio: { name: "Studio desk lamp", material: "Matte charcoal", detail: "Tilting shade" },
  cove: { name: "Cove reading lamp", material: "Brushed brass", detail: "Linen shade" },
  vale: { name: "Vale table lamp", material: "Amber glass", detail: "Walnut base" },
};
const fixtures = {
  "small brass lamp for a reading nook": { keyword: ["luma", "studio", "cove", "vale"], hybrid: ["cove", "luma", "vale", "studio"] },
  "adjustable desk lamp": { keyword: ["studio", "luma", "cove"], hybrid: ["luma", "studio", "cove"] },
  "amber glass lamp": { keyword: ["vale", "luma", "studio"], hybrid: ["vale", "cove", "luma"] },
};
const params = new URLSearchParams(location.search);
const compare = params.get("view") === "compare";
const input = document.querySelector("#query");
const catalog = document.querySelector("#catalog");
const meta = document.querySelector("#result-meta");
const diagnostics = document.querySelector("#diagnostics");

function tile(id) {
  return `<span class="photo photo-${id}" aria-hidden="true"></span>`;
}

function card(id, rank) {
  const { name, material, detail } = products[id];
  return `<li class="product">
    ${tile(id)}
    <span class="card-rank" aria-label="Rank ${rank}">${String(rank).padStart(2, "0")}</span>
    <div class="product-text"><h3>${name}</h3><p>${material} · ${detail}</p></div>
  </li>`;
}

function compareCard(id, rank, delta = "") {
  if (!id) return '<div class="ranked absent">No item at this rank</div>';
  const { name, material, detail } = products[id];
  return `<div class="ranked" data-product="${id}">
    <span class="row-rank" aria-label="Rank ${rank}">${String(rank).padStart(2, "0")}</span>
    ${tile(id)}
    <div class="ranked-copy"><h3>${name}</h3><p>${material} · ${detail}</p></div>
    ${delta}
  </div>`;
}

function rankChange(baseline, current) {
  if (baseline < 0) return '<span class="delta">New</span>';
  const difference = baseline - current;
  if (!difference) return '<span class="delta stable">Same</span>';
  const direction = difference > 0 ? "Up" : "Down";
  return `<span class="delta ${difference > 0 ? "rise" : ""}" aria-label="${direction} ${Math.abs(difference)} places">${difference > 0 ? "↑" : "↓"} ${Math.abs(difference)}</span>`;
}

function compareList({ keyword, hybrid }) {
  const depth = Math.max(keyword.length, hybrid.length);
  const rows = Array.from({ length: depth }, (_, i) => {
    const right = hybrid[i];
    return `<div class="rank-pair">
      ${compareCard(keyword[i], i + 1)}
      ${compareCard(right, i + 1, right && rankChange(keyword.indexOf(right), i))}
    </div>`;
  });
  return `<div class="compare-labels">
    <div><h3>Keyword <span>BM25</span></h3><p>Matches query terms</p></div>
    <div><h3>Hybrid <span>BM25 + Dense</span></h3><p>Combines term and meaning matches</p></div>
  </div>${rows.join("")}`;
}

function render(query) {
  input.value = query;
  const normalized = query.trim().toLowerCase();
  const result = Object.hasOwn(fixtures, normalized) ? fixtures[normalized] : null;
  const linkQuery = "?q=" + encodeURIComponent(query);
  document.querySelector("#search-view").href = linkQuery;
  document.querySelector("#compare-view").href = linkQuery + "&view=compare";
  diagnostics.hidden = !compare || !result;
  diagnostics.open = false;
  for (const example of document.querySelectorAll(".examples button")) {
    example.setAttribute("aria-pressed", String(example.dataset.query === normalized));
  }
  if (!result) {
    meta.textContent = "No fixture for this query";
    catalog.innerHTML = '<p class="empty">Choose an example above to see its sample rankings.</p>';
    return;
  }
  if (compare) {
    meta.textContent = "Model-enabled preview · Rank movement is relative to Keyword";
    catalog.innerHTML = compareList(result);
  } else {
    meta.textContent = `${result.keyword.length} sample hits · Keyword (BM25)`;
    catalog.innerHTML = `<ol class="product-grid">${result.keyword.map((id, i) => card(id, i + 1)).join("")}</ol>`;
  }
}

function search(query) {
  params.set("q", query);
  history.replaceState(null, "", "?" + params);
  render(query);
}

document.body.classList.toggle("is-compare", compare);
if (compare) {
  document.querySelector("#page-title").textContent = "Compare strategies.";
  document.querySelector(".lead").textContent = "One query, two ways to rank. Hybrid requires a model and index.";
  document.querySelector("#results-title").textContent = "Rank comparison";
} else {
  document.querySelector("#compare-view").title = "Open the model-enabled comparison preview";
}
document.querySelector(compare ? "#compare-view" : "#search-view").setAttribute("aria-current", "page");
document.querySelector("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  search(input.value.trim());
});
for (const example of document.querySelectorAll(".examples button")) {
  example.addEventListener("click", () => search(example.dataset.query));
}
render(params.get("q") ?? Object.keys(fixtures)[0]);
