/* Shared helpers for the public site and the admin panel. */
window.MC = (() => {
  const TYPES = {
    mod:     { label: "مود",          plural: "مودات",        icon: "⚒" },
    addon:   { label: "إضافة بيدروك", plural: "إضافات بيدروك", icon: "🧩" },
    texture: { label: "تكستر",        plural: "تكسترات",      icon: "🎨" },
    shader:  { label: "شيدر",         plural: "شيدرات",       icon: "✨" },
    map:     { label: "خريطة",        plural: "خرائط",        icon: "🗺" },
    world:   { label: "عالم",         plural: "عوالم",        icon: "🌍" },
  };
  const EDITIONS = { java: "Java", bedrock: "Bedrock" };

  const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;", "`": "&#96;" };
  const esc = (v) => String(v ?? "").replace(/[&<>"'`]/g, (c) => ESC[c]);

  /** Only https:// links or plain relative paths (no scheme, no "..", no "//"). */
  function safeUrl(u) {
    u = String(u ?? "").trim();
    if (/^https:\/\/[^\s"'<>\\`]+$/i.test(u)) return u;
    if (/^[\w\-./%]+$/.test(u) && !u.startsWith("//") && !u.includes("..")) return u;
    return "";
  }
  const safeColor = (c) => (/^#[0-9a-f]{6}$/i.test(c || "") ? c : "#5d5d5d");
  const ytId = (v) => (/^[\w-]{11}$/.test(v || "") ? v : "");

  /** Pull an 11-char video id out of any common YouTube URL form. */
  function parseYouTube(input) {
    const s = String(input || "").trim();
    if (ytId(s)) return s;
    const m = s.match(/^https:\/\/(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?(?:.*&)?v=|shorts\/|embed\/|live\/)|youtu\.be\/)([\w-]{11})/i);
    return m ? m[1] : "";
  }

  const fmtNum = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? (n / 1e3).toFixed(1) + "K" : String(n || 0));

  function isRecent(date, days = 14) {
    const t = Date.parse(date);
    return !Number.isNaN(t) && Date.now() - t < days * 864e5;
  }

  /** owner/repo from mods.json, or guessed from a *.github.io address. */
  function repoOf(site) {
    if (/^[\w.-]+\/[\w.-]+$/.test(site?.repo || "")) return site.repo;
    const m = location.hostname.match(/^([\w-]+)\.github\.io$/i);
    const seg = location.pathname.split("/").filter(Boolean)[0];
    return m && seg ? `${m[1]}/${seg}` : "";
  }

  /** { tag: totalDownloads } for every release, cached for 10 minutes. */
  async function downloadCounts(repo) {
    const key = `mc.dl.${repo}`;
    try {
      const c = JSON.parse(sessionStorage.getItem(key) || "null");
      if (c && Date.now() - c.t < 6e5) return c.v;
    } catch { /* storage unavailable */ }
    const out = {};
    try {
      for (let page = 1; page <= 5; page++) {
        const r = await fetch(`https://api.github.com/repos/${repo}/releases?per_page=100&page=${page}`, {
          headers: { Accept: "application/vnd.github+json" },
        });
        if (!r.ok) break;
        const list = await r.json();
        list.forEach((rel) => {
          out[rel.tag_name] = (rel.assets || []).reduce((s, a) => s + (a.download_count || 0), 0);
        });
        if (list.length < 100) break;
      }
      try { sessionStorage.setItem(key, JSON.stringify({ t: Date.now(), v: out })); } catch { /* ignore */ }
    } catch { /* offline or rate limited: just show no counts */ }
    return out;
  }

  /**
   * Plain-language install steps for an item, per device.
   * Returns [{ label, steps: [html-safe strings] }]. Steps may contain <b>/<code> (static text only).
   */
  function guideFor(m) {
    const bedrock = m.edition === "bedrock";
    const loader = esc(m.loader || "Fabric");
    const PHONE = "📱 جوال", PC = "💻 كمبيوتر";
    const openFile = (where) => [
      `${where === "pc" ? "دبل كليك على الملف" : "اضغط على الملف من الإشعار أو من مجلد <b>التنزيلات</b>"} بعد ما يخلص التحميل.`,
      where === "pc" ? "ماين كرافت ينفتح لحاله ويقول <b>Import Started</b> ثم <b>Successfully imported</b> ✔" : "إذا سألك بأي تطبيق تفتحه، اختر <b>Minecraft</b>. اللعبة تنفتح وتقول <b>Successfully imported</b> ✔",
    ];
    switch (m.type) {
      case "addon":
      case "mod":
        if (bedrock) {
          const after = [
            "سوّ عالم جديد (أو اضغط ✏ على عالمك) ← <b>Behavior Packs</b> ← اضغط على الإضافة ← <b>Activate</b>.",
            "نفس الشي في <b>Resource Packs</b> إذا موجودة.",
            "إذا ما اشتغلت: من إعدادات العالم ← <b>Experiments</b> ← فعّل كل الخيارات.",
          ];
          return [{ label: PHONE, steps: [...openFile("phone"), ...after] }, { label: PC, steps: [...openFile("pc"), ...after] }];
        }
        return [{ label: PC, steps: [
          `ثبّت <b>${loader}</b> لنفس إصدار ماين كرافت (من موقعهم الرسمي).`,
          "اضغط <code>Win + R</code> واكتب <code>%appdata%\\.minecraft</code> واضغط Enter.",
          "افتح مجلد <b>mods</b> (إذا ما موجود سوّه بنفسك) وحط الملف داخله. <b>لا تفك الضغط.</b>",
          `شغّل اللانشر واختر بروفايل <b>${loader}</b> واضغط Play ✔`,
        ] }];
      case "texture":
      case "shader":
        if (bedrock) {
          const after = ["ادخل <b>Settings</b> ← <b>Global Resources</b> ← <b>My Packs</b>.", "اضغط على الحزمة ← <b>Activate</b> ✔"];
          return [{ label: PHONE, steps: [...openFile("phone"), ...after] }, { label: PC, steps: [...openFile("pc"), ...after] }];
        }
        if (m.type === "shader") {
          return [{ label: PC, steps: [
            "ثبّت <b>Iris</b> (أسهل طريقة للشيدرات) من موقعه الرسمي.",
            "داخل اللعبة: <b>Options</b> ← <b>Video Settings</b> ← <b>Shader Packs</b> ← <b>Open Shader Pack Folder</b>.",
            "حط الملف هناك <b>بدون ما تفك الضغط</b>.",
            "ارجع للعبة واختر الشيدر واضغط <b>Done</b> ✔",
          ] }];
        }
        return [{ label: PC, steps: [
          "داخل اللعبة: <b>Options</b> ← <b>Resource Packs</b> ← <b>Open Pack Folder</b>.",
          "حط الملف هناك <b>بدون ما تفك الضغط</b>.",
          "ارجع للعبة، الحزمة تطلع باليسار، اضغط السهم عليها ← <b>Done</b> ✔",
        ] }];
      default: // map / world
        if (bedrock) {
          const after = ["العالم يطلع في قائمة <b>Play</b> ← <b>Worlds</b> ✔"];
          return [{ label: PHONE, steps: [...openFile("phone"), ...after] }, { label: PC, steps: [...openFile("pc"), ...after] }];
        }
        return [{ label: PC, steps: [
          "فك ضغط الملف (كليك يمين ← <b>Extract All</b>).",
          "اضغط <code>Win + R</code> واكتب <code>%appdata%\\.minecraft\\saves</code> واضغط Enter.",
          "انقل مجلد العالم هناك.",
          "شغّل اللعبة ← <b>Singleplayer</b> وتلقاه بالقائمة ✔",
        ] }];
    }
  }

  const downloadsOf = (m, counts) => (m.releases || []).reduce((s, t) => s + (counts[t] || 0), 0);

  return { guideFor, TYPES, EDITIONS, esc, safeUrl, safeColor, ytId, parseYouTube, fmtNum, isRecent, repoOf, downloadCounts, downloadsOf };
})();
