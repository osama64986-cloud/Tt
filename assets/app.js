(() => {
  const TYPES = {
    mod:     { label: "مود",   icon: "⚒" },
    texture: { label: "تكستر", icon: "🎨" },
    map:     { label: "خريطة", icon: "🗺" },
    world:   { label: "عالم",  icon: "🌍" },
  };

  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = (u) => (/^(https?:\/\/|\.?\/?[\w\-./%]+$)/i.test(u || "") && !/^javascript:/i.test(u) ? u : "#");

  const state = { mods: [], type: "", q: "", version: "", sort: "new" };

  fetch("mods.json", { cache: "no-cache" })
    .then((r) => r.json())
    .then((data) => {
      setupSite(data.site || {});
      state.mods = data.mods || [];
      buildFilters();
      render();
      openFromHash();
    })
    .catch(() => {
      $("#grid").innerHTML = '<p class="empty">تعذر تحميل قائمة المودات. تأكد من ملف mods.json</p>';
    });

  function setupSite(site) {
    if (site.name) {
      $("#siteName").textContent = site.name;
      $("#footerName").textContent = site.name;
      document.title = `${site.name} — Minecraft`;
    }
    if (site.tagline) $("#tagline").textContent = site.tagline;
    if (site.author) $("#authorName").textContent = site.author;
    $("#year").textContent = new Date().getFullYear();
    const links = [];
    if (site.youtube) links.push(`<a class="mc-btn" href="${esc(safeUrl(site.youtube))}" target="_blank" rel="noopener">▶ يوتيوب</a>`);
    if (site.discord) links.push(`<a class="mc-btn" href="${esc(safeUrl(site.discord))}" target="_blank" rel="noopener">💬 ديسكورد</a>`);
    $("#socials").innerHTML = links.join("");
  }

  function buildFilters() {
    const versions = [...new Set(state.mods.flatMap((m) => m.versions || []))]
      .sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
    $("#versionFilter").insertAdjacentHTML("beforeend", versions.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join(""));

    const counts = { mod: 0, texture: 0, map: 0, world: 0 };
    state.mods.forEach((m) => { if (m.type in counts) counts[m.type]++; });
    $("#stats").innerHTML = Object.entries(counts)
      .map(([t, n]) => `<div class="stat"><b>${n}</b><span>${TYPES[t].label}</span></div>`).join("");

    $("#tabs").addEventListener("click", (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;
      document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
      state.type = btn.dataset.type;
      render();
    });
    $("#search").addEventListener("input", (e) => { state.q = e.target.value.trim().toLowerCase(); render(); });
    $("#versionFilter").addEventListener("change", (e) => { state.version = e.target.value; render(); });
    $("#sortBy").addEventListener("change", (e) => { state.sort = e.target.value; render(); });
  }

  function filtered() {
    return state.mods
      .filter((m) => !state.type || m.type === state.type)
      .filter((m) => !state.version || (m.versions || []).includes(state.version))
      .filter((m) => {
        if (!state.q) return true;
        const hay = [m.name, m.description, m.loader, ...(m.tags || [])].join(" ").toLowerCase();
        return hay.includes(state.q);
      })
      .sort((a, b) => state.sort === "name"
        ? a.name.localeCompare(b.name, "ar")
        : String(b.date || "").localeCompare(String(a.date || "")));
  }

  function thumb(m) {
    const t = TYPES[m.type] || { label: m.type, icon: "📦" };
    const style = m.image
      ? `background-image:url('${esc(safeUrl(m.image))}')`
      : `background-color:${esc(/^#[0-9a-f]{3,8}$/i.test(m.color || "") ? m.color : "#555")}`;
    return `<div class="thumb ${m.image ? "" : "generated"}" style="${style}">
      ${m.image ? "" : `<span>${t.icon}</span>`}
      <span class="badge">${esc(t.label)}</span>
    </div>`;
  }

  function render() {
    const list = filtered();
    $("#empty").hidden = list.length > 0;
    $("#grid").innerHTML = list.map((m) => `
      <article class="card" tabindex="0" data-id="${esc(m.id)}">
        ${thumb(m)}
        <div class="card-body">
          <h3>${esc(m.name)}</h3>
          <p>${esc(m.description)}</p>
          <div class="meta">
            ${m.loader ? `<span class="chip">${esc(m.loader)}</span>` : ""}
            ${(m.versions || []).map((v) => `<span class="chip">${esc(v)}</span>`).join("")}
          </div>
        </div>
        <div class="card-foot">
          <small>${esc(m.size || "")}</small>
          <a class="mc-btn mc-btn-green" href="${esc(safeUrl(m.file))}" download data-dl>⬇ تحميل</a>
        </div>
      </article>`).join("");
  }

  $("#grid").addEventListener("click", (e) => {
    if (e.target.closest("[data-dl]")) return;
    const card = e.target.closest(".card");
    if (card) openModal(card.dataset.id);
  });
  $("#grid").addEventListener("keydown", (e) => {
    const card = e.target.closest(".card");
    if (card && e.key === "Enter" && e.target === card) openModal(card.dataset.id);
  });

  function openModal(id) {
    const m = state.mods.find((x) => x.id === id);
    if (!m) return;
    const t = TYPES[m.type] || { label: m.type };
    const pageUrl = `${location.origin}${location.pathname}#${encodeURIComponent(m.id)}`;
    $("#modalBody").innerHTML = `
      ${thumb(m)}
      <div class="modal-content">
        <h2>${esc(m.name)}</h2>
        <p>${esc(m.description)}</p>
        ${m.details ? `<p>${esc(m.details)}</p>` : ""}
        <table class="info-table">
          <tr><td>النوع</td><td>${esc(t.label)}</td></tr>
          ${m.loader ? `<tr><td>المحمّل / الصيغة</td><td>${esc(m.loader)}</td></tr>` : ""}
          <tr><td>إصدارات ماين كرافت</td><td dir="ltr" style="text-align:right">${esc((m.versions || []).join(", "))}</td></tr>
          ${m.version ? `<tr><td>إصدار الملف</td><td>${esc(m.version)}</td></tr>` : ""}
          ${m.size ? `<tr><td>الحجم</td><td>${esc(m.size)}</td></tr>` : ""}
          ${m.date ? `<tr><td>تاريخ النشر</td><td>${esc(m.date)}</td></tr>` : ""}
        </table>
        ${(m.tags || []).length ? `<h4>الوسوم</h4><div class="meta">${m.tags.map((x) => `<span class="chip">${esc(x)}</span>`).join("")}</div>` : ""}
        ${(m.changelog || []).length ? `<h4>سجل التحديثات</h4><ul>${m.changelog.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>` : ""}
        <div class="actions">
          <a class="mc-btn mc-btn-green" href="${esc(safeUrl(m.file))}" download>⬇ تحميل ${esc(m.size || "")}</a>
          <button class="mc-btn mc-btn-gold" id="shareBtn">🔗 نسخ الرابط</button>
        </div>
      </div>`;
    $("#shareBtn").onclick = async (e) => {
      try { await navigator.clipboard.writeText(pageUrl); e.target.textContent = "✔ تم النسخ"; }
      catch { prompt("انسخ الرابط:", pageUrl); }
    };
    history.replaceState(null, "", `#${encodeURIComponent(m.id)}`);
    $("#modal").showModal();
  }

  function openFromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && state.mods.some((m) => m.id === id)) openModal(id);
  }

  const modal = $("#modal");
  $("#closeModal").onclick = () => modal.close();
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.close(); });
  modal.addEventListener("close", () => history.replaceState(null, "", location.pathname));
})();
