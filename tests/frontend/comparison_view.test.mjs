/*
 * Official IPO Comparison — the trust-verification screen.
 *
 * These drive the real comparisonView.js against a review-layer-shaped snapshot
 * and pin the promises of the screen: field-by-field Official-vs-Generated,
 * the four soft highlight families (AI / user / missing / office), a summary
 * that reads "ready" only when nothing substantive is missing, export gated on
 * completeness, a professional empty state, and no internal names ever shown.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass } from "./harness.mjs";

function snap(over = {}) {
  return Object.assign({
    path: "requester.name", label: "Applicant Name", section: "1. Applicant",
    status: "from_document", value: "ABC Technologies Pvt Ltd",
  }, over);
}

const FULL = [
  snap(),
  snap({ path: "r.nat", label: "Nationality", status: "entered_by_you", value: "Indian" }),
  snap({ path: "r.title", label: "Title", status: "edited_by_you", value: "A Cooler", original: "A Solar Cooler" }),
  snap({ path: "s.addr", label: "Address for Service", section: "2. Service", status: "missing", value: "" }),
  snap({ path: "sig.signature", label: "Signature", section: "3. Sign", status: "exempt", value: "", exemptReason: "signature" }),
  snap({ path: "ad.office", label: "Patent Office", section: "3. Sign", status: "exempt", value: "", exemptReason: "office" }),
];

describe("comparisonView", () => {
  let ns, container;
  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "comparisonView.js"));
    container = makeContainer();
  });

  const render = (opts) => ns.comparisonView.render(container, Object.assign({
    formNumber: "18", officialName: "Request for Examination",
    snapshot: FULL, summary: { autoFilled: 1, edited: 1, missing: 1, complete: false },
    onBack: () => {}, onContinueExport: () => {},
  }, opts));

  describe("two synchronized views", () => {
    test("shows an Official column and a Generated column", () => {
      render();
      assert.match(container.textContent, /Official IPO Form/);
      assert.match(container.textContent, /Generated Form/);
    });

    test("groups fields under their sections", () => {
      render();
      assert.match(container.textContent, /1\. Applicant/);
      assert.match(container.textContent, /2\. Service/);
    });

    test("pairs each official label with its generated value", () => {
      render();
      assert.match(container.textContent, /Applicant Name/);
      assert.match(container.textContent, /ABC Technologies Pvt Ltd/);
    });
  });

  describe("the four highlight families", () => {
    test("AI-filled reads 'Filled automatically'", () => {
      render();
      assert.match(container.textContent, /Filled automatically/);
      assert.ok(findByClass(container, "cmp-ai"));
    });
    test("user values read blue with their own wording", () => {
      render();
      assert.match(container.textContent, /Entered by you/);
      assert.match(container.textContent, /Edited by you/);
      assert.ok(findByClass(container, "cmp-user"));
    });
    test("missing reads amber with a Return to Review cue", () => {
      render();
      assert.match(container.textContent, /Missing/);
      assert.match(container.textContent, /Return to Review/);
      assert.ok(findByClass(container, "cmp-missing"));
    });
    test("office/at-filing fields read grey, labelled accurately", () => {
      render();
      assert.match(container.textContent, /Patent Office Use/);
      assert.match(container.textContent, /Signed at filing/);
      assert.ok(findByClass(container, "cmp-office"));
    });
  });

  describe("summary + export gating", () => {
    test("with missing fields it is not ready and export is disabled", () => {
      render();
      assert.match(container.textContent, /still missing/);
      assert.equal(findByText(container, "Continue to Export →").disabled, true);
    });

    test("with nothing missing it reads Ready for export and enables export", () => {
      let exported = 0;
      render({
        snapshot: FULL.filter((f) => f.status !== "missing"),
        summary: { autoFilled: 1, edited: 1, missing: 0, complete: true },
        onContinueExport: () => { exported += 1; },
      });
      assert.match(container.textContent, /Ready for export/);
      const cont = findByText(container, "Continue to Export →");
      assert.notEqual(cont.disabled, true);
      cont.click();
      assert.equal(exported, 1);
    });
  });

  describe("navigation", () => {
    test("Back to Review calls back", () => {
      let backed = 0;
      render({ onBack: () => { backed += 1; } });
      findByText(container, "← Back to Review").click();
      assert.equal(backed, 1);
    });
  });

  describe("empty state", () => {
    test("no snapshot shows a professional message, never a blank page", () => {
      let backed = 0;
      render({ snapshot: [], onBack: () => { backed += 1; } });
      assert.match(container.textContent, /Comparison unavailable/);
      assert.match(container.textContent, /return to Review/i);
      findByText(container, "← Return to Review").click();
      assert.equal(backed, 1);
    });
  });

  describe("no internal names are ever shown", () => {
    test("statuses, keys, sourceTypes and percentages never appear", () => {
      render();
      const t = container.textContent;
      for (const leak of ["from_document", "entered_by_you", "requester.name", "%", "sourceType", "form2_specification"]) {
        assert.ok(!t.includes(leak), "leaked: " + leak);
      }
    });
  });
});
