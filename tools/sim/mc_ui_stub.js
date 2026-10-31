// بدائل بسيطة لـ @minecraft/server-ui: النماذج ترجع دائماً أول زر (أو الزر المحدد من السيناريو)
export const sim = { nextSelection: 0, formsShown: [] };
export class ActionFormData {
  constructor() { this.buttons = []; this._title = ""; this._body = ""; }
  title(t) { this._title = t; return this; }
  body(b) { this._body = b; return this; }
  button(t) { this.buttons.push(t); return this; }
  async show() {
    sim.formsShown.push({ title: this._title, body: this._body, buttons: this.buttons });
    return { canceled: false, selection: Math.min(sim.nextSelection, this.buttons.length - 1) };
  }
}
export class MessageFormData extends ActionFormData {}
export class ModalFormData extends ActionFormData {}
