/*
 * Visitor comments written ON the site (no account needed).
 *
 * Backend: a Supabase project whose table is closed to everyone. The browser can only
 * call three database functions:
 *   post_comment(...)    -> publishes a clean comment at once ("ok"), or holds a suspicious one ("held")
 *   comments_for(mod)    -> published comments (each with a random pub_id, no internal ids)
 *   report_comment(id)   -> one report per visitor; 3 reports hide an auto-published comment
 * The owner moderates from admin.html with a moderation key (see admin.js).
 * The publishable key below is meant to be public; it grants nothing else.
 * Every value from the server is treated as untrusted and escaped before display.
 */
(() => {
  const API = "https://eqcexrzutbqaubzyelce.supabase.co/rest/v1/rpc/";
  const KEY = "sb_publishable_Xr62lm36FzgCdcfiIn-j_Q_BfNwFNVe";
  const { esc } = MC;
  const KINDS = { pro: ["👍", "عجبني"], con: ["👎", "ما عجبني"], bug: ["🐞", "مشكلة"], idea: ["💡", "اقتراح"] };
  const DEVICES = { phone: "📱 جوال", pc: "💻 كمبيوتر", console: "🎮 كونسول" };
  const ID_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
  const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
  // Same idea as the database rule: no links, markup or e-mail-like text.
  // (checked after NFKC, so fullwidth letters and dots count too; the database repeats every check)
  const LINK_RE = /(https?:|www\.|[a-z0-9-]+(\.|\[\.\]|\(\.\)|\[dot\]|。|٫)(com|net|org|io|xyz|ru|ly|me|gg|link|site|top|co|shop|app|dev|tv|info|biz|store|online|live|tk|ml|cc|to|us|uk)\b|[<>]|@[a-z0-9_.-]+\.|discord\.gg|t\.me\/)/i;
  const hasLink = (t) => LINK_RE.test(t.normalize("NFKC"));
  const TWO_CHARS = /[\p{L}\p{N}].*[\p{L}\p{N}]/su;
  const MESSAGES = {
    ok: "✔ انشر رأيك! شكراً 💚",
    held: "✔ وصل رأيك! راح يظهر بعد ما يشوفه صاحب الموقع. 💚",
    too_short: "اكتب رأيك أول (حرفين على الأقل).",
    bad_mod: "هذا العمل ما يقبل آراء هسه.",
    too_long: "رأيك طويل كلش، اختصره شوية.",
    no_links: "ممنوع الروابط والإيميلات بالرأي. اكتب كلام بس.",
    bad_nickname: "الاسم بس حروف وأرقام.",
    busy: "فيه آراء كثيرة هسه، جرّب بعد شوية.",
    limit: "أرسلت آراء كثيرة، انتظر شوية وجرّب.",
    error: "صار خطأ بالاتصال. جرّب مرة ثانية.",
  };

  async function rpc(fn, body) {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 9000);
    try {
      const r = await fetch(API + fn, {
        method: "POST",
        headers: { apikey: KEY, "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctl.signal,
        credentials: "omit",
        referrerPolicy: "no-referrer",
      });
      if (!r.ok) throw new Error(String(r.status));
      return await r.json();
    } finally {
      clearTimeout(t);
    }
  }

  // Approved comments are cached per tab for 5 minutes, so browsing back and forth does not
  // call the database again (keeps the free plan's monthly traffic small).
  const CACHE_MS = 5 * 60 * 1000;
  function cached(modId) {
    try {
      const c = JSON.parse(sessionStorage.getItem("nabd.c." + modId) || "null");
      return c && typeof c.at === "number" && Date.now() - c.at >= 0 && Date.now() - c.at < CACHE_MS && Array.isArray(c.rows) ? c.rows : null;
    } catch { return null; }
  }
  function store(modId, rows) {
    try { sessionStorage.setItem("nabd.c." + modId, JSON.stringify({ at: Date.now(), rows })); } catch { /* full / private mode */ }
  }

  /** Approved comments from the database, cleaned like everything else (also when read from the cache). */
  async function loadSiteComments(modId) {
    try {
      let rows = cached(modId);
      if (!rows) { rows = await rpc("comments_for", { p_mod: modId }); if (Array.isArray(rows) && rows.length) store(modId, rows.slice(0, 50)); } // empty lists are tiny: not cached, so a new approval shows at once
      return (Array.isArray(rows) ? rows : []).slice(0, 50).filter((r) => r && Object.hasOwn(KINDS, r.kind)
        && typeof r.body === "string" && r.body).map((r) => ({
        kind: r.kind,
        text: Array.from(r.body).slice(0, 600).join(""),
        name: typeof r.nickname === "string" && r.nickname ? Array.from(r.nickname).slice(0, 30).join("") : "لاعب",
        date: /^[0-9]{4}-[0-9]{2}-[0-9]{2}/.test(r.approved_at || "") ? r.approved_at.slice(0, 10) : "",
        device: Object.hasOwn(DEVICES, r.device) ? r.device : "",
        pid: typeof r.pub_id === "string" && UUID_RE.test(r.pub_id) ? r.pub_id : "",
      }));
    } catch {
      return null; // offline / paused: the section still works without the list
    }
  }

  // Simple per-browser limit: 3 comments per 10 minutes (the database has its own limits).
  function underLimit() {
    try {
      const now = Date.now();
      const list = JSON.parse(localStorage.getItem("nabd.sent") || "[]").filter((t) => typeof t === "number" && now - t < 6e5);
      return list.length < 3;
    } catch { return true; }
  }
  function remember() {
    try {
      const now = Date.now();
      const list = JSON.parse(localStorage.getItem("nabd.sent") || "[]").filter((t) => typeof t === "number" && now - t < 6e5);
      list.push(now);
      localStorage.setItem("nabd.sent", JSON.stringify(list));
    } catch { /* ignore */ }
  }

  // Reports this browser already sent (so the button shows "reported" and is not pressed twice).
  const reported = () => { try { const a = JSON.parse(localStorage.getItem("nabd.rep") || "[]"); return Array.isArray(a) ? a.filter((x) => typeof x === "string") : []; } catch { return []; } };
  const markReported = (pid) => { try { localStorage.setItem("nabd.rep", JSON.stringify([...reported(), pid].slice(-200))); } catch { /* ignore */ } };

  function itemHtml(c) {
    const [icon, label] = KINDS[c.kind];
    const rep = c.pid ? (reported().includes(c.pid) ? `<span class="c-rep done">🚩 بلّغت</span>`
      : `<button type="button" class="c-rep" data-pid="${esc(c.pid)}" title="بلّغ عن كلام مسيء أو سبام">🚩 بلّغ</button>`) : "";
    return `<li class="fb fb-${c.kind}"><span class="fb-kind">${icon} ${esc(label)}</span><p>${esc(c.text)}</p>
      <small>— <bdi>${esc(c.name)}</bdi>${c.date ? ` · ${esc(c.date)}` : ""}${c.device ? ` · ${esc(DEVICES[c.device])}` : ""}</small>${rep}</li>`;
  }

  /**
   * Render the comments section for one item into `el`.
   * ghItems: approved feedback from feedback.json (GitHub path), already cleaned by MC.cleanFeedback.
   */
  function mount(el, modId, ghItems = []) {
    if (!el || !ID_RE.test(modId || "")) return;
    const fromGithub = ghItems.filter((i) => i.mod === modId).map((i) => ({
      kind: i.kind === "pro" || i.kind === "con" || i.kind === "bug" || i.kind === "idea" ? i.kind : "idea",
      text: i.text, name: i.user, date: i.date, device: i.device || "",
    }));
    el.innerHTML = `<section class="feedback comments">
      <h4>💬 آراء اللاعبين</h4>
      <div class="meta c-counts"></div>
      <ul class="fb-list c-list"><li class="muted-note c-loading">جاري التحميل…</li></ul>
      <form class="cform" novalidate>
        <h5>✍️ اكتب رأيك أو بلّغ عن مشكلة</h5>
        <div class="kind-pick" role="radiogroup" aria-label="نوع الرأي">
          ${Object.entries(KINDS).map(([k, [icon, label]], i) =>
            `<label><input type="radio" name="kind" value="${k}" ${i === 0 ? "checked" : ""}><span>${icon} ${label}</span></label>`).join("")}
        </div>
        <textarea name="body" rows="3" maxlength="600" required placeholder="اكتب رأيك هنا… (بدون روابط)"></textarea>
        <div class="c-row">
          <input name="nick" maxlength="30" autocomplete="nickname" placeholder="اسمك (اختياري)">
          <select name="device" aria-label="جهازك">
            <option value="">جهازك (اختياري)</option>
            <option value="phone">📱 جوال</option><option value="pc">💻 كمبيوتر</option><option value="console">🎮 كونسول</option>
          </select>
        </div>
        <input name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
        <button class="mc-btn mc-btn-green" type="submit">📨 إرسال</button>
        <p class="c-msg" role="status"></p>
        <p class="muted-note">رأيك يطلع فوراً. الكلام المسيء والسبام يتشال. لا تكتب معلوماتك الشخصية (رقم، إيميل، عنوان).</p>
      </form>
    </section>`;

    const list = el.querySelector(".c-list");
    const counts = el.querySelector(".c-counts");
    const render = (items) => {
      list.innerHTML = items.length ? items.slice(0, 60).map(itemHtml).join("")
        : `<li class="muted-note">ما فيه آراء بعد. كن أول واحد!</li>`;
      const n = Object.keys(KINDS).map((k) => [k, items.filter((i) => i.kind === k).length]).filter(([, c]) => c);
      counts.innerHTML = n.map(([k, c]) => `<span class="chip">${KINDS[k][0]} ${c}</span>`).join(" ");
    };
    if (fromGithub.length) render(fromGithub);
    list.addEventListener("click", async (e) => {
      const b = e.target.closest("button.c-rep");
      if (!b || !UUID_RE.test(b.dataset.pid || "")) return;
      if (b.dataset.confirm !== "1") { b.dataset.confirm = "1"; b.textContent = "🚩 متأكد؟ اضغط مرة ثانية"; return; }
      b.disabled = true;
      try {
        const r = await rpc("report_comment", { p_pub_id: b.dataset.pid });
        if (r === "ok" || r === "already") { markReported(b.dataset.pid); b.textContent = "🚩 وصل البلاغ، شكراً"; }
        else b.textContent = r === "limit" ? "بلّغت كثير اليوم" : "ما زبط";
      } catch { b.disabled = false; b.textContent = "ما زبط، جرّب مرة ثانية"; }
    });
    const loadList = () => loadSiteComments(modId).then((site) => {
      if (site === null) { if (!fromGithub.length) list.innerHTML = `<li class="muted-note">ما قدرنا نحمّل الآراء هسه.</li>`; return; }
      render([...site, ...fromGithub].sort((a, b) => (b.date || "").localeCompare(a.date || "")));
    });
    // Ask the database only when the visitor actually reaches the comments.
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        if (entries.some((e) => e.isIntersecting)) { io.disconnect(); loadList(); }
      }, { rootMargin: "300px" });
      io.observe(el);
    } else loadList();

    const form = el.querySelector(".cform");
    const msg = el.querySelector(".c-msg");
    const opened = Date.now();
    const say = (key, ok = false) => { msg.textContent = MESSAGES[key] || MESSAGES.error; msg.classList.toggle("ok", ok); };
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector("button");
      const body = form.body.value.trim();
      const nick = form.nick.value.trim();
      if (form.website.value || Date.now() - opened < 2500) return say("ok", true); // bot: pretend success
      if (!TWO_CHARS.test(body)) return say("too_short");
      if (hasLink(body) || hasLink(nick)) return say("no_links");
      if (nick && (!/^[\p{L}\p{N} _.-]+$/u.test(nick) || !/[\p{L}\p{N}]/u.test(nick))) return say("bad_nickname");
      if (!underLimit()) return say("limit");
      btn.disabled = true;
      try {
        const res = await rpc("post_comment", {
          p_mod: modId, p_kind: form.kind.value, p_body: body, p_nickname: nick || null, p_device: form.device.value || null,
        });
        const key = typeof res === "string" ? res : "error";
        say(Object.hasOwn(MESSAGES, key) ? key : "error", key === "ok" || key === "held");
        if (key === "ok" || key === "held") { remember(); form.reset(); }
        if (key === "ok") { try { sessionStorage.removeItem("nabd.c." + modId); } catch { /* ignore */ } loadList(); }
      } catch {
        say("error");
      } finally {
        btn.disabled = false;
      }
    });
  }

  MC.comments = { mount, rpc, KINDS, DEVICES };
})();
