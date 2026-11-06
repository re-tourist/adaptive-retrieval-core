import assert from "node:assert/strict";
import { writeFile } from "node:fs/promises";

const debuggerUrl = process.argv[2] ?? "http://127.0.0.1:9226";
const page = await fetch(debuggerUrl + "/json/new?about:blank", { method: "PUT" });
if (!page.ok) throw new Error("Could not create a tab in the local browser.");
const target = await page.json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
const pending = new Map();
let id = 0;
socket.addEventListener("message", ({ data }) => {
  const response = JSON.parse(data);
  const callback = pending.get(response.id);
  if (!callback) return;
  pending.delete(response.id);
  if (response.error) callback.reject(new Error(response.error.message));
  else callback.resolve(response.result);
});

function call(method, params = {}) {
  const seq = ++id;
  return new Promise((resolve, reject) => {
    pending.set(seq, { resolve, reject });
    socket.send(JSON.stringify({ id: seq, method, params }));
  });
}

async function evaluate(expression) {
  const response = await call("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (response.exceptionDetails) throw new Error(response.result.description);
  return response.result.value;
}

async function open(relative, width, height) {
  const url = new URL(relative, import.meta.url).href;
  await call("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  const response = await call("Page.navigate", { url });
  if (response.errorText) throw new Error(response.errorText);
  await waitFor(`location.href === ${JSON.stringify(url)} && document.readyState === "complete"`);
}

async function waitFor(expression) {
  for (let i = 0; i < 100; i += 1) {
    if (await evaluate(expression)) return;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error("Browser condition did not complete: " + expression);
}

async function checkFit() {
  assert(await evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "Horizontal overflow");
  const [content, viewport] = await evaluate("[document.documentElement.scrollHeight, innerHeight]");
  assert(content <= viewport, `Viewport crops the document (${content} > ${viewport})`);
}

async function capture(file, width, height) {
  await checkFit();
  const response = await call("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const png = Buffer.from(response.data, "base64");
  assert.equal(png.readUInt32BE(16), width);
  assert.equal(png.readUInt32BE(20), height);
  await writeFile(new URL(file, import.meta.url), png);
  console.log(`${file} · ${width} × ${height}`);
}

try {
  await call("Page.enable");
  await call("Emulation.setScrollbarsHidden", { hidden: true });
  await open("index.html", 1440, 900);
  assert.equal(await evaluate("document.querySelectorAll('.product').length"), 4);
  assert.equal(await evaluate("document.querySelector('.product h3').textContent"), "Luma task lamp");
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.product-grid')).gridTemplateColumns.split(' ').length"), 4);
  assert(await evaluate(`(async () => {
    const image = new Image();
    image.src = "assets/lamp-sheet.png";
    await image.decode();
    return image.naturalWidth * 2 === image.naturalHeight * 3;
  })()`));
  await capture("search-home.png", 1440, 900);

  await open("index.html?view=compare", 1440, 900);
  assert.deepEqual(await evaluate("Array.from(document.querySelector('.rank-pair').children, el => el.dataset.product)"), ["luma", "cove"]);
  assert.equal(await evaluate("document.querySelector('.rank-pair .delta').textContent"), "↑ 2");
  assert.equal(await evaluate("document.querySelector('#diagnostics').open"), false);
  await capture("compare.png", 1440, 900);

  await open("readme-hero.html", 1280, 980);
  assert(await evaluate("document.querySelector('figure img').decode().then(() => true)"));
  await capture("readme-hero.png", 1280, 980);

  await open("index.html", 390, 980);
  assert.equal(await evaluate("getComputedStyle(document.querySelector('.product-grid')).gridTemplateColumns.split(' ').length"), 2);
  await capture("search-home-mobile.png", 390, 980);
  await open("index.html?view=compare", 390, 1150);
  assert(await evaluate("document.querySelector('.rank-pair').children[0].offsetLeft < document.querySelector('.rank-pair').children[1].offsetLeft"));
  assert(await evaluate(`Array.from(document.querySelectorAll('.rank-pair')).every(row => {
    const [left, right] = Array.from(row.querySelectorAll('.photo'), el => el.getBoundingClientRect().top);
    return Math.abs(left - right) < 1;
  })`));
  await capture("compare-mobile.png", 390, 1150);

  await evaluate("document.querySelector('.examples button:last-child').click()");
  assert.equal(await evaluate("document.querySelector('.rank-pair h3').textContent"), "Vale table lamp");
  assert.equal(await evaluate("document.querySelectorAll('.delta').length"), 3);
  assert(await evaluate("document.querySelector('#search-view').href.includes('amber%20glass%20lamp')"));
  await evaluate("document.querySelector('#diagnostics summary').click()");
  assert(await evaluate("document.querySelector('#diagnostics').open"));
  await evaluate("document.querySelector('#search-view').click()");
  await waitFor("document.querySelector('#search-view')?.getAttribute('aria-current') === 'page'");
  assert.equal(await evaluate("document.querySelector('#query').value"), "amber glass lamp");
  await evaluate("document.querySelector('#compare-view').click()");
  await waitFor("document.querySelector('#compare-view')?.getAttribute('aria-current') === 'page'");
  assert.equal(await evaluate("document.querySelector('#query').value"), "amber glass lamp");
  await evaluate("document.querySelector('#query').value = 'unlisted sample'; document.querySelector('#search-form').requestSubmit()");
  assert.equal(await evaluate("document.querySelector('#result-meta').textContent"), "No fixture for this query");
  assert(await evaluate("document.querySelector('#diagnostics').hidden"));
  await open("readme-hero.html", 390, 790);
  await checkFit();
  console.log("Layout, fixture changes, query preservation, empty state, and diagnostics checks passed.");
} finally {
  socket.close();
  await fetch(debuggerUrl + "/json/close/" + target.id);
}
