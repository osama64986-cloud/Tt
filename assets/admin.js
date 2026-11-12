/*
 * Owner-only admin panel.
 *
 * Nothing here is secret: the page is useless without a GitHub token that has
 * write access to the repository. GitHub itself enforces who can change what.
 *
 * Publishing flow (all calls go to api.github.com, which allows CORS):
 *   1. upload each file as a git blob
 *   2. commit them, plus inbox/meta.json, to a throwaway branch "inbox/<id>"
 *   3. start the "publish.yml" workflow, which validates everything, creates the
 *      GitHub Release, updates mods.json, redeploys the site and deletes the branch
 */
(() => {
  // Refuse to run inside a frame (clickjacking protection; Pages can't send headers).
  if (window.top !== window.self) { document.documentElement.innerHTML = ""; return; }

  const { TYPES, EDITIONS, esc, safeUrl, safeColor, fmtNum, parseYouTube } = MC;
  const $ = (s, r = document) => r.querySelector(s);
  const LOCAL = ["localhost", "127.0.0.1"].includes(location.hostname);
  // A custom API host is only honoured on a local dev machine, never on the live site.
  const API = (LOCAL && localStorage.getItem("mc.apiBase")) || "https://api.github.com";
  const WORKFLOW = "publish.yml";
  const MAX_FILE = 95 * 1024 * 1024;
  const STORE_KEY = "mc.admin";      // sessionStorage: this tab only, cleared on close
  const VAULT_KEY = "mc.admin.vault"; // localStorage: token encrypted with the owner's password
  const IDLE_MS = 30 * 60 * 1000;     // auto-lock after 30 minutes without activity

  let auth = null;      // { token, repo, login }
  let data = { site: {}, mods: [] };
  let counts = {};
  let editing = null;   // id of the item being edited, or null for new
  let busy = false;
  let tokenExpiry = null;

  /* ---------- GitHub API ---------- */
  async function gh(path, { method = "GET", body, raw = false, token = auth?.token } = {}) {
    const res = await fetch(API + path, {
      method,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: raw ? "application/vnd.github.raw+json" : "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    const exp = res.headers.get("github-authentication-token-expiration");
    if (exp) tokenExpiry = exp;
    if (!res.ok) {
      let msg = "";
      try { msg = (await res.json()).message || ""; } catch { /* no body */ }
      const err = new Error(explain(res.status, msg));
      err.status = res.status;
      throw err;
    }
    if (res.status === 204) return null;
    return raw ? res.text() : res.json();
  }

  function explain(status, msg) {
    if (status === 401) return "المفتاح غير صحيح أو منتهي. سوّ مفتاح جديد.";
    if (status === 403 && /rate limit/i.test(msg)) return "وصلت حد الطلبات في GitHub، انتظر شوي وحاول مرة ثانية.";
    if (status === 403) return "المفتاح ما عنده الصلاحيات الكافية (Contents و Actions: Read and write).";
    if (status === 404) return "ما لقينا المستودع أو الملف. تأكد من اسم المستودع وإن المفتاح مسموح له عليه.";
    if (status === 422 && /workflow/i.test(msg)) return "ما لقينا ملف النشر publish.yml على فرع main. تأكد إنك دمجت التحديثات في main.";
    return `خطأ من GitHub (${status}) ${msg}`;
  }

  /** Upload one blob with progress (XHR, because fetch has no upload progress). */
  function uploadBlob(base64, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API}/repos/${auth.repo}/git/blobs`);
      xhr.setRequestHeader("Authorization", `Bearer ${auth.token}`);
      xhr.setRequestHeader("Accept", "application/vnd.github+json");
      xhr.setRequestHeader("X-GitHub-Api-Version", "2022-11-28");
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(e.loaded / e.total);
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText).sha);
        else {
          let m = ""; try { m = JSON.parse(xhr.responseText).message; } catch { /* ignore */ }
          reject(new Error(explain(xhr.status, m)));
        }
      };
      xhr.onerror = () => reject(new Error("انقطع الاتصال أثناء الرفع. تأكد من الإنترنت وحاول مرة ثانية."));
      xhr.send(JSON.stringify({ content: base64, encoding: "base64" }));
    });
  }

  const toBase64 = (blob) => new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] || "");
    r.onerror = () => reject(new Error("ما قدرنا نقرأ الملف من جهازك."));
    r.readAsDataURL(blob);
  });

  /** Downscale + re-encode an image so pages stay fast. */
  async function compressImage(file, maxW = 1600) {
    if (!/^image\/(png|jpeg|webp|gif)$/.test(file.type)) throw new Error(`"${file.name}" مو صورة مدعومة.`);
    if (file.size > 25 * 1024 * 1024) throw new Error(`الصورة "${file.name}" كبيرة جداً.`);
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, maxW / bmp.width);
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bmp.width * scale);
    canvas.height = Math.round(bmp.height * scale);
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = scale < 1 && bmp.width > 256; // keep pixel art crisp
    ctx.drawImage(bmp, 0, 0, canvas.width, canvas.height);
    const out = await new Promise((res) => canvas.toBlob(res, "image/webp", 0.86));
    if (!out || out.type !== "image/webp") return new Promise((res) => canvas.toBlob(res, "image/png"));
    return out;
  }

  /* ---------- Jobs UI ---------- */
  function job(title) {
    const el = document.createElement("div");
    el.className = "job";
    el.innerHTML = `<b></b><div class="bar"><span></span></div><small></small>`;
    $("b", el).textContent = title;
    $("#jobs").prepend(el);
    return {
      step(text, pct) {
        $("small", el).textContent = text;
        if (pct != null) $(".bar span", el).style.width = `${Math.max(2, Math.min(100, pct))}%`;
      },
      done(text) { el.classList.add("done"); this.step(text, 100); setTimeout(() => el.remove(), 20000); },
      fail(text, link) {
        el.classList.add("fail");
        $("small", el).textContent = text;
        if (link) {
          const a = document.createElement("a");
          a.href = link; a.target = "_blank"; a.rel = "noopener"; a.textContent = " (التفاصيل)";
          $("small", el).append(a);
        }
      },
    };
  }

  /* ---------- Publish pipeline ---------- */
  async function publish(meta, files, title) {
    const j = job(title);
    busy = true;
    try {
      const tree = [{ path: "inbox/meta.json", mode: "100644", type: "blob", content: JSON.stringify(meta, null, 2) }];
      const total = files.reduce((s, f) => s + f.blob.size, 0) || 1;
      let doneBytes = 0;
      for (const f of files) {
        j.step(`تجهيز ${f.label}...`, (doneBytes / total) * 70);
        const b64 = await toBase64(f.blob);
        const sha = await uploadBlob(b64, (p) => j.step(`رفع ${f.label}: ${Math.round(p * 100)}%`, ((doneBytes + p * f.blob.size) / total) * 70));
        doneBytes += f.blob.size;
        tree.push({ path: `inbox/${f.path}`, mode: "100644", type: "blob", sha });
      }
      j.step("حفظ في GitHub...", 72);
      const t = await gh(`/repos/${auth.repo}/git/trees`, { method: "POST", body: { tree } });
      const c = await gh(`/repos/${auth.repo}/git/commits`, { method: "POST", body: { message: `admin: ${meta.action} ${meta.id || "site"}`, tree: t.sha, parents: [] } });
      const rand = crypto.getRandomValues(new Uint32Array(1))[0].toString(36);
      const branch = `inbox/${Date.now().toString(36)}-${rand}`;
      await gh(`/repos/${auth.repo}/git/refs`, { method: "POST", body: { ref: `refs/heads/${branch}`, sha: c.sha } });

      j.step("تشغيل النشر...", 76);
      const runsUrl = `/repos/${auth.repo}/actions/workflows/${WORKFLOW}/runs?event=workflow_dispatch&per_page=20`;
      const before = new Set(((await gh(runsUrl)).workflow_runs || []).map((r) => r.id));
      await gh(`/repos/${auth.repo}/actions/workflows/${WORKFLOW}/dispatches`, { method: "POST", body: { ref: "main", inputs: { inbox: branch } } });
      const run = await waitForRun(runsUrl, before, j);
      if (run.conclusion === "success") {
        j.done("✔ تم النشر! الموقع تحدّث.");
        await loadData();
      } else {
        j.fail("✖ فشل النشر. افتح التفاصيل لتعرف السبب.", run.html_url);
      }
    } catch (e) {
      j.fail(`✖ ${e.message}`);
    } finally {
      busy = false;
    }
  }

  /** Wait for the run this dispatch started: the oldest run id we had not seen before. */
  async function waitForRun(runsUrl, before, j) {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    let run = null;
    for (let i = 0; i < 240; i++) { // up to ~20 minutes
      await sleep(i < 3 ? 3000 : 5000);
      const r = await gh(runsUrl);
      const fresh = (r.workflow_runs || []).filter((x) => !before.has(x.id)).sort((a, b) => a.id - b.id);
      if (!run) run = fresh[0] || null;
      else run = fresh.find((x) => x.id === run.id) || run;
      if (!run) { j.step("بانتظار بدء النشر...", 78); continue; }
      if (run.status === "completed") return run;
      j.step(run.status === "queued" ? "في الطابور..." : "ينشر الآن (إنشاء الإصدار وتحديث الموقع)...", run.status === "queued" ? 80 : 88);
    }
    throw new Error("النشر أخذ وقت طويل. شيّك على تبويب Actions في GitHub.");
  }

  /* ---------- Data ---------- */
  async function loadData() {
    const text = await gh(`/repos/${auth.repo}/contents/mods.json?ref=main`, { raw: true });
    data = JSON.parse(text);
    data.site ||= {};
    data.mods = Array.isArray(data.mods) ? data.mods : [];
    counts = await MC.downloadCounts(auth.repo).catch(() => ({}));
    renderList();
  }

  function renderList() {
    const total = data.mods.reduce((s, m) => s + MC.downloadsOf(m, counts), 0);
    $("#dashSummary").textContent = `${data.mods.length} عمل منشور${total ? ` · ${fmtNum(total)} تحميل` : ""}`;
    if (!data.mods.length) {
      $("#itemList").innerHTML = `<div class="panel"><p>ما فيه أعمال بعد. اضغط <b>➕ رفع عمل جديد</b> وابدأ!</p></div>`;
      return;
    }
    $("#itemList").innerHTML = data.mods.map((m) => {
      const img = safeUrl(m.image);
      const dl = MC.downloadsOf(m, counts);
      return `<div class="item" data-id="${esc(m.id)}">
        <div class="mini" data-color="${esc(safeColor(m.color))}">${img ? `<img src="${esc(img)}" alt="">` : esc(TYPES[m.type]?.icon || "📦")}</div>
        <div>
          <h3>${m.featured === true ? "⭐ " : ""}${esc(m.name)}</h3>
          <div class="sub">${esc(TYPES[m.type]?.label || m.type)} · ${esc(EDITIONS[m.edition] || "")} · ${esc((m.versions || []).join(", "))} · ${esc(m.size || "")}${dl ? ` · ⬇ ${fmtNum(dl)}` : ""}</div>
        </div>
        <div class="btns">
          <a class="mc-btn" href="./#${encodeURIComponent(m.id)}" target="_blank" rel="noopener">👁</a>
          <button class="mc-btn" data-act="edit">✏ تعديل</button>
          <button class="mc-btn mc-btn-red" data-act="delete">🗑 حذف</button>
        </div>
      </div>`;
    }).join("");
    document.querySelectorAll(".mini[data-color]").forEach((el) => { el.style.backgroundColor = el.dataset.color; });
  }

  /* ---------- Login & encrypted "remember me" ---------- */
  const enc = new TextEncoder();
  const b64 = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf)));
  const unb64 = (str) => Uint8Array.from(atob(str), (c) => c.charCodeAt(0));

  async function deriveKey(password, salt) {
    const base = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey(
      { name: "PBKDF2", salt, iterations: 600000, hash: "SHA-256" },
      base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  }

  async function lockToVault(password) {
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await deriveKey(password, salt);
    const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, enc.encode(auth.token));
    localStorage.setItem(VAULT_KEY, JSON.stringify({ v: 1, repo: auth.repo, login: auth.login, salt: b64(salt), iv: b64(iv), ct: b64(ct) }));
  }

  async function unlockVault(password) {
    const vault = readVault();
    if (!vault) throw new Error("ما فيه مفتاح محفوظ.");
    try {
      const key = await deriveKey(password, unb64(vault.salt));
      const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv: unb64(vault.iv) }, key, unb64(vault.ct));
      return { token: new TextDecoder().decode(pt), repo: vault.repo, login: vault.login };
    } catch {
      throw new Error("كلمة السر غلط.");
    }
  }

  function readVault() {
    try { const v = JSON.parse(localStorage.getItem(VAULT_KEY) || "null"); return v?.v === 1 ? v : null; }
    catch { return null; }
  }
  function readSession() {
    try { return JSON.parse(sessionStorage.getItem(STORE_KEY) || "null"); } catch { return null; }
  }
  function saveSession() {
    try { sessionStorage.setItem(STORE_KEY, JSON.stringify(auth)); } catch { /* page-only login */ }
  }

  async function login(token, repo) {
    if (!/^[\w-][\w.-]*\/[\w-][\w.-]*$/.test(repo)) throw new Error("اكتب المستودع بالشكل: اسم-الحساب/اسم-المستودع");
    if (/^ghp_/.test(token)) throw new Error("هذا مفتاح Classic وصلاحياته على كل حسابك. استخدم Fine-grained (يبدأ بـ github_pat_) ومحدد على هذا المستودع بس.");
    if (!/^github_pat_[A-Za-z0-9_]{20,}$/.test(token)) throw new Error("هذا ما يشبه مفتاح GitHub. لازم يبدأ بـ github_pat_");
    const info = await gh(`/repos/${repo}`, { token });
    if (!info.permissions?.push) throw new Error("هذا المفتاح ما عنده صلاحية كتابة على المستودع.");
    let me = "";
    try { me = (await gh("/user", { token })).login; } catch { /* fine-grained tokens may not read /user */ }
    auth = { token, repo: info.full_name, login: me };
    saveSession();
  }

  function show(view, err = "") {
    ["loginView", "unlockView", "dashView"].forEach((v) => { $(`#${v}`).hidden = v !== view; });
    $("#logoutBtn").hidden = view !== "dashView";
    if (view === "loginView") $("#loginError").textContent = err;
    if (view === "unlockView") { $("#unlockError").textContent = err; $("#unlockInput").value = ""; $("#unlockInput").focus(); }
  }
  const showLogin = (err) => show(readVault() ? "unlockView" : "loginView", err);

  async function showDash() {
    show("dashView");
    $("#whoami").textContent = auth.login || "";
    $("#tokenInput").value = "";
    $("#passInput").value = "";
    try {
      await loadData();
      warnExpiry();
    } catch (e) {
      if (e.status === 401) { logout(); showLogin(e.message); return; }
      $("#itemList").innerHTML = `<p class="error">${esc(e.message)}</p>`;
    }
  }

  /**
   * Link that opens GitHub's "new fine-grained token" form already filled in
   * (name, owner, 90-day expiry, Contents + Actions write). The owner only has to
   * pick the repository and press Generate.
   */
  function tokenUrl(repo) {
    const owner = /^[\w-][\w.-]*\/[\w-][\w.-]*$/.test(repo || "") ? repo.split("/")[0] : "";
    const q = new URLSearchParams({
      name: `NABD admin ${new Date().toISOString().slice(0, 10)}`,
      description: "لوحة تحكم موقع نبض: رفع وتعديل المودات",
      expires_in: "90",
      contents: "write",
      actions: "write",
    });
    if (owner) q.set("target_name", owner);
    return `https://github.com/settings/personal-access-tokens/new?${q}`;
  }
  function updateTokenLink() {
    const repo = $("#repoInput").value.trim();
    $("#makeTokenBtn").href = tokenUrl(repo);
    $("#repoNameHint").textContent = repo.split("/")[1] || "مستودع الموقع";
  }

  /** Pull a token out of whatever was pasted (extra spaces, new lines, labels...). */
  const extractToken = (text) => (String(text).match(/github_pat_[A-Za-z0-9_]{20,}/) || [""])[0];
  function checkToken() {
    const raw = $("#tokenInput").value;
    const tok = extractToken(raw);
    if (tok && tok !== raw) $("#tokenInput").value = tok;
    const hint = $("#tokenHint");
    hint.classList.toggle("ok", !!tok);
    hint.textContent = tok ? "✔ المفتاح شكله صحيح" : raw.trim() ? (/^ghp_/.test(raw.trim()) ? "✖ هذا مفتاح Classic. سوّ مفتاح جديد من الزر الأخضر فوق." : "✖ هذا ما يشبه المفتاح. لازم يبدأ بـ github_pat_") : "";
  }

  function warnExpiry() {
    const t = tokenExpiry ? Date.parse(tokenExpiry.replace(" UTC", "Z").replace(" ", "T")) : NaN;
    const days = Math.floor((t - Date.now()) / 864e5);
    const el = $("#tokenWarn");
    el.hidden = !(days <= 10);
    if (!el.hidden) {
      el.textContent = `⚠️ مفتاح GitHub ينتهي بعد ${Math.max(0, days)} يوم. `;
      const a = document.createElement("a");
      a.href = tokenUrl(auth?.repo);
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = "سوّ مفتاح جديد الحين";
      el.append(a);
    }
  }

  /** Ends the session. The encrypted vault stays unless forget = true. */
  function logout(forget = false) {
    auth = null;
    try {
      sessionStorage.removeItem(STORE_KEY);
      localStorage.removeItem("mc.admin"); // old unencrypted format from earlier versions
      if (forget) localStorage.removeItem(VAULT_KEY);
    } catch { /* ignore */ }
  }

  $("#loginBtn").addEventListener("click", async () => {
    const btn = $("#loginBtn");
    btn.disabled = true;
    $("#loginError").textContent = "";
    try {
      const remember = $("#rememberInput").checked;
      const pass = $("#passInput").value;
      if (remember && pass.length < 8) throw new Error("اكتب كلمة سر 8 أحرف أو أكثر لقفل المفتاح.");
      await login(extractToken($("#tokenInput").value) || $("#tokenInput").value.trim(), $("#repoInput").value.trim());
      if (remember) await lockToVault(pass); else localStorage.removeItem(VAULT_KEY);
      await showDash();
    } catch (e) {
      $("#loginError").textContent = e.message;
    } finally { btn.disabled = false; }
  });
  $("#tokenInput").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#loginBtn").click(); });
  $("#tokenInput").addEventListener("input", checkToken);
  $("#repoInput").addEventListener("input", updateTokenLink);
  $("#pasteBtn").addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      $("#tokenInput").value = extractToken(text) || text.trim();
      checkToken();
    } catch {
      $("#tokenInput").focus();
      $("#tokenHint").classList.remove("ok");
      $("#tokenHint").textContent = "اضغط مطولاً على الخانة واختر «لصق».";
    }
  });
  $("#showBtn").addEventListener("click", () => {
    const i = $("#tokenInput");
    i.type = i.type === "password" ? "text" : "password";
  });
  $("#rememberInput").addEventListener("change", (e) => { $("#passWrap").hidden = !e.target.checked; });
  $("#logoutBtn").addEventListener("click", () => { logout(); showLogin(); });
  $("#unlockBtn").addEventListener("click", async () => {
    const btn = $("#unlockBtn");
    btn.disabled = true;
    try {
      const a = await unlockVault($("#unlockInput").value);
      await gh(`/repos/${a.repo}`, { token: a.token }); // still valid?
      auth = a;
      saveSession();
      await showDash();
    } catch (e) {
      if (e.status === 401) { logout(true); show("loginView", "المفتاح المحفوظ انتهى أو انحذف. ادخل بمفتاح جديد."); }
      else $("#unlockError").textContent = e.message;
    } finally { btn.disabled = false; }
  });
  $("#unlockInput").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#unlockBtn").click(); });
  $("#forgetBtn").addEventListener("click", () => {
    if (confirm("راح ينحذف المفتاح المحفوظ من هذا الجهاز. متأكد؟")) { logout(true); show("loginView"); }
  });

  // Auto-lock when idle.
  let lastActive = Date.now();
  ["pointerdown", "keydown", "scroll"].forEach((ev) => addEventListener(ev, () => { lastActive = Date.now(); }, { passive: true }));
  setInterval(() => {
    if (auth && !busy && Date.now() - lastActive > IDLE_MS) {
      logout();
      document.querySelectorAll("dialog[open]").forEach((d) => d.close());
      showLogin("انقفلت اللوحة لأنك ما استخدمتها 30 دقيقة.");
    }
  }, 30000);
  $("#reloadBtn").addEventListener("click", () => loadData().catch((e) => alert(e.message)));

  /* ---------- Editor ---------- */
  const form = $("#itemForm");
  const editor = $("#editor");
  form.type.innerHTML = Object.entries(TYPES).map(([k, t]) => `<option value="${k}">${t.icon} ${t.label}</option>`).join("");

  const slugify = (s) => String(s).toLowerCase().normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50);

  form.name.addEventListener("input", () => {
    if (!editing && !form.id.dataset.touched) form.id.value = slugify(form.name.value);
  });
  form.id.addEventListener("input", () => { form.id.dataset.touched = "1"; });
  form.addEventListener("change", (e) => {
    if (e.target.name === "source") {
      form.querySelectorAll("[data-source]").forEach((el) => { el.hidden = el.dataset.source !== form.source.value; });
    }
    if (e.target.name === "file") {
      const f = form.file.files[0];
      $("#fileHint").textContent = f ? `${f.name} — ${(f.size / 1048576).toFixed(1)} MB${f.size > MAX_FILE ? " ⚠️ أكبر من 95MB، استخدم رابط خارجي" : ""}` : "";
      if (f && !form.edition.dataset.touched && /\.(mcaddon|mcpack|mcworld|mctemplate)$/i.test(f.name)) form.edition.value = "bedrock";
    }
    if (e.target.name === "edition") form.edition.dataset.touched = "1";
    if (e.target.name === "cover" || e.target.name === "screenshots") {
      const imgs = [...form.cover.files, ...form.screenshots.files].slice(0, 7);
      $("#previews").querySelectorAll("img").forEach((i) => URL.revokeObjectURL(i.src));
      $("#previews").replaceChildren(...imgs.map((f) => Object.assign(document.createElement("img"), { src: URL.createObjectURL(f), alt: "" })));
    }
  });

  function updateLatestBtn() {
    $("#addLatestBtn").textContent = `➕ آخر إصدار (${MC.LATEST[form.edition.value] || ""})`;
  }
  $("#addLatestBtn").addEventListener("click", () => {
    const v = MC.LATEST[form.edition.value];
    const list = splitList(form.versions.value);
    if (v && !list.includes(v)) form.versions.value = [v, ...list].join(", ");
  });
  form.edition.addEventListener("change", updateLatestBtn);

  function openEditor(m) {
    editing = m ? m.id : null;
    form.reset();
    delete form.id.dataset.touched;
    delete form.edition.dataset.touched;
    $("#previews").replaceChildren();
    $("#fileHint").textContent = "";
    $("#formError").textContent = "";
    $("#editorTitle").textContent = m ? `تعديل: ${m.name}` : "رفع عمل جديد";
    form.id.readOnly = !!m;
    form.querySelectorAll("[data-source]").forEach((el) => { el.hidden = el.dataset.source !== "upload"; });
    if (m) {
      Object.assign(form.name, { value: m.name || "" });
      form.id.value = m.id;
      form.type.value = m.type in TYPES ? m.type : "mod";
      form.edition.value = m.edition in EDITIONS ? m.edition : "java";
      form.loader.value = m.loader || "";
      form.versions.value = (m.versions || []).join(", ");
      form.version.value = m.version || "";
      form.description.value = m.description || "";
      form.details.value = m.details || "";
      form.tags.value = (m.tags || []).join("، ");
      form.video.value = m.video ? `https://youtu.be/${m.video}` : "";
      form.color.value = safeColor(m.color);
      form.featured.checked = m.featured === true;
      if (m.external) {
        form.source.value = "link";
        form.querySelectorAll("[data-source]").forEach((el) => { el.hidden = el.dataset.source !== "link"; });
        form.externalUrl.value = m.file || "";
        form.externalSize.value = m.size || "";
      }
      $("#fileHint").textContent = m.file ? "اترك الملف فاضي إذا ما تبي تغيّره." : "";
    }
    updateLatestBtn();
    editor.showModal();
    form.name.focus();
  }

  const splitList = (s) => [...new Set(String(s).split(/[,،\n]/).map((x) => x.trim()).filter(Boolean))];

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const err = (msg) => { $("#formError").textContent = msg; };
    if (busy) return err("فيه عملية نشر شغّالة، انتظرها تخلص.");

    const id = form.id.value.trim();
    const versions = splitList(form.versions.value);
    if (!form.name.value.trim()) return err("اكتب اسم العمل.");
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(id) || id.length > 50) return err("المعرّف لازم يكون حروف إنجليزية صغيرة وأرقام وشرطات فقط، مثل: dragon-addon");
    if (!editing && data.mods.some((m) => m.id === id)) return err("فيه عمل بنفس المعرّف، غيّره.");
    if (!versions.length) return err("اكتب إصدار ماين كرافت واحد على الأقل.");
    if (!form.description.value.trim()) return err("اكتب وصف قصير.");
    const video = form.video.value.trim();
    if (video && !parseYouTube(video)) return err("رابط اليوتيوب غير صحيح.");

    const useLink = form.source.value === "link";
    const file = form.file.files[0];
    const external = form.externalUrl.value.trim();
    if (useLink && !/^https:\/\/[^\s"'<>\\`]+$/i.test(external)) return err("الرابط الخارجي لازم يبدأ بـ https://");
    if (!useLink && !file && !(editing && !data.mods.find((m) => m.id === editing)?.external)) return err("اختر الملف اللي تبي ترفعه.");
    if (!useLink && file && file.size > MAX_FILE) return err("الملف أكبر من 95MB. ارفعه على Releases أو MediaFire واستخدم «رابط خارجي».");
    if (form.screenshots.files.length > 6) return err("أقصى شي 6 صور إضافية.");

    const files = [];
    try {
      if (!useLink && file) files.push({ path: `files/${file.name.slice(-120)}`, blob: file, label: file.name });
      if (form.cover.files[0]) files.push({ path: "images/cover.webp", blob: await compressImage(form.cover.files[0]), label: "الغلاف" });
      let i = 0;
      for (const s of form.screenshots.files) files.push({ path: `images/shot-${++i}.webp`, blob: await compressImage(s, 1920), label: `صورة ${i}` });
    } catch (ex) { return err(ex.message); }

    const meta = {
      action: "upsert",
      id,
      isNew: !editing,
      entry: {
        name: form.name.value.trim(),
        type: form.type.value,
        edition: form.edition.value,
        loader: form.loader.value.trim(),
        versions,
        version: form.version.value.trim(),
        description: form.description.value.trim(),
        details: form.details.value.trim(),
        tags: splitList(form.tags.value),
        video: parseYouTube(video),
        color: form.color.value,
        featured: form.featured.checked,
      },
      changelogNote: form.changelogNote.value.trim(),
      external: useLink ? { url: external, size: form.externalSize.value.trim() } : null,
      fileName: !useLink && file ? file.name.slice(-120) : null,
      cover: !!form.cover.files[0],
      screenshots: form.screenshots.files.length,
    };
    editor.close();
    publish(meta, files, `${editing ? "تحديث" : "نشر"}: ${meta.entry.name}`);
  });

  $("#newBtn").addEventListener("click", () => openEditor(null));
  $("#itemList").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const m = data.mods.find((x) => x.id === btn.closest(".item").dataset.id);
    if (!m) return;
    if (btn.dataset.act === "edit") openEditor(m);
    if (btn.dataset.act === "delete") {
      if (busy) return alert("فيه عملية نشر شغّالة، انتظرها تخلص.");
      const typed = prompt(`راح ينحذف "${m.name}" مع ملفاته وصوره نهائياً.\nللتأكيد اكتب المعرّف: ${m.id}`);
      if (typed === m.id) publish({ action: "delete", id: m.id }, [], `حذف: ${m.name}`);
    }
  });

  /* ---------- Settings ---------- */
  const sForm = $("#settingsForm");
  const SITE_FIELDS = ["name", "author", "tagline", "about", "donate", "youtube", "discord", "tiktok", "instagram", "website", "googleVerify"];
  $("#settingsBtn").addEventListener("click", () => {
    SITE_FIELDS.forEach((k) => { sForm[k].value = data.site[k] || ""; });
    $("#settingsError").textContent = "";
    $("#settings").showModal();
  });
  sForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (busy) { $("#settingsError").textContent = "فيه عملية نشر شغّالة، انتظرها تخلص."; return; }
    const site = {};
    for (const k of SITE_FIELDS) {
      const v = sForm[k].value.trim();
      const social = MC.SOCIALS.find((p) => p.key === k);
      if (social && v && !MC.socialUrl(k, v)) {
        $("#settingsError").textContent = `رابط ${social.label} لازم يكون من ${social.hosts.join(" أو ")} ويبدأ بـ https://`;
        return;
      }
      if (["donate", "website"].includes(k) && v && !/^https:\/\/[^\s"'<>\\`]+$/i.test(v)) {
        $("#settingsError").textContent = "الروابط لازم تبدأ بـ https://";
        return;
      }
      if (k === "googleVerify" && v && !/^[A-Za-z0-9_-]{10,100}$/.test(v)) {
        $("#settingsError").textContent = "كود Google: الصق الكود بس (اللي بين علامات content=\"...\")، مو السطر كامل.";
        return;
      }
      site[k] = v;
    }
    $("#settings").close();
    publish({ action: "settings", site }, [], "تحديث إعدادات الموقع");
  });

  document.querySelectorAll("dialog").forEach((d) => {
    d.addEventListener("click", (e) => { if (e.target === d || e.target.closest("[data-close]")) d.close(); });
  });
  window.addEventListener("beforeunload", (e) => { if (busy) { e.preventDefault(); e.returnValue = ""; } });

  /* ---------- Start ---------- */
  (async () => {
    let site = {};
    try { site = (await (await fetch("mods.json", { cache: "no-cache" })).json()).site || {}; } catch { /* ignore */ }
    $("#repoInput").value = MC.repoOf(site);
    updateTokenLink();
    try { localStorage.removeItem("mc.admin"); } catch { /* drop old unencrypted format */ }
    const saved = readSession();
    if (saved?.token && saved?.repo) { auth = saved; await showDash(); }
    else showLogin();
  })();
})();
