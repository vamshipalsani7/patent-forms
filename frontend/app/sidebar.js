/*
 * Forms panel: a "Patent Workspace" home button, a search box, and a scrollable
 * list of the actions a user can take (each backed by an IPO form). Pure UI —
 * knows nothing about form definitions, the renderer, or the workspace data. It
 * reads the static catalog and emits onSelect(formId) / onHome().
 *
 * Action-first presentation: each item leads with what filing the form
 * accomplishes ("Request Expedited Examination"), with the form number shown as
 * secondary confirmation ("Form 18A"). This is the professional's mental model —
 * they know the action they need, not always the form number.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";
  var el = ns.dom.el;

  function mountSidebar(container, catalog, opts) {
    var onSelect = (opts && opts.onSelect) || function () {};
    var onHome = (opts && opts.onHome) || null;
    var active = null;

    container.innerHTML = "";

    if (onHome) {
      var home = el("button", "workspace-nav", "");
      home.type = "button";
      home.appendChild(el("span", "workspace-nav-icon", "🏠"));
      home.appendChild(el("span", "workspace-nav-label", "Patent Workspace"));
      home.addEventListener("click", function () {
        active = null;
        renderList();
        onHome();
      });
      container.appendChild(home);
    }

    container.appendChild(el("div", "panel-heading", "Prepare a Form"));

    var searchWrap = el("div", "sidebar-search");
    var searchInput = el("input", "sidebar-search-input");
    searchInput.type = "search";
    searchInput.setAttribute("aria-label", "Search actions or forms");
    searchInput.placeholder = "Search actions or form numbers…";
    searchWrap.appendChild(searchInput);
    container.appendChild(searchWrap);

    var listEl = el("div", "form-list");
    container.appendChild(listEl);

    function matches(f, q) {
      if (!q) return true;
      return (f.action || "").toLowerCase().indexOf(q) >= 0 ||
             f.formNumber.toLowerCase().indexOf(q) >= 0 ||
             f.officialName.toLowerCase().indexOf(q) >= 0;
    }

    function renderList() {
      var q = searchInput.value.trim().toLowerCase();
      listEl.innerHTML = "";
      var items = catalog.filter(function (f) { return matches(f, q); });
      if (!items.length) {
        listEl.appendChild(el("div", "form-list-empty", "No actions match “" + searchInput.value + "”."));
        return;
      }
      items.forEach(function (f) {
        var item = el("button", "form-item" + (f.formId === active ? " active" : ""));
        item.type = "button";
        // Action first, form number second — the UX rule for this panel.
        item.appendChild(el("div", "form-item-action", f.action || f.officialName));
        item.appendChild(el("div", "form-item-number", "Form " + f.formNumber));
        item.title = f.officialName;
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
