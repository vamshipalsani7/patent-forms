/*
 * The Filing Package screen — the end of the journey.
 *
 * The promise is that everything is already prepared: the user never chooses
 * what to generate, only what to take. These tests pin that promise — all four
 * documents are offered, "Download All" is the primary action, each download
 * reports success or a readable failure, and nothing internal is named.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass } from "./harness.mjs";

describe("downloadView", () => {
  let ns, container, requested;

  function render(over = {}) {
    requested = [];
    ns.downloadView.render(container, Object.assign({
      formNumber: "18",
      onDownload: (part, done) => {
        requested.push(part);
        done({ ok: true, filename: "Form18_RequestExpressExamination.pdf" });
      },
    }, over));
  }

  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "downloadView.js"));
    container = makeContainer();
  });

  describe("the package is presented as already prepared", () => {
    test("announces the package is ready for the named form", () => {
      render();
      assert.match(container.textContent, /Filing Package Ready/i);
      assert.match(container.textContent, /Form 18/);
    });

    test("lists all four documents with what each is for", () => {
      render();
      const text = container.textContent;
      assert.match(text, /Official IPO PDF/);
      assert.match(text, /Editable Word document/);
      assert.match(text, /Filing Summary/);
      assert.match(text, /Provenance Report/);
      assert.match(text, /file with the Patent Office/i);
      assert.match(text, /Not filed with the IPO/i);
    });

    test("offers Download All as the primary action", () => {
      render();
      const all = findByText(container, "Download All (ZIP)");
      assert.ok(all);
      assert.ok(all.classList.contains("primary"));
    });
  });

  describe("downloading", () => {
    test("Download All requests the zip", () => {
      render();
      findByText(container, "Download All (ZIP)").click();
      assert.deepEqual(requested, ["zip"]);
    });

    test("each document can be downloaded on its own", () => {
      render();
      const buttons = [];
      (function walk(n) {
        if (n.tagName === "BUTTON" && n.textContent === "Download") buttons.push(n);
        (n.children || []).forEach(walk);
      })(container);
      assert.equal(buttons.length, 4, "one download button per document");
      buttons.forEach((b) => b.click());
      assert.deepEqual(requested, ["pdf", "docx", "summary", "provenance"]);
    });

    test("a completed download is confirmed by name", () => {
      render();
      findByText(container, "Download All (ZIP)").click();
      const status = findByClass(container, "pkg-status");
      assert.match(status.textContent, /Downloaded Form18_RequestExpressExamination\.pdf/);
    });

    test("a failure is reported in plain language, not silently", () => {
      render({
        onDownload: (part, done) => done({ ok: false, error: "Could not reach the service." }),
      });
      findByText(container, "Download All (ZIP)").click();
      const status = findByClass(container, "pkg-status");
      assert.match(status.textContent, /Could not reach the service/);
      assert.ok(status.classList.contains("err"));
    });

    test("the button is re-enabled after a download resolves", () => {
      render();
      const all = findByText(container, "Download All (ZIP)");
      all.click();
      assert.notEqual(all.disabled, true, "button must not stay disabled");
    });
  });

  describe("navigation", () => {
    test("offers preparing another form when the host supports it", () => {
      let another = 0;
      render({ onAnother: () => { another += 1; } });
      findByText(container, "Prepare another form").click();
      assert.equal(another, 1);
    });

    test("offers a way back to the comparison", () => {
      let back = 0;
      render({ onBack: () => { back += 1; } });
      findByText(container, "← Back to comparison").click();
      assert.equal(back, 1);
    });
  });

  describe("no internal names are shown", () => {
    test("the screen never mentions how the documents were produced", () => {
      render();
      const text = container.textContent.toLowerCase();
      for (const leak of ["mapper", "sourcetype", "json", "reportlab", "endpoint", "api/"]) {
        assert.ok(!text.includes(leak), "leaked: " + leak);
      }
    });
  });
});

describe("packageClient", () => {
  let ns, calls;

  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "packageClient.js"));
    calls = [];
    globalThis.URL = { createObjectURL: () => "blob:x", revokeObjectURL: () => {} };
    globalThis.document.body = {
      appendChild: () => {}, removeChild: () => {},
    };
  });

  const okResponse = (filename) => ({
    ok: true, status: 200,
    headers: { get: (h) => (h === "Content-Disposition" ? `attachment; filename="${filename}"` : null) },
    blob: () => Promise.resolve({ size: 10 }),
  });

  test("posts the payload to the requested part", async () => {
    globalThis.fetch = (url, options) => {
      calls.push({ url, options });
      return Promise.resolve(okResponse("Form18_FilingPackage.zip"));
    };
    const result = await ns.packageClient.download("form_18", "zip", { workspace_id: "default" });
    assert.match(calls[0].url, /\/api\/package\/form_18\?part=zip/);
    assert.equal(calls[0].options.method, "POST");
    assert.deepEqual(JSON.parse(calls[0].options.body), { workspace_id: "default" });
    assert.equal(result.ok, true);
    assert.equal(result.filename, "Form18_FilingPackage.zip");
  });

  test("uses the filename the server asked for", () => {
    const name = ns.packageClient.filenameFrom(
      { headers: { get: () => 'attachment; filename="Form18_Provenance.pdf"' } }, "fallback.bin");
    assert.equal(name, "Form18_Provenance.pdf");
  });

  test("falls back to a sensible name when the header is absent", () => {
    const name = ns.packageClient.filenameFrom({ headers: { get: () => null } }, "fallback.bin");
    assert.equal(name, "fallback.bin");
  });

  test("a server error resolves to a readable failure, never throws", async () => {
    globalThis.fetch = () => Promise.resolve({ ok: false, status: 500 });
    const result = await ns.packageClient.download("form_18", "pdf", {});
    assert.equal(result.ok, false);
    assert.match(result.error, /could not be prepared/i);
  });

  test("an unreachable service resolves to a readable failure", async () => {
    globalThis.fetch = () => Promise.reject(new Error("offline"));
    const result = await ns.packageClient.download("form_18", "pdf", {});
    assert.equal(result.ok, false);
    assert.match(result.error, /Could not reach the service/i);
  });
});
