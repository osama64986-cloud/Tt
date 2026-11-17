/*
 * Visitor comments written ON the site (no account needed).
 *
 * Backend: a Supabase project whose table is closed to everyone. The browser can only
 * call two database functions:
 *   submit_comment(...) -> puts the comment in a private queue (status "pending")
 *   list_comments(mod)  -> returns comments the owner approved
 * The owner approves from admin.html with a moderation key (see admin.js).
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
  // Same idea as the database rule: no links, markup or e-mail-like text.
  const LINK_RE = /(https?:\/\/|www\.|[a-z0-9-]+\.(com|net|org|io|xyz|ru|ly|me|gg|link|site|top)\b|[<>]|@[a-z0-9_.-]+\.)/i;
  const MESSAGES = {
    ok: "✔ وصل رأيك! راح يظهر هنا بعد ما يراجعه صاحب الموقع. شكراً 💚",
    too_short: "اكتب رأيك أول (حرفين على الأقل).",
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

  /** Approved comments from the database, cleaned like everything else. */
  async function loadSiteComments(modId) {
    try {
      const rows = await rpc("list_comments", { p_mod: modId });
      return (Array.isArray(rows) ? rows : []).slice(0, 50).filter((r) => r && Object.hasOwn(KINDS, r.kind)
        && typeof r.body === "string" && r.body).map((r) => ({
        kind: r.kind,
        text: Array.from(r.body).slice(0, 600).join(""),
        name: typeof r.nickname === "string" && r.nickname ? Array.from(r.nickname).slice(0, 30).join("") : "لاعب",
        date: /^[0-9]{4}-[0-9]{2}-[0-9]{2}/.test(r.approved_at || "") ? r.approved_at.slice(0, 10) : "",
        device: Object.hasOwn(DEVICES, r.device) ? r.device : "",
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

  function itemHtml(c) {
    const [icon, label] = KINDS[c.kind];
    return `<li class="fb fb-${c.kind}"><span class="fb-kind">${icon} ${esc(label)}</span><p>${esc(c.text)}</p>
      <small>— <bdi>${esc(c.name)}</bdi>${c.date ? ` · ${esc(c.date)}` : ""}${c.device ? ` · ${esc(DEVICES[c.device])}` : ""}</small></li>`;
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
        <p class="muted-note">رأيك يظهر هنا بعد ما يراجعه صاحب الموقع. لا تكتب معلوماتك الشخصية (رقم، إيميل، عنوان).</p>
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
    render(fromGithub);
    loadSiteComments(modId).then((site) => {
      if (site === null) { if (!fromGithub.length) list.innerHTML = `<li class="muted-note">ما قدرنا نحمّل الآراء هسه.</li>`; return; }
      render([...site, ...fromGithub].sort((a, b) => (b.date || "").localeCompare(a.date || "")));
    });

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
      if (body.length < 2) return say("too_short");
      if (LINK_RE.test(body) || LINK_RE.test(nick)) return say("no_links");
      if (nick && !/^[\p{L}\p{N} _.-]+$/u.test(nick)) return say("bad_nickname");
      if (!underLimit()) return say("limit");
      btn.disabled = true;
      try {
        const res = await rpc("submit_comment", {
          p_mod: modId, p_kind: form.kind.value, p_body: body, p_nickname: nick || null, p_device: form.device.value || null,
        });
        const key = typeof res === "string" ? res : "error";
        say(Object.hasOwn(MESSAGES, key) ? key : "error", key === "ok");
        if (key === "ok") { remember(); form.reset(); }
      } catch {
        say("error");
      } finally {
        btn.disabled = false;
      }
    });
  }

  MC.comments = { mount, rpc, KINDS, DEVICES };
})();
