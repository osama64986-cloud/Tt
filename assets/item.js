/* Item page (m/<id>/): colours, install guide and the download hint. */
(() => {
  const $ = (s) => document.querySelector(s);
  document.querySelectorAll(".thumb[data-color]").forEach((el) => { el.style.backgroundColor = el.dataset.color; });

  const g = $("#guide");
  if (g) {
    const guide = MC.guideFor({ type: g.dataset.type, edition: g.dataset.edition, loader: g.dataset.loader });
    const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    const start = Math.max(0, guide.findIndex((x) => x.label.includes(mobile ? "جوال" : "كمبيوتر")));
    const wrap = document.createElement("div");
    wrap.innerHTML = (guide.length > 1 ? `<div class="guide-tabs" role="tablist">${guide.map((x, i) =>
      `<button type="button" role="tab" class="${i === start ? "active" : ""}" data-tab="${i}" aria-selected="${i === start}">${x.label}</button>`).join("")}</div>` : "")
      + guide.map((x, i) => `<ol class="steps" data-panel="${i}" ${i === start ? "" : "hidden"}>${x.steps.map((s) => `<li>${s}</li>`).join("")}</ol>`).join("")
      + `<p class="muted-note">ما زبط؟ شوف <a href="../../#faq">الأسئلة الشائعة</a>.</p>`;
    g.append(wrap);
    g.addEventListener("click", (e) => {
      const b = e.target.closest("[data-tab]");
      if (!b) return;
      g.querySelectorAll("[data-tab]").forEach((x) => { x.classList.toggle("active", x === b); x.setAttribute("aria-selected", x === b); });
      g.querySelectorAll("[data-panel]").forEach((p) => { p.hidden = p.dataset.panel !== b.dataset.tab; });
    });
  }
  $("#dlBtn")?.addEventListener("click", () => {
    $("#dlStarted").hidden = false;
    g?.classList.add("flash");
    setTimeout(() => g?.scrollIntoView({ behavior: "smooth", block: "start" }), 300);
  });
})();
