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

  ns.dom = { el: el };
})(window.PatentFormsApp);
