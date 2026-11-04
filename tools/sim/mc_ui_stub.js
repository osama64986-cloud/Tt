// بدائل بسيطة لـ @minecraft/server-ui: النماذج ترجع دائماً أول زر (أو الزر المحدد من السيناريو)
// queue: اختيارات متتالية لعدة شاشات (قائمة ← قائمة فرعية ← تفاصيل)، وcancelWhenEmpty: لما تخلص القائمة النموذج يتسكر (حتى ما تدور الشاشات للأبد)
export const sim = { nextSelection: 0, formsShown: [], queue: [], cancelWhenEmpty: false };
let chain = 0, chainTimer = null;
export class ActionFormData {
  constructor() { this.buttons = []; this.icons = []; this._title = ""; this._body = ""; }
  title(t) { this._title = t; return this; }
  body(b) { this._body = b; return this; }
  button(t, icon) { this.buttons.push(t); this.icons.push(icon); return this; }
  async show() {
    sim.formsShown.push({ title: this._title, body: this._body, buttons: this.buttons, icons: this.icons });
    if (globalThis.__allText) for (const t of [this._title, this._body, ...this.buttons]) if (typeof t === "string") for (const ln of t.split("\n")) if (ln.trim()) globalThis.__allText.add(ln);
    // أمان: شاشات ترجع لبعضها (رجوع ← قائمة) بدون توقف ما تدور للأبد بالمحاكي (العداد يتصفر أول ما يرتاح الكود)
    chain++; if (!chainTimer) chainTimer = setTimeout(() => { chain = 0; chainTimer = null; }, 0);
    if (chain > 300) return { canceled: true, cancelationReason: "UserClosed" };
    if (sim.queue.length) return { canceled: false, selection: Math.min(sim.queue.shift(), this.buttons.length - 1) };
    if (sim.cancelWhenEmpty) return { canceled: true, cancelationReason: "UserClosed" };
    return { canceled: false, selection: Math.min(sim.nextSelection, this.buttons.length - 1) };
  }
}
export class MessageFormData extends ActionFormData {}
export class ModalFormData extends ActionFormData {}
