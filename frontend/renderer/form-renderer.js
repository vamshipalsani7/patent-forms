/*
 * Generic, definition-driven form renderer.
 *
 * Renders an editable form from a Form Definition JSON that validates against
 * docs/specifications/schema/form-definition.schema.json. It contains NO
 * form-specific content: everything it draws comes from the definition object
 * it is given. It never fetches a definition itself and never knows which
 * form (formId/formNumber) it is rendering.
 *
 * Public API (attached to window.FormRenderer):
 *
 *   FormRenderer.mount(container, definition, initialValues, callbacks) -> controller
 *
 *     container      DOM element to render into (cleared first).
 *     definition     A Form Definition object (already parsed JSON).
 *     initialValues  Plain object of previously saved field values, or null/{}.
 *     callbacks      Optional: {
 *                       onChange(values)        // fired after every user edit
 *                       onGapsChange(gaps, findings) // fired after every render;
 *                                                     // seam for a future Validation feature
 *                     }
 *
 *   controller = {
 *     getValues()        -> plain-object snapshot of current field values
 *     setValues(values)  -> replace all values and re-render (e.g. "restore draft")
 *     getGaps()          -> missing-information gaps found while rendering
 *     getFindings()       -> non-blocking fidelity notes found while rendering
 *     unmount()          -> remove the rendered DOM from `container`
 *   }
 *
 * Only one form is ever mounted at a time by this application, so internal
 * state is a module-level singleton that `mount()` fully resets on every call
 * (definition, values, callbacks, computed condition triggers). This is the
 * smallest change that lets the host application own the form's editor state
 * (per the "do not let the renderer own the application" requirement) without
 * restructuring the rendering logic itself, which is unchanged from the
 * approved proof-of-architecture version.
 *
 * Design rule carried over from the proof phase: if the renderer needs
 * information the definition does not supply, it records the gap in `gaps[]`
 * instead of inventing it.
 */
