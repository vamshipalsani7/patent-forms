/*
 * Forms panel: search box + scrollable list of IPO forms. Pure UI — knows
 * nothing about form definitions, the renderer, draft persistence, or the
 * Document Workspace. It only reads the static catalog and emits
 * onSelect(formId).
 *
 * The app-level brand ("Patent Forms") now lives in the shared app-bar in
 * index.html, since the recommended Sprint 1 layout puts it above both the
 * Documents and Forms sections rather than owned by this panel alone. This
 * is the only change in this file — the search/list/selection logic below
 * is unmodified.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;

  function mountSidebar(container, catalog, opts) {
    var onSelect = (opts && opts.onSelect) || function () {};
    var active = null;

    container.innerHTML = "";

    container.appendChild(el("div", "panel-heading", "Search Forms"));

    var searchWrap = el("div", "sidebar-search");
    var searchInput = el("input", "sidebar-search-input");
    searchInput.type = "search";
    searchInput.setAttribute("aria-label", "Search forms by number or name");
    searchInput.placeholder = "Search forms by number or name…";
    searchWrap.appendChild(searchInput);
    container.appendChild(searchWrap);

    var listEl = el("div", "form-list");
    container.appendChild(listEl);

    function renderList() {
      var q = searchInput.value.trim().toLowerCase();
      listEl.innerHTML = "";
      var items = catalog.filter(function (f) {
        if (!q) return true;
        return f.formNumber.toLowerCase().indexOf(q) >= 0 ||
               f.officialName.toLowerCase().indexOf(q) >= 0;
      });
      if (!items.length) {
        listEl.appendChild(el("div", "form-list-empty", "No forms match “" + searchInput.value + "”."));
        return;
      }
      items.forEach(function (f) {
        var item = el("button", "form-item" + (f.formId === active ? " active" : ""));
        item.type = "button";
        item.appendChild(el("div", "form-item-number", "Form " + f.formNumber));
        item.appendChild(el("div", "form-item-name", f.officialName));
        item.addEventListener("click", function () {
          active = f.formId;
          renderList();
          onSelect(f.formId);
        });
        listEl.appendChild(item);
      });
    }

    searchInput.addEventListener("input", renderList);
    renderList();

    return {
      setActive: function (formId) { active = formId; renderList(); }
    };
  }

  ns.sidebar = { mount: mountSidebar };
})(window.PatentFormsApp);
