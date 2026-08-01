/*
 * Patent Workspace view — the milestone's central screen.
 *
 * These tests drive the real workspaceView.js against the harness DOM, using
 * summary payloads shaped exactly like the backend's /api/workspace response.
 * They pin the four promises of the screen — grouped facts with provenance,
 * conflict review the user resolves, missing-info the user can fill, and no
 * internal engine names ever shown — plus the document-first empty state.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass } from "./harness.mjs";

function value(v, over = {}) {
  return {
    value: v, confidence: 0.85, page: 1,
    source_document: "spec.pdf", source_type: "form2_specification",
    source_type_label: "Specification", ...over,
  };
}

function baseSummary(over = {}) {
  return {
    workspace_id: "default",
    documents: [
      { document_id: "d1", filename: "spec.pdf", document_type: "Specification",
        status: "extracted", fact_count: 3, page_count: 1 },
    ],
    sections: [
      { id: "title", label: "Title", fields: [
        { key: "invention.title", label: "Title of the Invention", conflict: false,
          values: [value("A Solar Cooler")] },
      ]},
      { id: "inventors", label: "Inventors", fields: [
        { key: "inventor.name", label: "Inventor Name", conflict: false,
          values: [value("Rajesh Kumar"), value("Priya Sharma")] },
      ]},
    ],
    missing: [],
    stats: { document_count: 1, fact_count: 3, conflict_count: 0, missing_count: 0 },
    ...over,
  };
}

describe("workspaceView", () => {
  let ns, container;
  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "workspaceOverrides.js", "workspaceView.js"));
    // No window.prompt stub: the view must not use browser dialogs. If any code
    // path reaches for prompt/confirm, it will throw and fail the test.
    container = makeContainer();
  });

  const render = (summary, opts) =>
    ns.workspaceView.render(container, summary, Object.assign({ workspaceId: "default" }, opts));

  describe("empty state (document-first)", () => {
    test("with no documents it invites uploading, not a blank form", () => {
      render({ documents: [], sections: [], missing: [], stats: {} });
      const text = container.textContent;
      assert.match(text, /Start a patent matter/i);
      assert.match(text, /Upload your patent documents/i);
    });
  });

  describe("grouped facts with provenance", () => {
    test("renders section labels and field values", () => {
      render(baseSummary());
      const text = container.textContent;
      assert.match(text, /Title of the Invention/);
      assert.match(text, /A Solar Cooler/);
      assert.match(text, /Inventor Name/);
    });

    test("keeps every value of a multi-valued field", () => {
      render(baseSummary());
      const text = container.textContent;
      assert.match(text, /Rajesh Kumar/);
      assert.match(text, /Priya Sharma/);
    });

    test("every value shows its source document, page and confidence", () => {
      render(baseSummary());
      const text = container.textContent;
      assert.match(text, /Specification/);
      assert.match(text, /spec\.pdf/);
      assert.match(text, /p\.1/);
    });

    test("confidence is shown in plain language, with the exact figure on hover", () => {
      render(baseSummary());
      // Language, not a bare number, in the visible text…
      assert.match(container.textContent, /High confidence/);
      assert.doesNotMatch(container.textContent, /85% confident/);
      // …and the precise percentage preserved as a tooltip for anyone who wants it.
      const src = findByClass(container, "wsp-value-src");
      assert.equal(src.getAttribute("title"), "85% confidence");
    });

    test("low and medium confidence read differently from high", () => {
      const s = baseSummary({
        sections: [{ id: "title", label: "Title", fields: [
          { key: "invention.title", label: "Title of the Invention", conflict: false,
            values: [value("A Solar Cooler", { confidence: 0.5 })] },
        ]}],
      });
      render(s);
      assert.match(container.textContent, /Low confidence/);
    });
  });

  describe("conflicts — the user decides", () => {
    const conflicting = () => baseSummary({
      sections: [
        { id: "title", label: "Title", fields: [
          { key: "invention.title", label: "Title of the Invention", conflict: true,
            values: [value("A Solar Cooler"), value("An Older Title", { source_document: "old.pdf" })] },
        ]},
      ],
      stats: { document_count: 2, fact_count: 2, conflict_count: 1, missing_count: 0 },
    });

    test("a conflict shows a review flag and both values", () => {
      render(conflicting());
      const text = container.textContent;
      assert.match(text, /Needs review/i);
      assert.match(text, /A Solar Cooler/);
      assert.match(text, /An Older Title/);
    });

    test("choosing a value resolves the conflict and persists the choice", () => {
      render(conflicting());
      findByText(container, "Use this").click();  // pick the first option
      const text = container.textContent;
      assert.match(text, /Resolved/i);
      assert.doesNotMatch(text, /Needs review/i);

      // Persisted: a fresh render of the same summary stays resolved.
      const fresh = makeContainer();
      ns.workspaceView.render(fresh, conflicting(), { workspaceId: "default" });
      assert.match(fresh.textContent, /Resolved/i);
    });

    test("a resolved conflict can be changed via an inline Change control", () => {
      render(conflicting());
      findByText(container, "Use this").click();       // resolve to the first value
      assert.match(container.textContent, /Resolved/i);

      findByText(container, "Change").click();          // reopen the picker in place
      assert.match(container.textContent, /Needs review|Choose the one to use/i);
      // Both options are offered again so the user can pick the other value.
      assert.match(container.textContent, /A Solar Cooler/);
      assert.match(container.textContent, /An Older Title/);
    });

    test("the review banner disappears once all conflicts are resolved", () => {
      render(conflicting());
      assert.match(container.textContent, /Review needed/i);
      findByText(container, "Use this").click();
      assert.doesNotMatch(container.textContent, /Review needed/i);
    });
  });

  describe("missing information", () => {
    const withMissing = () => baseSummary({
      missing: [{ key: "applicant.nationality", label: "Applicant Nationality" }],
      stats: { document_count: 1, fact_count: 3, conflict_count: 0, missing_count: 1 },
    });

    test("a missing field is shown as not found, with a way to enter it", () => {
      render(withMissing());
      const text = container.textContent;
      assert.match(text, /Applicant Nationality/);
      assert.match(text, /Not found/i);
      assert.ok(findByText(container, "Enter value"), "no Enter value control");
    });

    test("entering a value uses an inline input, not a browser prompt", () => {
      // window.prompt is intentionally sabotaged: if the view still used it,
      // this test would throw rather than pass.
      globalThis.window.prompt = () => { throw new Error("window.prompt must not be used"); };

      render(withMissing());
      findByText(container, "Enter value").click();      // swaps the row to an inline input
      const input = findByClass(container, "wsp-inline-input");
      assert.ok(input, "no inline input appeared");

      input.value = "Indian";
      findByText(container, "Save").click();

      const text = container.textContent;
      assert.match(text, /Indian/);
      assert.match(text, /Entered by you/i);
    });

    test("cancelling inline entry leaves the field unfilled", () => {
      render(withMissing());
      findByText(container, "Enter value").click();
      const input = findByClass(container, "wsp-inline-input");
      input.value = "Indian";
      findByText(container, "Cancel").click();
      assert.doesNotMatch(container.textContent, /Entered by you/i);
      assert.match(container.textContent, /Not found/i);
    });

    test("a workspace with all core fields present shows no missing panel", () => {
      render(baseSummary());  // missing: []
      assert.doesNotMatch(container.textContent, /Information still needed/i);
    });
  });

  describe("uploaded documents", () => {
    test("lists each document with its detected type and status", () => {
      render(baseSummary({
        documents: [
          { document_id: "d1", filename: "spec.pdf", document_type: "Specification",
            status: "extracted", fact_count: 3, page_count: 1 },
          { document_id: "d2", filename: "scan.pdf", document_type: "Unrecognised Document",
            status: "unrecognised", fact_count: 0, page_count: 3 },
        ],
      }));
      const text = container.textContent;
      assert.match(text, /Uploaded Documents/);
      assert.match(text, /spec\.pdf/);
      assert.match(text, /scan\.pdf/);
      assert.match(text, /Couldn’t read/);
    });
  });

  describe("no internal engine names are ever shown", () => {
    test("vocabulary keys and sourceTypes never appear as text", () => {
      render(baseSummary({
        missing: [{ key: "applicant.nationality", label: "Applicant Nationality" }],
      }));
      const text = container.textContent;
      for (const leak of ["invention.title", "inventor.name", "applicant.nationality",
                           "form2_specification", "form1", "autofill", "sourceType"]) {
        assert.ok(!text.includes(leak), "leaked internal name: " + leak);
      }
    });
  });

  describe("guidance toward a form", () => {
    test("offers a path to choosing a form", () => {
      let chose = false;
      render(baseSummary(), { onChooseForm: () => { chose = true; } });
      assert.match(container.textContent, /Ready to prepare a form/i);
      findByText(container, "Choose a form").click();
      assert.equal(chose, true);
    });
  });

  describe("decisions are captured for the form generator", () => {
    // The Workspace→Form bridge: what the user resolves/enters here is what the
    // generated form pre-fills with. This checks the decision reaches the store
    // in the flat {key: value} shape the suggestions request sends.
    test("a resolved conflict and a typed value merge into one decision map", () => {
      const summary = baseSummary({
        sections: [{ id: "title", label: "Title", fields: [
          { key: "invention.title", label: "Title of the Invention", conflict: true,
            values: [value("A"), value("B", { source_document: "b.pdf" })] },
        ]}],
        missing: [{ key: "applicant.nationality", label: "Applicant Nationality" }],
      });
      render(summary);

      findByText(container, "Use this").click();          // resolve title -> "A"
      findByText(container, "Enter value").click();
      findByClass(container, "wsp-inline-input").value = "Indian";
      findByText(container, "Save").click();

      const decisions = ns.workspaceOverrides.merged("default");
      assert.equal(decisions["invention.title"], "A");
      assert.equal(decisions["applicant.nationality"], "Indian");
    });
  });
});
