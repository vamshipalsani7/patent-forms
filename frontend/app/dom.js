/*
 * Tiny shared DOM helper for the application-shell modules (sidebar, main
 * area, app wiring) ONLY. The renderer (frontend/renderer/form-renderer.js)
 * deliberately does not depend on this file — it stays a fully self-contained
 * component with zero coupling to the host application's utilities.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // "1 document" / "2 documents" — the app talks to patent professionals, not
  // to a parser, so counts read as English rather than "1 document(s)".
  function plural(n, singular, pluralForm) {
    var word = n === 1 ? singular : (pluralForm || singular + "s");
    return n + " " + word;
  }

  ns.dom = { el: el, plural: plural };
})(window.PatentFormsApp);