(function () {
  "use strict";

  var DEF = null;
  var callbacks = {};
  var state = {}; // path -> value (string | array<string> | array<rowObject> | dataURL)
  var gaps = []; // blocking: information the renderer required but the definition lacked
  var findings = []; // informational: fidelity notes that did not block rendering
  var triggerPaths = new Set(); // field paths referenced by any condition (drive re-render)

  var appEl = null; // container for the rendered form (element with class "app")
  var completenessEl = null; // container for the completeness/gaps panel

  // ------------------------------------------------------------------ helpers
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function getVal(path) { return state[path]; }
  function snapshot() { return JSON.parse(JSON.stringify(state)); }
  function notify() {
    if (callbacks && typeof callbacks.onChange === "function") callbacks.onChange(snapshot());
  }
  function setVal(path, v) { state[path] = v; notify(); }

  function isFilledVal(v) {
    if (v == null) return false;
    if (Array.isArray(v)) {
      return v.some(function (x) {
        if (x && typeof x === "object") return Object.keys(x).some(function (k) { return String(x[k] || "").trim() !== ""; });
        return String(x || "").trim() !== "";
      });
    }
    return String(v).trim() !== "";
  }
  function scalar(v) { return Array.isArray(v) ? "" : (v == null ? "" : String(v)); }
  function minCount(rep) { return rep && typeof rep.min === "number" ? rep.min : 0; }

  // ------------------------------------------------------------- conditions
  function evalCond(c) {
    if (!c) return true;
    if (c.allOf) return c.allOf.every(evalCond);
    if (c.anyOf) return c.anyOf.some(evalCond);
    if (c.not) return !evalCond(c.not);
    var v = getVal(c.field);
    switch (c.op) {
      case "isFilled": return isFilledVal(v);
      case "isEmpty": return !isFilledVal(v);
      case "equals": return scalar(v) === c.value;
      case "notEquals": return scalar(v) !== c.value;
      case "in": return Array.isArray(v) ? v.indexOf(c.value) >= 0 : scalar(v) === c.value;
      case "notIn": return Array.isArray(v) ? v.indexOf(c.value) < 0 : scalar(v) !== c.value;
      case "gt": return parseFloat(scalar(v)) > c.value;
      case "gte": return parseFloat(scalar(v)) >= c.value;
      case "lt": return parseFloat(scalar(v)) < c.value;
      case "lte": return parseFloat(scalar(v)) <= c.value;
      case "matches": try { return new RegExp(c.value).test(scalar(v)); } catch (e) { return false; }
      default:
        gaps.push("Condition uses operator '" + c.op + "' which the renderer does not implement.");
        return true;
    }
  }
  function isVisible(f) {
    return !f.visibleWhen || evalCond(f.visibleWhen);
  }
  function isRequired(f) {
    return !!f.required || (f.requiredWhen && evalCond(f.requiredWhen));
  }
  function collectTriggers(def) {
    var set = new Set();
    function visit(c) {
      if (!c) return;
      if (c.allOf) c.allOf.forEach(visit);
      if (c.anyOf) c.anyOf.forEach(visit);
      if (c.not) visit(c.not);
      if (c.field) set.add(c.field);
    }
    function fields(arr) {
      arr.forEach(function (f) {
        visit(f.visibleWhen); visit(f.requiredWhen); visit(f.enabledWhen);
        if (f.fields) fields(f.fields);
      });
    }
    (def.sections || []).forEach(function (s) {
      visit(s.visibleWhen); fields(s.fields || []);
      (s.constraints || []).forEach(function (k) { visit(k.when); visit(k.assert); });
    });
    (def.constraints || []).forEach(function (k) { visit(k.when); visit(k.assert); });
    return set;
  }

  // ------------------------------------------------------------ label helper
  function reqStar(f) {
    if (!isRequired(f)) return null;
    return el("span", "req", "*");
  }

  // --------------------------------------------------------- change handlers
  function onScalarInput(path, controlValue) {
    setVal(path, controlValue);
    if (triggerPaths.has(path)) render(); // a text field referenced by a condition
  }
  function onDiscreteChange(path, controlValue) {
    setVal(path, controlValue);
    render(); // discrete controls may flip conditional visibility
  }

  // --------------------------------------------------------- field renderers
  // Returns a DOM node for one field at `path`. Inline vs block chosen by group.
  function renderField(f, base) {
    var path = base + "." + f.id;
    var inline = !!(f.presentation && f.presentation.group);

    switch (f.kind) {
      case "boilerplate":
        if (f.text == null) { gaps.push("boilerplate field '" + path + "' has no `text`."); }
        return el("span", "boilerplate", f.text || "");

      case "text":
      case "number":
      case "date":
      case "textarea":
        return f.repeatable ? repeatScalar(f, path, inline) : scalarControl(f, path, inline, 0, null);

      case "strikeoutChoice":
        return strikeoutControl(f, path, inline);

      case "radio":
        return radioControl(f, path);

      case "dropdown":
        return dropdownControl(f, path, inline);

      case "checkbox":
        return checkboxControl(f, path);

      case "checkboxGroup":
        return checkboxGroupControl(f, path);

      case "signature":
      case "signatureBlock":
        return f.kind === "signature" ? signatureControl(f, path) : groupControl(f, path);

      case "group":
        return groupControl(f, path);

      case "table":
        return tableControl(f, path);

      default:
        gaps.push("Field '" + path + "' has unsupported kind '" + f.kind + "'.");
        return el("span", "unsupported", "[unsupported kind: " + f.kind + "]");
    }
  }

  function labelFor(f, forId) {
    var lab = el("label", "field-label");
    lab.setAttribute("for", forId);
    lab.appendChild(document.createTextNode(f.label != null ? f.label : f.id));
    var star = reqStar(f);
    if (star) lab.appendChild(star);
    return lab;
  }

  // scalar single control (optionally one instance of a repeatable), inline or block
  function scalarControl(f, path, inline, idx, arrPath) {
    var id = "c_" + (arrPath || path) + (arrPath ? "_" + idx : "");
    var isTextarea = f.kind === "textarea" || (f.presentation && f.presentation.multiline);
    var input = isTextarea ? el("textarea") : el("input");
    if (!isTextarea) input.type = f.kind === "date" ? "date" : (f.kind === "number" ? "number" : "text");
    input.id = id;

    // value binding (single vs repeatable-instance)
    var readPath = arrPath || path;
    var val = arrPath ? (getVal(arrPath) || [])[idx] : getVal(path);
    input.value = val == null ? "" : val;

    if (f.validation && f.validation.pattern) { input.setAttribute("pattern", f.validation.pattern); }
    if (f.label) { input.title = f.label; if (inline) input.placeholder = f.label; }

    input.addEventListener("input", function () {
      if (arrPath) {
        var a = getVal(arrPath) || [];
        a[idx] = input.value;
        setVal(arrPath, a);
        if (triggerPaths.has(arrPath)) render();
      } else {
        onScalarInput(path, input.value);
      }
    });
    if (triggerPaths.has(readPath)) {
      input.addEventListener("change", function () { render(); });
    }

    if (inline) {
      var wrap = el("span", "inline-field");
      wrap.appendChild(input);
      var cap = el("span", "cap", (f.label || f.id) + (isRequired(f) ? " *" : ""));
      wrap.appendChild(cap);
      return wrap;
    }
    var block = el("div", "field block-control");
    block.appendChild(labelFor(f, id));
    if (f.description) block.appendChild(el("div", "desc", f.description));
    block.appendChild(input);
    return block;
  }

  // repeatable scalar: array of controls with add/remove
  function repeatScalar(f, path, inline) {
    var min = minCount(f.repeatable);
    if (!Array.isArray(getVal(path))) {
      var start = Math.max(min, 1); // ensure at least one editable instance
      state[path] = Array.from({ length: start }, function () { return ""; });
    }
    var arr = getVal(path);
    var container = el(inline ? "span" : "div", inline ? "inline-field" : "field");
    if (!inline) { container.appendChild(labelFor(f, "rep_" + path)); if (f.description) container.appendChild(el("div", "desc", f.description)); }

    var itemsWrap = el(inline ? "span" : "div");
    arr.forEach(function (_, idx) {
      var row = el(inline ? "span" : "div", inline ? "inline-field" : "repeat-item");
      var ctl = scalarControl(f, path, inline, idx, path);
      row.appendChild(ctl);
      var del = el("button", "btn del", "−");
      del.type = "button";
      del.title = "Remove " + (f.repeatable.itemLabel || "item");
      del.disabled = arr.length <= Math.max(min, 1);
      del.addEventListener("click", function () { arr.splice(idx, 1); setVal(path, arr); render(); });
      row.appendChild(del);
      itemsWrap.appendChild(row);
    });
    container.appendChild(itemsWrap);

    var add = el("button", "btn add", "+ " + (f.repeatable.itemLabel || "Add"));
    add.type = "button";
    if (f.repeatable.max != null && arr.length >= f.repeatable.max) add.disabled = true;
    add.addEventListener("click", function () { arr.push(""); setVal(path, arr); render(); });
    container.appendChild(add);
    return container;
  }

  function strikeoutControl(f, path, inline) {
    if (!f.options || !f.options.length) { gaps.push("strikeoutChoice '" + path + "' has no options."); }
    var current = getVal(path);
    var wrap = el(inline ? "span" : "div", inline ? "inline-field" : "field");
    if (!inline) { var lab = el("label", "field-label"); lab.textContent = f.label || f.id; var s = reqStar(f); if (s) lab.appendChild(s); wrap.appendChild(lab); }
    var strike = el("span", "strike");
    (f.options || []).forEach(function (opt) {
      var o = el("span", "strike-opt", opt.label != null ? opt.label : opt.value);
      if (current) { o.classList.add(current === opt.value ? "selected" : "struck"); }
      o.addEventListener("click", function () {
        onDiscreteChange(path, current === opt.value ? "" : opt.value);
      });
      strike.appendChild(o);
    });
    wrap.appendChild(strike);
    if (inline) { var cap = el("span", "cap", (f.label || f.id) + (isRequired(f) ? " *" : "")); wrap.appendChild(cap); }
    return wrap;
  }

  function radioControl(f, path) {
    if (!f.options || !f.options.length) { gaps.push("radio '" + path + "' has no options."); }
    var current = getVal(path);
    var wrap = el("div", "field");
    wrap.appendChild(labelFor(f, "r_" + path));
    if (f.description) wrap.appendChild(el("div", "desc", f.description));
    (f.options || []).forEach(function (opt, i) {
      var row = el("label", "radio-opt");
      var input = el("input");
      input.type = "radio";
      input.name = path;
      input.value = opt.value;
      input.checked = current === opt.value;
      input.addEventListener("change", function () { onDiscreteChange(path, opt.value); });
      row.appendChild(input);
      row.appendChild(el("span", null, opt.label != null ? opt.label : opt.value));
      wrap.appendChild(row);
    });
    return wrap;
  }

  function dropdownControl(f, path, inline) {
    if (!f.options || !f.options.length) { gaps.push("dropdown '" + path + "' has no options."); }
    var current = getVal(path);
    var sel = el("select");
    sel.id = "s_" + path;
    var ph = el("option", null, "— Select —");
    ph.value = "";
    sel.appendChild(ph);
    (f.options || []).forEach(function (opt) {
      var o = el("option", null, opt.label != null ? opt.label : opt.value);
      o.value = opt.value;
      if (current === opt.value) o.selected = true;
      sel.appendChild(o);
    });
    sel.addEventListener("change", function () { onDiscreteChange(path, sel.value); });

    if (inline) {
      var w = el("span", "inline-field");
      w.appendChild(sel);
      w.appendChild(el("span", "cap", (f.label || f.id) + (isRequired(f) ? " *" : "")));
      return w;
    }
    var block = el("div", "field block-control");
    block.appendChild(labelFor(f, sel.id));
    block.appendChild(sel);
    return block;
  }

  function checkboxControl(f, path) {
    var wrap = el("label", "radio-opt");
    var input = el("input");
    input.type = "checkbox";
    input.checked = getVal(path) === true || getVal(path) === "true";
    input.addEventListener("change", function () { onDiscreteChange(path, input.checked); });
    wrap.appendChild(input);
    wrap.appendChild(el("span", null, (f.label || f.id) + (isRequired(f) ? " *" : "")));
    return wrap;
  }

  function checkboxGroupControl(f, path) {
    if (!f.options || !f.options.length) { gaps.push("checkboxGroup '" + path + "' has no options."); }
    var current = Array.isArray(getVal(path)) ? getVal(path) : [];
    var wrap = el("div", "field");
    wrap.appendChild(labelFor(f, "cg_" + path));
    (f.options || []).forEach(function (opt) {
      var row = el("label", "radio-opt");
      var input = el("input");
      input.type = "checkbox";
      input.checked = current.indexOf(opt.value) >= 0;
      input.addEventListener("change", function () {
        var set = Array.isArray(getVal(path)) ? getVal(path).slice() : [];
        var at = set.indexOf(opt.value);
        if (input.checked && at < 0) set.push(opt.value);
        if (!input.checked && at >= 0) set.splice(at, 1);
        onDiscreteChange(path, set);
      });
      row.appendChild(input);
      row.appendChild(el("span", null, opt.label != null ? opt.label : opt.value));
      wrap.appendChild(row);
    });
    return wrap;
  }

  function signatureControl(f, path) {
    var wrap = el("div", "field");
    wrap.appendChild(labelFor(f, "sig_" + path));
    var canvas = el("canvas", "sig-pad");
    canvas.width = 340; canvas.height = 90;
    wrap.appendChild(canvas);
    var ctx = canvas.getContext("2d");
    ctx.lineWidth = 2; ctx.lineCap = "round"; ctx.strokeStyle = "#12203a";
    // restore previously drawn signature after a re-render
    if (getVal(path)) {
      var img = new Image();
      img.onload = function () { ctx.drawImage(img, 0, 0); };
      img.src = getVal(path);
    }
    var drawing = false, last = null;
    function pos(e) { var r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; }
    canvas.addEventListener("pointerdown", function (e) { drawing = true; last = pos(e); canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", function (e) { if (!drawing) return; var p = pos(e); ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke(); last = p; });
    canvas.addEventListener("pointerup", function () { drawing = false; setVal(path, canvas.toDataURL()); });
    var clear = el("button", "btn del", "Clear");
    clear.type = "button";
    clear.addEventListener("click", function () { ctx.clearRect(0, 0, canvas.width, canvas.height); setVal(path, ""); });
    var bar = el("div"); bar.style.marginTop = "4px"; bar.appendChild(clear);
    wrap.appendChild(bar);
    return wrap;
  }

  // group / signatureBlock: nested fields; repeatable => repeat whole block
  function groupControl(f, path) {
    var wrap = el("div", "field");
    if (f.label) { var lab = el("label", "field-label"); lab.textContent = f.label; wrap.appendChild(lab); }
    if (!f.fields) { gaps.push("group/signatureBlock '" + path + "' has no `fields`."); return wrap; }
    var instances = f.repeatable ? Math.max(minCount(f.repeatable), 1) : 1;
    // Track instance count in state for repeatable groups
    if (f.repeatable) {
      if (typeof getVal(path + "#count") !== "number") state[path + "#count"] = instances;
      instances = getVal(path + "#count");
    }
    for (var i = 0; i < instances; i++) {
      var instPath = f.repeatable ? path + "." + i : path;
      var box = el("div");
      if (f.repeatable) { box.style.borderLeft = "3px solid #d0d5dd"; box.style.paddingLeft = "8px"; box.style.margin = "6px 0"; }
      box.appendChild(renderFields(f.fields, instPath));
      wrap.appendChild(box);
    }
    if (f.repeatable) {
      var add = el("button", "btn add", "+ " + (f.repeatable.itemLabel || "Add"));
      add.type = "button";
      add.addEventListener("click", function () { setVal(path + "#count", getVal(path + "#count") + 1); render(); });
      wrap.appendChild(add);
    }
    return wrap;
  }

  function tableControl(f, path) {
    if (!f.columns || !f.columns.length) { gaps.push("table '" + path + "' has no `columns`."); return el("div"); }
    var min = minCount(f.repeatable);
    if (!Array.isArray(getVal(path))) {
      var start = Math.max(min, 1);
      state[path] = Array.from({ length: start }, function () { return {}; });
    }
    var rows = getVal(path);

    var wrap = el("div", "field");
    if (f.label) { var lab = el("label", "field-label"); lab.textContent = f.label; var s = reqStar(f); if (s) lab.appendChild(s); wrap.appendChild(lab); }

    var table = el("table", "grid");
    var thead = el("thead");
    var htr = el("tr");
    f.columns.forEach(function (col) { htr.appendChild(el("th", null, col.label != null ? col.label : col.id)); });
    htr.appendChild(el("th", "rowctl", ""));
    thead.appendChild(htr);
    table.appendChild(thead);

    var tbody = el("tbody");
    rows.forEach(function (row, rIdx) {
      var tr = el("tr");
      f.columns.forEach(function (col) {
        var td = el("td");
        td.appendChild(cellControl(col, path, rIdx));
        tr.appendChild(td);
      });
      var ctl = el("td", "rowctl");
      var del = el("button", "btn del", "−");
      del.type = "button";
      del.disabled = rows.length <= Math.max(min, 1);
      del.addEventListener("click", function () { rows.splice(rIdx, 1); setVal(path, rows); render(); });
      ctl.appendChild(del);
      tr.appendChild(ctl);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    wrap.appendChild(table);

    var add = el("button", "btn add", "+ " + (f.repeatable && f.repeatable.itemLabel ? f.repeatable.itemLabel : "Add row"));
    add.type = "button";
    add.style.marginTop = "6px";
    if (f.repeatable && f.repeatable.max != null && rows.length >= f.repeatable.max) add.disabled = true;
    add.addEventListener("click", function () { rows.push({}); setVal(path, rows); render(); });
    wrap.appendChild(add);
    return wrap;
  }

  function cellControl(col, tablePath, rIdx) {
    var cell = col.cell || {};
    var rows = getVal(tablePath);
    var input;
    if (cell.kind === "date") { input = el("input"); input.type = "date"; }
    else if (cell.kind === "number") { input = el("input"); input.type = "number"; }
    else if (cell.kind === "textarea") { input = el("textarea"); }
    else if (cell.kind === "dropdown" || cell.kind === "radio" || cell.kind === "strikeoutChoice") {
      if (!cell.options) { gaps.push("table '" + tablePath + "' column '" + col.id + "' is kind '" + cell.kind + "' but has no options."); }
      input = el("select");
      var ph = el("option", null, "—"); ph.value = ""; input.appendChild(ph);
      (cell.options || []).forEach(function (o) { var opt = el("option", null, o.label != null ? o.label : o.value); opt.value = o.value; input.appendChild(opt); });
    }
    else { input = el("input"); input.type = "text"; }

    var v = rows[rIdx] ? rows[rIdx][col.id] : "";
    input.value = v == null ? "" : v;
    if (cell.format) input.title = cell.format;
    var evt = (input.tagName === "SELECT") ? "change" : "input";
    input.addEventListener(evt, function () {
      if (!rows[rIdx]) rows[rIdx] = {};
      rows[rIdx][col.id] = input.value;
      setVal(tablePath, rows);
    });
    return input;
  }

  // ------------------------------------------------ section / group layout
  // Renders a list of fields, grouping consecutive same-`presentation.group`
  // fields into one inline flow (so boilerplate + inline inputs read as a sentence).
  function renderFields(fields, base) {
    var frag = document.createDocumentFragment();
    var i = 0;
    while (i < fields.length) {
      var f = fields[i];
      var grp = f.presentation && f.presentation.group;
      if (grp) {
        var run = el("div", "inline-flow");
        var j = i;
        while (j < fields.length) {
          var g = fields[j];
          var ggrp = g.presentation && g.presentation.group;
          if (ggrp !== grp) break;
          if (isVisible(g)) run.appendChild(renderField(g, base));
          j++;
        }
        if (run.childNodes.length) frag.appendChild(run);
        i = j;
      } else {
        if (isVisible(f)) frag.appendChild(renderField(f, base));
        i++;
      }
    }
    return frag;
  }

  function renderSection(s) {
    var row = el("div", "section-row");
    var left = el("div", "section-title", s.title != null ? s.title : s.id);
    if (s.description) left.appendChild(el("div", "section-desc", s.description));
    var body = el("div", "section-body");
    body.appendChild(renderFields(s.fields || [], s.id));
    row.appendChild(left);
    row.appendChild(body);
    return row;
  }

  function renderHeader(def) {
    var h = el("div", "form-header");
    h.appendChild(el("div", "form-number", "FORM " + (def.formNumber != null ? def.formNumber : "?")));
    var lr = def.legalReference || {};
    var statute = (lr.act || []).join("; ");
    if (lr.rules && lr.rules[0]) statute += (statute ? " and " : "") + lr.rules[0];
    if (statute) h.appendChild(el("div", "statute", statute));
    if (def.officialName) h.appendChild(el("div", "subject", def.officialName.toUpperCase()));
    // Citation: only the 2nd+ entries of legalReference.rules carry the "See rule..." line.
    if (lr.rules && lr.rules.length > 1) {
      h.appendChild(el("div", "citation", lr.rules.slice(1).join("; ")));
      findings.push(
        "Header citation rendered verbatim from legalReference.rules[1] (\"" + lr.rules.slice(1).join("; ") +
        "\"). The official form prints it parenthesised, e.g. \"(See ...)\"; the parenthesised form exists only in metadata.printedHeader, which the schema marks as not-for-rendering. A first-class legalReference.citation would remove this ambiguity. Not required by the render spec; not invented here."
      );
    }
    return h;
  }

  function renderNotes(notes) {
    var wrap = el("div", "notes");
    wrap.appendChild(el("h3", null, "Notes"));
    var ul = el("ul");
    notes.forEach(function (n) { ul.appendChild(el("li", null, n)); });
    wrap.appendChild(ul);
    return wrap;
  }

  // ---------------------------------------------------------------- render
  function render() {
    gaps = [];
    findings = [];
    appEl.innerHTML = "";
    appEl.appendChild(renderHeader(DEF));
    (DEF.sections || []).forEach(function (s) {
      if (s.visibleWhen && !evalCond(s.visibleWhen)) return;
      appEl.appendChild(renderSection(s));
    });
    if (DEF.notes && DEF.notes.length) appEl.appendChild(renderNotes(DEF.notes));
    renderCompleteness();
    if (callbacks && typeof callbacks.onGapsChange === "function") {
      callbacks.onGapsChange(gaps.slice(), findings.slice());
    }
  }

  function renderCompleteness() {
    completenessEl.innerHTML = "";
    var uniqueGaps = Array.from(new Set(gaps));
    var uniqueFindings = Array.from(new Set(findings));
    if (uniqueGaps.length === 0) {
      completenessEl.className = "completeness ok";
      completenessEl.appendChild(el("h2", null, "✓ Definition is complete"));
      completenessEl.appendChild(el("div", null,
        "The renderer built this entire form editor from its JSON definition alone — no required information was missing, nothing was invented."));
    } else {
      completenessEl.className = "completeness gaps";
      completenessEl.appendChild(el("h2", null, "⚠ Missing information (" + uniqueGaps.length + ")"));
      completenessEl.appendChild(el("div", null, "The renderer needed the following but the definition did not supply it:"));
      var ul = el("ul");
      uniqueGaps.forEach(function (g) { ul.appendChild(el("li", null, g)); });
      completenessEl.appendChild(ul);
    }
    if (uniqueFindings.length) {
      var fWrap = el("div", "findings");
      fWrap.appendChild(el("strong", null, "Non-blocking fidelity notes:"));
      var ul2 = el("ul");
      uniqueFindings.forEach(function (x) { ul2.appendChild(el("li", null, x)); });
      fWrap.appendChild(ul2);
      completenessEl.appendChild(fWrap);
    }
  }

  // ------------------------------------------------------------------- mount
  function mount(container, definition, initialValues, cbs) {
    if (!container) throw new Error("FormRenderer.mount requires a container element.");
    if (!definition) throw new Error("FormRenderer.mount requires a form definition object.");

    DEF = definition;
    callbacks = cbs || {};
    state = initialValues ? JSON.parse(JSON.stringify(initialValues)) : {};
    gaps = [];
    findings = [];
    triggerPaths = collectTriggers(DEF);

    container.innerHTML = "";
    completenessEl = el("section", "completeness");
    appEl = el("main", "app");
    container.appendChild(completenessEl);
    container.appendChild(appEl);

    render();

    return {
      getValues: function () { return snapshot(); },
      setValues: function (values) { state = values ? JSON.parse(JSON.stringify(values)) : {}; render(); },
      getGaps: function () { return gaps.slice(); },
      getFindings: function () { return findings.slice(); },
      unmount: function () {
        container.innerHTML = "";
        DEF = null; state = {}; appEl = null; completenessEl = null;
      }
    };
  }

  window.FormRenderer = { mount: mount };
})();
