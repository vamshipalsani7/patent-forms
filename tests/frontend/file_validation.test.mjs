/*
 * fileValidation — the product accepts the document formats patent
 * professionals actually hold, decided by extension (browser MIME types for
 * local Word/text files are unreliable).
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap } from "./harness.mjs";

describe("fileValidation", () => {
  let fv;
  beforeEach(() => {
    ({ ns: { fileValidation: fv } } = bootstrap("fileValidation.js"));
  });

  const file = (name, type = "") => ({ name, type, size: 1024 });

  test("accepts the four supported source formats", () => {
    for (const name of ["a.pdf", "b.docx", "c.doc", "d.txt"]) {
      assert.equal(fv.isSupported(file(name)), true, name);
    }
  });

  test("accepts regardless of a blank or wrong MIME type", () => {
    assert.equal(fv.isSupported(file("spec.docx", "")), true);
    assert.equal(fv.isSupported(file("spec.docx", "application/octet-stream")), true);
  });

  test("is case-insensitive on the extension", () => {
    assert.equal(fv.isSupported(file("SCAN.PDF")), true);
    assert.equal(fv.isSupported(file("Spec.DocX")), true);
  });

  test("rejects unsupported formats", () => {
    for (const name of ["sheet.xlsx", "image.png", "slides.pptx", "archive.zip", "noext"]) {
      assert.equal(fv.isSupported(file(name)), false, name);
    }
  });

  test("rejects a null/undefined file rather than throwing", () => {
    assert.equal(fv.isSupported(null), false);
    assert.equal(fv.isSupported(undefined), false);
  });

  test("extensionOf reads the last dotted segment, lowercased", () => {
    assert.equal(fv.extensionOf(file("My.Patent.Spec.PDF")), ".pdf");
    assert.equal(fv.extensionOf(file("noext")), "");
  });

  test("the accept attribute advertises all four types", () => {
    for (const ext of [".pdf", ".docx", ".doc", ".txt"]) {
      assert.ok(fv.ACCEPT_ATTR.includes(ext), "accept missing " + ext);
    }
  });

  test("supported set matches the backend's advertised extensions", () => {
    assert.deepEqual([...fv.SUPPORTED_EXTENSIONS].sort(), [".doc", ".docx", ".pdf", ".txt"]);
  });
});
