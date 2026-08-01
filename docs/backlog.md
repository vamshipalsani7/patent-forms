# Backlog

Work that has been considered and deliberately deferred, with the condition that
would make it worth doing. An item here is not rejected — it is waiting on a
trigger.

---

## Deferred extractors: FER, Hearing Notice, Controller Order

**Status:** deferred, 2026-08-01
**Trigger to build:** a form definition's `autofill.sources[]` cites one of them.

These three were originally scheduled as extractors #5–#7. A demand analysis of
all 34 form definitions found that **no definition references any of them**:

| sourceType | `autofill.sources[]` citations |
|---|---|
| `form1` | 124 |
| `patent_certificate` | 63 |
| `form26_authorisation` | 32 |
| `form2_specification` | 20 |
| `assignment_document` | 10 |
| `priority_document` | 9 |
| `form5` | 7 |
| `pct_document` | 6 |
| `form16_registration` | 1 |
| **FER / Hearing Notice / Controller Order** | **0** |

They are also absent from `backend/vocabulary/registry.json` entirely — no
sourceType, and no key that only they could supply.

**Why this matters rather than being a technicality.** The registry is
demand-driven by design: *"A key may only appear here if at least one form
definition's autofill block references it. Generated from demand — not from a
model of everything about a patent."* An extractor for a source nothing consumes
produces facts that reach no field. The work would be invisible to the user.

**The vision risk specifically.** What these three documents uniquely carry —
over and above the application number and title already available from richer
sources — is *dates*: the FER reply deadline, the hearing date, the compliance
window in a Controller order. Building extraction around those values pulls the
product toward deadline tracking, which the frozen vision excludes by name.
Patent Forms prepares forms; it does not tell the user when to file them.

**What would legitimately un-defer this.** Not "we support FER now", but a
concrete field on a concrete form. For example, if Form 4 (extension of time)
gains an authored autofill source for the original due date, or a Form 13
amendment field needs the objection reference, then the demand exists and the
extractor becomes justified — scoped to exactly the cited keys.

**Cost when the trigger fires:** small. The plumbing is already generic. Adding
one is: a `DocumentType` member, classifier anchors, a `PatternExtractor`
subclass declaring patterns, and a registry entry. No pipeline change.

---

## ~~Multi-row autofill for repeatable tables~~ — DONE 2026-08-01

Implemented. The mapper now emits the renderer's actual state shape for all four
field kinds. The original diagnosis in this entry was incomplete: repeatable
*scalars* did fill row 1 only, but tables and repeatable *groups* were emitting
paths form-renderer.js never reads (`path[].colId`, and un-indexed `path.childId`
instead of `path.i.childId`), so they filled **nothing**. See the limitations
below for what remains.

---

## Positional correlation has no fact-level identity

**Status:** accepted limitation, 2026-08-01
**Trigger to revisit:** a user reports a table row pairing values that belong to
different entries.

Row *i* of a table, and instance *i* of a repeatable group, are assembled by
taking the *i*-th fact of each contributing key. `Fact` records which document
and page a value came from, not which inventor or which foreign application it
belonged to, so position is the only join available.

This holds when the values came from one document in document order, which is
how every extractor in the library emits them. It breaks when two keys are
filled from different documents that list their entries in different orders —
country from one priority document, application number from another. Nothing in
the mapper can detect that.

Mitigations already in place: columns of unequal length produce short rows rather
than padded ones, so a genuinely unknown cell stays blank instead of borrowing a
neighbour's; and every cell keeps its own `Fact`, so a user reviewing the row can
see that two values came from different documents.

The real fix is a group/instance ordinal on `Fact`, set by the extractor at the
point where it already knows it is reading the second inventor block. That is a
model change plus a change to every multi-value extractor, and it is not worth
doing before a real document exercises the failure.

---

## Repeated-value ordering depends on equal confidence

**Status:** accepted limitation, 2026-08-01

`PatentProfile.get_facts()` sorts by confidence descending. The sort is stable,
so facts extracted at equal confidence keep document order — and every
multi-value key in the library is emitted at a single confidence by its
extractor, so inventors currently arrive in the order the document printed them.

Inventor order is legally meaningful on Form 5, so this matters. But it is a
property of how the extractors happen to assign confidence today, not something
the model guarantees. If an extractor ever varies confidence across instances of
the same key, the order silently changes. The ordinal described in the previous
entry would fix this too.

---

## Re-extraction does not expand a saved draft's repeatable groups

**Status:** working as designed, recorded because it looks like a bug

`mainArea.showForm()` lets draft values win over suggestions, including the
`path#count` entry that controls how many instances of a repeatable group are
drawn. So if a user saves a draft with one inventor block and later uploads a
specification naming three, the newly suggested `#count` of 3 is overridden by
the saved 1, and instances 2 and 3 sit in state unread until the user clicks
"+ Add" — at which point their values appear immediately, already filled.

This is the same "user edits are never overwritten" rule that governs every
other field, and changing it for `#count` alone would be inconsistent. Recorded
so it is not mistaken for the multi-row bug fixed above.
