(() => {
  const { guideFor, TYPES, EDITIONS, esc, safeUrl, safeColor, ytId, fmtNum, isRecent } = MC;
  const $ = (s) => document.querySelector(s);
  const state = { site: {}, mods: [], counts: {}, type: "", edition: "", q: "", version: "", sort: "new" };

  init();

  async function init() {
    let data;
    try {
      const r = await fetch("mods.json", { cache: "no-cache" });
      if (!r.ok) throw new Error(r.status);
      data = await r.json();
    } catch {
      $("#grid").innerHTML = "";
      showEmpty("تعذر تحميل قائمة الأعمال، حاول تحدّث الصفحة.");
      return;
    }
    state.site = data.site || {};
    state.mods = (Array.isArray(data.mods) ? data.mods : []).filter((m) => m && m.id && m.name);
    setupSite();
    buildControls();
    render();
    openFromHash();

    if (state.mods.some((m) => (m.releases || []).length)) {
      state.counts = await loadCounts();
      renderStats();
      render();
    }
  }

  /** Download counts: the static stats.json made at deploy time, else GitHub's API. */
  async function loadCounts() {
    try {
      const r = await fetch("stats.json", { cache: "no-cache" });
      if (r.ok) {
        const j = await r.json();
        if (j && typeof j.tags === "object" && Object.keys(j.tags).length) return j.tags;
      }
    } catch { /* fall back below */ }
    const repo = MC.repoOf(state.site);
    return repo ? MC.downloadCounts(repo) : {};
  }

  /* ---------- Site chrome ---------- */
  function setupSite() {
    const s = state.site;
    if (s.name) {
      $("#siteName").textContent = s.name;
      $("#footerName").textContent = s.name;
      document.title = `${s.name} — مودات وإضافات ماين كرافت`;
    }
    if (s.tagline) $("#tagline").textContent = s.tagline;
    if (s.about) $("#aboutText").textContent = s.about;
    $("#year").textContent = new Date().getFullYear();
    const links = [
      [s.donate, "❤ ادعمني"], [s.youtube, "▶ يوتيوب"], [s.discord, "💬 ديسكورد"], [s.tiktok, "🎵 تيك توك"], [s.website, "🌐 موقع آخر"],
    ].filter(([u]) => /^https:\/\//i.test(u || "") && safeUrl(u));
    $("#socials").innerHTML = links
      .map(([u, label]) => `<a class="mc-btn" href="${esc(safeUrl(u))}" target="_blank" rel="noopener noreferrer">${label}</a>`)
      .join("");
    if (/^https:\/\//i.test(s.donate || "") && safeUrl(s.donate)) {
      const a = $("#navDonate");
      a.href = safeUrl(s.donate);
      a.hidden = false;
    }
    renderStats();
  }

  function renderStats() {
    const total = state.mods.reduce((s, m) => s + MC.downloadsOf(m, state.counts), 0);
    const items = [[state.mods.length, "عمل منشور"]];
    const types = new Set(state.mods.map((m) => m.type)).size;
    if (types) items.push([types, "أقسام"]);
    if (total) items.push([fmtNum(total), "تحميل"]);
    $("#stats").innerHTML = items.map(([n, l]) => `<div class="stat"><b>${esc(n)}</b><span>${esc(l)}</span></div>`).join("");
  }

  function buildControls() {
    const counts = {};
    state.mods.forEach((m) => { counts[m.type] = (counts[m.type] || 0) + 1; });
    const tabs = [`<button class="tab active" role="tab" aria-selected="true" data-type="">الكل <small>${state.mods.length}</small></button>`]
      .concat(Object.entries(TYPES).filter(([t]) => counts[t])
        .map(([t, d]) => `<button class="tab" role="tab" aria-selected="false" data-type="${t}">${d.icon} ${d.plural} <small>${counts[t]}</small></button>`));
    $("#tabs").innerHTML = tabs.join("");

    const versions = [...new Set(state.mods.flatMap((m) => m.versions || []))]
      .sort((a, b) => String(b).localeCompare(String(a), undefined, { numeric: true }));
    $("#versionFilter").insertAdjacentHTML("beforeend", versions.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join(""));

    $("#tabs").addEventListener("click", (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;
      document.querySelectorAll(".tab").forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-selected", b === btn);
      });
      state.type = btn.dataset.type;
      render();
    });
    let t;
    $("#search").addEventListener("input", (e) => {
      clearTimeout(t);
      t = setTimeout(() => { state.q = e.target.value.trim().toLowerCase(); render(); }, 120);
    });
    $("#editionFilter").addEventListener("change", (e) => { state.edition = e.target.value; render(); });
    $("#versionFilter").addEventListener("change", (e) => { state.version = e.target.value; render(); });
    $("#sortBy").addEventListener("change", (e) => { state.sort = e.target.value; render(); });
  }

  /* ---------- Listing ---------- */
  function filtered() {
    const dl = (m) => MC.downloadsOf(m, state.counts);
    const date = (m) => String(m.updated || m.date || "");
    return state.mods
      .filter((m) => !state.type || m.type === state.type)
      .filter((m) => !state.edition || m.edition === state.edition)
      .filter((m) => !state.version || (m.versions || []).includes(state.version))
      .filter((m) => {
        if (!state.q) return true;
        return [m.name, m.description, m.loader, ...(m.tags || []), TYPES[m.type]?.label]
          .join(" ").toLowerCase().includes(state.q);
      })
      .sort((a, b) => {
        if (state.sort === "name") return a.name.localeCompare(b.name, "ar");
        if (state.sort === "popular") return dl(b) - dl(a) || date(b).localeCompare(date(a));
        return (b.featured === true) - (a.featured === true) || date(b).localeCompare(date(a));
      });
  }

  function thumbHtml(m, big = false) {
    const t = TYPES[m.type] || { label: "", icon: "📦" };
    const img = safeUrl(m.image);
    const badges = [`<span class="badge">${esc(t.label)}</span>`];
    if (isRecent(m.updated || m.date)) badges.push(`<span class="badge badge-new">${m.updated && m.updated !== m.date ? "محدَّث" : "جديد"}</span>`);
    if (m.featured === true) badges.push(`<span class="badge badge-star">⭐ مميز</span>`);
    return `<div class="thumb${img ? "" : " generated"}" data-color="${esc(safeColor(m.color))}">
      ${img ? `<img src="${esc(img)}" alt="" loading="${big ? "eager" : "lazy"}" decoding="async">` : `<span class="thumb-icon">${t.icon}</span>`}
      <div class="badges">${badges.join("")}</div>
    </div>`;
  }

  function cardHtml(m) {
    const dl = MC.downloadsOf(m, state.counts);
    const file = safeUrl(m.file);
    return `
      <article class="card" tabindex="0" data-id="${esc(m.id)}" aria-label="${esc(m.name)}">
        ${thumbHtml(m)}
        <div class="card-body">
          <h3><a href="m/${encodeURIComponent(m.id)}/">${esc(m.name)}</a></h3>
          <p>${esc(m.description)}</p>
          <div class="meta">
            ${EDITIONS[m.edition] ? `<span class="chip chip-${esc(m.edition)}">${EDITIONS[m.edition]}</span>` : ""}
            ${m.loader ? `<span class="chip">${esc(m.loader)}</span>` : ""}
            ${(m.versions || []).slice(0, 3).map((v) => `<span class="chip">${esc(v)}</span>`).join("")}
          </div>
        </div>
        <div class="card-foot">
          <small>${esc(m.size || "")}${dl ? ` · ⬇ ${fmtNum(dl)}` : ""}</small>
          ${file ? `<button class="mc-btn mc-btn-green" type="button">⬇ تحميل</button>` : ""}
        </div>
      </article>`;
  }

  function paintColors(root) {
    root.querySelectorAll(".thumb[data-color]").forEach((el) => { el.style.backgroundColor = el.dataset.color; });
  }

  function showEmpty(msg) {
    $("#empty").textContent = msg;
    $("#empty").hidden = false;
  }

  function render() {
    const list = filtered();
    $("#empty").hidden = true;
    if (!state.mods.length) showEmpty("قريباً! أول الأعمال في الطريق ⛏");
    else if (!list.length) showEmpty("ما لقينا شي يطابق بحثك 🧐");
    $("#grid").innerHTML = list.map(cardHtml).join("");
    paintColors($("#grid"));

    const feat = state.mods.filter((m) => m.featured === true).slice(0, 1)[0];
    const fs = $("#featured");
    fs.hidden = !feat;
    if (feat && !fs.dataset.done) {
      fs.dataset.done = "1";
      fs.innerHTML = `<div class="feature-card" data-id="${esc(feat.id)}" tabindex="0">
        ${thumbHtml(feat, true)}
        <div class="feature-body">
          <span class="kicker">⭐ العمل المميز</span>
          <h2>${esc(feat.name)}</h2>
          <p>${esc(feat.description)}</p>
          <button class="mc-btn mc-btn-gold" type="button">التفاصيل والتحميل</button>
        </div>
      </div>`;
      paintColors(fs);
    }
  }

  const openFromEvent = (e) => {
    if (e.target.closest("[data-dl]")) return;
    const el = e.target.closest("[data-id]");
    if (el && (e.type === "click" || (e.key === "Enter" && e.target === el))) {
      if (e.type === "click" && !(e.ctrlKey || e.metaKey || e.shiftKey)) e.preventDefault(); // links are for search engines / new tabs
      openModal(el.dataset.id);
    }
  };
  ["click", "keydown"].forEach((ev) => {
    $("#grid").addEventListener(ev, openFromEvent);
    $("#featured").addEventListener(ev, openFromEvent);
  });

  /* ---------- Details modal ---------- */
  function openModal(id) {
    const m = state.mods.find((x) => x.id === id);
    if (!m) return;
    const t = TYPES[m.type] || { label: m.type };
    const pageUrl = `${location.origin}${location.pathname.replace(/[^/]*$/, "")}m/${encodeURIComponent(m.id)}/`;
    const shots = (m.screenshots || []).map(safeUrl).filter(Boolean);
    const video = ytId(m.video);
    const file = safeUrl(m.file);
    const dl = MC.downloadsOf(m, state.counts);
    const rows = [
      ["النوع", t.label],
      ["النسخة", EDITIONS[m.edition]],
      ["المحمّل / الصيغة", m.loader],
      ["إصدارات ماين كرافت", (m.versions || []).join("، ")],
      ["إصدار الملف", m.version],
      ["الحجم", m.size],
      ["التحميلات", dl ? fmtNum(dl) : ""],
      ["تاريخ النشر", m.date],
      ["آخر تحديث", m.updated && m.updated !== m.date ? m.updated : ""],
    ].filter(([, v]) => v);

    const guide = guideFor(m);
    const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    const startTab = Math.max(0, guide.findIndex((g) => g.label.includes(mobile ? "جوال" : "كمبيوتر")));
    const fits = [EDITIONS[m.edition], (m.versions || []).join("، ")].filter(Boolean).join(" ");
    const shareText = encodeURIComponent(`${m.name} — ${pageUrl}`);
    const donate = /^https:\/\//i.test(state.site.donate || "") ? safeUrl(state.site.donate) : "";

    $("#modalBody").innerHTML = `
      ${thumbHtml(m, true)}
      <div class="modal-content">
        <h2 id="modalTitle">${esc(m.name)}</h2>
        <p class="lead">${esc(m.description)}</p>

        <div class="dl-box">
          ${file ? `<a class="mc-btn mc-btn-green mc-btn-big" id="dlBtn" href="${esc(file)}" rel="noopener">⬇ تحميل ${esc(m.size || "")}</a>` : `<p>رابط التحميل غير متوفر حالياً.</p>`}
          <p class="fits">✔ يشتغل على: <b>${esc(fits)}</b>${m.loader ? ` · يحتاج <b>${esc(m.loader)}</b>` : ""}</p>
          <p class="dl-started" id="dlStarted" hidden>✔ بدأ التحميل! الحين سوّ الخطوات اللي تحت 👇</p>
        </div>

        <div class="guide" id="guide">
          <h3>🛠 شلون أثبّته؟</h3>
          ${guide.length > 1 ? `<div class="guide-tabs" role="tablist">${guide.map((g, i) =>
            `<button type="button" role="tab" class="${i === startTab ? "active" : ""}" data-tab="${i}" aria-selected="${i === startTab}">${g.label}</button>`).join("")}</div>` : ""}
          ${guide.map((g, i) => `<ol class="steps" data-panel="${i}" ${i === startTab ? "" : "hidden"}>${g.steps.map((st) => `<li>${st}</li>`).join("")}</ol>`).join("")}
          <p class="muted-note">ما زبط؟ شوف <a href="#faq" data-close-modal>الأسئلة الشائعة</a>.</p>
        </div>

        ${m.details ? `<h4>عن هذا العمل</h4><div class="details-text">${esc(m.details).replace(/\n/g, "<br>")}</div>` : ""}
        ${shots.length ? `<h4>صور</h4><div class="gallery">${shots.map((s, i) =>
          `<button type="button" class="shot" data-src="${esc(s)}" aria-label="صورة ${i + 1}"><img src="${esc(s)}" alt="" loading="lazy"></button>`).join("")}</div>` : ""}
        ${video ? `<h4>فيديو</h4><div class="video"><iframe src="https://www.youtube-nocookie.com/embed/${video}" title="فيديو ${esc(m.name)}" loading="lazy" allow="encrypted-media; picture-in-picture; fullscreen" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>` : ""}
        <h4>معلومات</h4>
        <table class="info-table">${rows.map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join("")}</table>
        ${(m.tags || []).length ? `<div class="meta tags">${m.tags.map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</div>` : ""}
        ${(m.changelog || []).length ? `<h4>سجل التحديثات</h4><ul class="changelog">${m.changelog.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : ""}
        ${/^[0-9a-f]{64}$/.test(m.sha256 || "") ? `<details class="hash"><summary>🔒 بصمة الملف (SHA-256) للتأكد إنه أصلي</summary><code dir="ltr">${m.sha256}</code></details>` : ""}
        <div class="actions">
          <a class="mc-btn mc-btn-wa" href="https://wa.me/?text=${shareText}" target="_blank" rel="noopener noreferrer">📤 واتساب</a>
          <button class="mc-btn mc-btn-gold" type="button" id="shareBtn">🔗 نسخ الرابط</button>
          ${donate ? `<a class="mc-btn mc-btn-red" href="${esc(donate)}" target="_blank" rel="noopener noreferrer">❤ ادعمني</a>` : ""}
        </div>
      </div>`;
    paintColors($("#modalBody"));

    $("#modalBody").querySelectorAll(".shot").forEach((b) => b.addEventListener("click", () => {
      const thumb = $("#modalBody .thumb");
      let img = thumb.querySelector("img");
      if (!img) {
        img = document.createElement("img");
        thumb.prepend(img);
        thumb.classList.remove("generated");
        thumb.querySelector(".thumb-icon")?.remove();
      }
      img.src = b.dataset.src;
      thumb.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }));
    $("#modalBody").querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => {
      $("#modalBody").querySelectorAll("[data-tab]").forEach((x) => { x.classList.toggle("active", x === b); x.setAttribute("aria-selected", x === b); });
      $("#modalBody").querySelectorAll("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== b.dataset.tab; });
    }));
    $("#dlBtn")?.addEventListener("click", () => {
      $("#dlStarted").hidden = false;
      $("#guide").classList.add("flash");
      setTimeout(() => $("#guide").scrollIntoView({ behavior: "smooth", block: "start" }), 300);
    });
    $("#modalBody [data-close-modal]")?.addEventListener("click", () => modal.close());
    $("#shareBtn").addEventListener("click", async (e) => {
      try { await navigator.clipboard.writeText(pageUrl); e.target.textContent = "✔ تم النسخ"; }
      catch { prompt("انسخ الرابط:", pageUrl); }
    });
    history.replaceState(null, "", `#${encodeURIComponent(m.id)}`);
    if (!modal.open) modal.showModal();
    modal.scrollTop = 0;
  }

  function openFromHash() {
    let id = "";
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { /* bad hash */ }
    if (id && state.mods.some((m) => m.id === id)) openModal(id);
  }

  const modal = $("#modal");
  $("#closeModal").addEventListener("click", () => modal.close());
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.close(); });
  modal.addEventListener("close", () => {
    $("#modalBody").innerHTML = ""; // stops any playing video
    history.replaceState(null, "", location.pathname + location.search);
  });
  window.addEventListener("hashchange", openFromHash);
})();
