// 胸腔衛教單張庫：全站共用程式。資料只從 data/catalog.json 與 leaflets/<id>.json 讀取。
const REPO_URL = "https://github.com/juliachou0530/NTU_Cool_GenAI_ChestHealth";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function getJSON(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error(`讀取 ${path} 失敗（HTTP ${res.status}）`);
  return res.json();
}

// 字級放大（1.25×）：只存在這個瀏覽器
function setupFontToggle() {
  const btn = document.getElementById("fontBtn");
  if (!btn) return;
  let big = false;
  try { big = localStorage.getItem("fontScale") === "1.25"; } catch (e) { /* 無法使用儲存空間時忽略 */ }
  const apply = () => {
    document.documentElement.style.setProperty("--scale", big ? "1.25" : "1");
    btn.textContent = big ? "A− 一般字體" : "A+ 放大字體";
    btn.setAttribute("aria-pressed", String(big));
  };
  btn.addEventListener("click", () => {
    big = !big;
    try { localStorage.setItem("fontScale", big ? "1.25" : "1"); } catch (e) { /* 忽略 */ }
    apply();
  });
  apply();
}

// ---------- 首頁 ----------
async function renderIndex() {
  const grid = document.getElementById("grid");
  const filters = document.getElementById("filters");
  try {
    const catalog = (await getJSON("data/catalog.json")).sort((a, b) => a.order - b.order);
    document.getElementById("count").textContent = catalog.length;
    const cats = ["全部", ...new Set(catalog.map((c) => c.category))];
    let current = "全部";
    const draw = () => {
      grid.innerHTML = catalog
        .filter((c) => current === "全部" || c.category === current)
        .map((c) => `
        <article class="card">
          <span class="tag ${c.category === "照護技巧" ? "skill" : ""}">${esc(c.category)}</span>
          <h2>${esc(c.title)}</h2>
          <p>${esc(c.summary)}</p>
          <div class="meta"><span>${esc(c.code)}</span><span>${esc(c.unit)}</span><span>${c.sections} 個段落</span></div>
          <a class="btn primary" href="leaflet.html?id=${encodeURIComponent(c.id)}">開始閱讀 →</a>
        </article>`).join("");
      filters.querySelectorAll(".chip").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.cat === current)));
    };
    filters.innerHTML = cats.map((c) => `<button class="chip" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
    filters.addEventListener("click", (e) => {
      const b = e.target.closest(".chip");
      if (b) { current = b.dataset.cat; draw(); }
    });
    draw();
  } catch (err) {
    grid.innerHTML = `<div class="error">${esc(err.message)}</div>`;
  }
}

// ---------- 單張頁 ----------
async function renderLeaflet() {
  const main = document.getElementById("leaflet");
  const id = new URLSearchParams(location.search).get("id");
  try {
    if (!id || !/^[a-z0-9-]+$/.test(id)) throw new Error("網址缺少有效的單張代號，例如 leaflet.html?id=pneumonia");
    const [d, catalog] = await Promise.all([getJSON(`leaflets/${id}.json`), getJSON("data/catalog.json")]);
    document.title = `${d.title}｜胸腔衛教單張庫`;
    const sorted = catalog.sort((a, b) => a.order - b.order);
    const i = sorted.findIndex((c) => c.id === d.id);
    const prev = sorted[i - 1], next = sorted[i + 1];

    const sections = d.content.map((b, n) => {
      const bullets = b.items.filter((it) => it.type === "bullet");
      const paras = b.items.filter((it) => it.type === "paragraph");
      return `
      <section class="section ${b.alert ? "alert" : ""}" id="s${n + 1}">
        <h2><span class="num">${b.alert ? "!" : n + 1}</span>${esc(b.heading)}</h2>
        ${paras.map((p) => `<p>${esc(p.text)}</p>`).join("")}
        ${bullets.length ? `<ul>${bullets.map((it) => `<li>${esc(it.text)}</li>`).join("")}</ul>` : ""}
      </section>`;
    }).join("");

    const quiz = d.quiz.questions.length ? `
      <section class="section quiz" id="quiz">
        <h2><span class="num">?</span>複習一下</h2>
        <ol>${d.quiz.questions.map((q) => `<li>${esc(q)}</li>`).join("")}</ol>
        <details><summary>看答案</summary><p>${esc(d.quiz.answers)}</p></details>
      </section>` : "";

    main.innerHTML = `
      <div class="wrap leaflet-head">
        <a class="back" href="./">← 回到單張庫</a>
        <h1>${esc(d.title)}</h1>
        <div class="facts">
          <span class="fact">${esc(d.category)}</span>
          <span class="fact">單張編號 ${esc(d.code)}</span>
          <span class="fact">制訂單位 ${esc(d.unit)}</span>
          <span class="fact">制修訂日期 ${esc(d.revised_date)}</span>
          <span class="fact">諮詢 ${esc(d.contact)}</span>
        </div>
      </div>
      <div class="wrap layout">
        <nav class="toc" aria-label="段落目錄"><strong>本單內容</strong>
          <ol>${d.content.map((b, n) => `<li><a href="#s${n + 1}">${esc(b.heading)}</a></li>`).join("")}
          ${quiz ? `<li><a href="#quiz">複習一下</a></li>` : ""}</ol>
        </nav>
        <div>
          ${sections}${quiz}
          ${d.notice ? `<div class="notice">${esc(d.notice)}</div>` : ""}
          <section class="refs"><strong>參考資料</strong><ol>${d.references.map((r) => `<li>${esc(r)}</li>`).join("")}</ol>
            <p>原始文字檔：<a href="${REPO_URL}/blob/main/${esc(d.source_file)}">${esc(d.source_file)}</a></p></section>
          <nav class="pager">
            ${prev ? `<a href="leaflet.html?id=${prev.id}"><span>← 上一份</span>${esc(prev.title)}</a>` : "<span></span>"}
            ${next ? `<a class="next" href="leaflet.html?id=${next.id}"><span>下一份 →</span>${esc(next.title)}</a>` : "<span></span>"}
          </nav>
        </div>
      </div>`;
  } catch (err) {
    main.innerHTML = `<div class="wrap" style="padding:2rem 0"><div class="error">${esc(err.message)}</div><p><a href="./">← 回到單張庫</a></p></div>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupFontToggle();
  const page = document.body.dataset.page;
  if (page === "index") renderIndex();
  if (page === "leaflet") renderLeaflet();
  const print = document.getElementById("printBtn");
  if (print) print.addEventListener("click", () => window.print());
});
