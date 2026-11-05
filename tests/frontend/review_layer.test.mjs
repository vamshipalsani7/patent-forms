/*
 * Review layer — the DOM decoration that turns the rendered form into a review.
 *
 * Rather than run the real renderer (a browser component), these tests build a
 * minimal field DOM shaped exactly as the renderer emits it — leaf nodes tagged
 * with data-path, each holding a label and a control — and assert the layer's
 * observable behaviour: provenance cards appear with the right language, missing
 * required fields are flagged, editing reveals the field's own control and flips
 * it to "Edited by you", reviewing counts, and the live summary is correct.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass } from "./harness.mjs";

describe("reviewLayer", () => {
  let ns, el, container, app, values, suggestions, reviewedPaths, summary, layer;

  function field(path, { required = false, value = "" } = {}) {
    const node = el("div", "field block-control");
    node.setAttribute("data-path", path);
    const label = el("label", "field-label", "Label");
    if (required) label.appendChild(el("span", "req", "*"));
    node.appendChild(label);
    const c = el("input");
    c.tagName = "INPUT";
    c.value = value;
    node.appendChild(c);
    app.appendChild(node);
    return { node, control: c };
  }

  function build(opts = {}) {
    layer = ns.reviewLayer.attach(container, Object.assign({
      suggestions, getValues: () => values, resolvedKeys: {},
      reviewedPaths, onReviewedChange: () => {}, onSummary: (s) => { summary = s; },
    }, opts));
    layer.refresh();
  }

  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "reviewModel.js", "reviewLayer.js"));
    el = ns.dom.el;
    container = makeContainer();
    app = el("main", "app");
    container.appendChild(app);
    values = {}; suggestions = {}; reviewedPaths = {}; summary = null;
  });

  describe("a field the AI filled from a document", () => {
    let f;
    beforeEach(() => {
      values["s.name"] = "ABC Technologies Pvt Ltd";
      suggestions["s.name"] = {
        value: "ABC Technologies Pvt Ltd", source_label: "Complete Specification",
        fact: { source_type: "form2_specification", method: "anchor", key: "applicant.name", page: 2, confidence: 0.9 },
      };
      f = field("s.name", { value: values["s.name"] });
      build();
    });

    test("shows the value, its source, page and confidence in words", () => {
      const chip = findByClass(f.node, "rev-chip");
      assert.match(chip.textContent, /From Complete Specification/);
      assert.match(chip.textContent, /Page 2/);
      assert.match(chip.textContent, /High Confidence/);
      assert.doesNotMatch(chip.textContent, /%|0\.9|form2_specification/);
    });

    test("hides the raw control until the user chooses to edit", () => {
      assert.equal(f.control.getAttribute("data-rev-hidden"), "1");
    });

    test("clicking the source opens a panel with the extracted text", () => {
      findByClass(f.node, "rev-chip").click();
      const panel = findByClass(f.node, "rev-source-panel");
      assert.ok(panel);
      assert.match(panel.textContent, /Complete Specification/);
      assert.match(panel.textContent, /ABC Technologies Pvt Ltd/);
    });

    test("editing reveals the field's own control and flips to Edited by you", () => {
      findByText(f.node, "Edit").click();
      assert.equal(f.control.getAttribute("data-rev-hidden"), "0");

      values["s.name"] = "ABC Technologies Pvt. Ltd.";
      f.control.value = values["s.name"];
      findByText(f.node, "Save").click();

      assert.match(findByClass(f.node, "rev-chip").textContent, /Edited by you/);
      assert.match(f.node.textContent, /Originally: ABC Technologies Pvt Ltd/);
      assert.equal(summary.edited, 1);
    });

    test("marking reviewed updates the count and persists via the callback", () => {
      let persisted = 0;
      build({ onReviewedChange: () => { persisted += 1; } });
      findByText(f.node, "Mark reviewed").click();
      assert.equal(reviewedPaths["s.name"], true);
      assert.equal(persisted, 1);
      assert.equal(summary.reviewed, 1);
    });
  });

  describe("a value entered or chosen by the user", () => {
    test("a manual value reads as Entered by you", () => {
      values["s.nat"] = "Indian";
      suggestions["s.nat"] = { value: "Indian", source_label: "you",
        fact: { source_type: "user", method: "manual", key: "applicant.nationality", confidence: 1 } };
      const f = field("s.nat", { value: "Indian" });
      build();
      assert.match(findByClass(f.node, "rev-chip").textContent, /Entered by you/);
    });

    test("a conflict-resolved value reads as Selected during review", () => {
      values["s.title"] = "A Solar Cooler";
      suggestions["s.title"] = { value: "A Solar Cooler", source_label: "Patent Certificate",
        fact: { source_type: "patent_certificate", method: "anchor", key: "invention.title", page: 1, confidence: 0.85 } };
      const f = field("s.title", { value: "A Solar Cooler" });
      build({ resolvedKeys: { "invention.title": true } });
      assert.match(findByClass(f.node, "rev-chip").textContent, /Selected during review/);
    });
  });

  describe("missing information", () => {
    test("a required empty field is flagged Missing / Required for this form", () => {
      values["s.addr"] = "";
      const f = field("s.addr", { required: true, value: "" });
      build();
      const card = findByClass(f.node, "rev-missing");
      assert.ok(card);
      assert.match(card.textContent, /Missing/);
      assert.match(card.textContent, /Required for this form/);
      assert.equal(summary.missing, 1);
      assert.equal(summary.complete, false);
    });

    test("completing a missing field clears its flag as the user types", () => {
      // Regression: recount() updated the summary but left the amber card in
      // place, so a field the user had just filled still read "Missing".
      values["s.addr"] = "";
      const f = field("s.addr", { required: true, value: "" });
      build();
      assert.ok(findByClass(f.node, "rev-missing"), "should start flagged");
      assert.equal(summary.missing, 1);

      values["s.addr"] = "12 MG Road, Bengaluru";   // user types
      layer.recount();

      assert.equal(findByClass(f.node, "rev-missing"), null, "flag must clear");
      assert.equal(summary.missing, 0);
      assert.equal(summary.complete, true);
    });

    test("emptying a required field flags it again without a full re-render", () => {
      values["s.addr"] = "something";
      const f = field("s.addr", { required: true, value: "something" });
      build();
      assert.equal(findByClass(f.node, "rev-missing"), null);

      values["s.addr"] = "";
      layer.recount();

      assert.ok(findByClass(f.node, "rev-missing"), "flag must return");
      assert.equal(summary.missing, 1);
    });

    test("an optional empty field is not flagged", () => {
      values["s.opt"] = "";
      field("s.opt", { required: false, value: "" });
      build();
      assert.equal(summary.missing, 0);
      assert.equal(summary.complete, true);
    });

    test("an exempt required field (e.g. signature) shows no Missing card and does not block completion", () => {
      values["s.sig"] = "";
      const f = field("s.sig", { required: true, value: "" });
      build({ exemptPaths: { "s.sig": true } });
      assert.equal(findByClass(f.node, "rev-missing"), null, "exempt field must not show a Missing card");
      assert.equal(summary.missing, 0);
      assert.equal(summary.complete, true);
    });

    test("index-stripping lets an exempt repeatable-group child be recognised", () => {
      values["s.grp.0.sigdate"] = "";
      const f = field("s.grp.0.sigdate", { required: true, value: "" });
      build({ exemptPaths: { "s.grp.sigdate": true } }); // definition path, no index
      assert.equal(findByClass(f.node, "rev-missing"), null);
      assert.equal(summary.missing, 0);
    });
  });

  describe("suggestions with no field in the form", () => {
    test("a structural/orphan suggestion neither decorates nor inflates the count", () => {
      // e.g. a repeatable group's `#count` bookkeeping, which is renderer state,
      // not a rendered field — there is no data-path node for it.
      values["s.name"] = "ABC";
      suggestions["s.name"] = { value: "ABC", source_label: "Specification",
        fact: { source_type: "form2_specification", method: "anchor", key: "applicant.name", page: 1, confidence: 0.9 } };
      suggestions["s.group#count"] = { value: 2, source_label: "Specification",
        fact: { source_type: "form2_specification", method: "anchor", key: "inventor.name", page: 1, confidence: 0.9 } };
      field("s.name", { value: "ABC" });  // only s.name exists as a field node
      build();
      assert.equal(summary.autoFilled, 1, "orphan suggestion must not be counted");
    });
  });

  describe("snapshot for the comparison screen", () => {
    test("captures every field with its label, value and review status", () => {
      values["s.name"] = "ABC Ltd";
      suggestions["s.name"] = { value: "ABC Ltd", source_label: "Specification",
        fact: { source_type: "form2_specification", method: "anchor", key: "applicant.name", page: 1, confidence: 0.9 } };
      field("s.name", { value: "ABC Ltd" });  // the helper gives it a .field-label "Label"
      values["s.addr"] = "";
      field("s.addr", { required: true, value: "" });     // a missing field
      build();

      const shot = layer.snapshot();
      const byPath = {};
      shot.forEach((d) => { byPath[d.path] = d; });
      assert.equal(byPath["s.name"].status, "from_document");
      assert.equal(byPath["s.name"].value, "ABC Ltd");
      assert.equal(byPath["s.name"].label, "Label", "snapshot reads the field's own label");
      assert.equal(byPath["s.addr"].status, "missing");
    });
  });

  describe("idempotence", () => {
    test("re-running decoration does not stack duplicate cards", () => {
      values["s.name"] = "ABC";
      suggestions["s.name"] = { value: "ABC", source_label: "Specification",
        fact: { source_type: "form2_specification", method: "anchor", key: "applicant.name", page: 1, confidence: 0.9 } };
      const f = field("s.name", { value: "ABC" });
      build();
      layer.refresh();
      layer.refresh();
      let cards = 0;
      (function count(n){ if (n.classList && n.classList.contains("rev-card")) cards += 1; (n.children||[]).forEach(count); })(f.node);
      assert.equal(cards, 1, "decoration must be idempotent");
    });
  });
});
