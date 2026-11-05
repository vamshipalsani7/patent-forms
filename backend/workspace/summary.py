"""Build the Patent Workspace summary from a PatentProfile.

The summary is the consolidated, human-facing answer to "what do the uploaded
documents tell us about this patent?" — organised the way a patent professional
thinks about a matter (title, applicants, inventors, agent, …), not the way the
extractor stores it (flat vocabulary keys). It also surfaces the two things a
reviewer must not miss: information that is **missing**, and information the
documents **disagree** on.

Design boundaries:
  * Read-only. Consumes facts; produces none. No form logic — the mapper does
    that. No persistence — the store does that.
  * Every displayed value keeps full provenance: which document (by its real
    filename), which page, how confident. A value a user cannot trace is an
    assertion, and these end up on statutory filings.
  * Nothing here is invented. A section appears only if the documents supplied
    facts for it; a field is "missing" only if genuinely absent.

Conflict policy is deliberately conservative — see CONFLICTING_KEYS.
"""

from __future__ import annotations

from typing import Any, Optional

from models.fact import Fact
from models.patent_profile import PatentProfile

# --------------------------------------------------------------------------
# Display vocabulary — the one place raw keys/source-types become UI language.
# The UX rule is that the interface never exposes internal names (vocabulary
# keys, sourceTypes, extractor ids); this map is how that rule is kept.
# --------------------------------------------------------------------------

_KEY_LABELS: dict[str, str] = {
    "invention.title": "Title of the Invention",
    "applicant.name": "Applicant Name",
    "applicant.address": "Applicant Address",
    "applicant.nationality": "Applicant Nationality",
    "applicant.country": "Applicant Country of Residence",
    "inventor.name": "Inventor Name",
    "inventor.nationality": "Inventor Nationality",
    "inventor.address": "Inventor Address",
    "agent.name": "Patent Agent",
    "agent.inpaNumber": "Agent Registration No. (IN/PA)",
    "application.number": "Application Number",
    "application.filingDate": "Filing Date",
    "patent.number": "Patent Number",
    "patent.grantDate": "Date of Grant",
    "patentee.name": "Patentee Name",
    "patentee.address": "Patentee Address",
    "patentee.nationality": "Patentee Nationality",
    "assignee.name": "Assignee Name",
    "assignee.address": "Assignee Address",
    "assignee.nationality": "Assignee Nationality",
    "foreignApplications[].country": "Priority Country",
    "foreignApplications[].number": "Priority Application Number",
    "foreignApplications[].filingDate": "Priority Filing Date",
    "signatory.name": "Signatory",
}

_SOURCE_TYPE_LABELS: dict[str, str] = {
    "form1": "Form 1 (Application for Grant)",
    "form2_specification": "Specification",
    "form3": "Form 3 (Statement & Undertaking)",
    "form5": "Form 5 (Inventorship)",
    "form16_registration": "Form 16 (Registration of Title)",
    "form26_authorisation": "Form 26 (Authorisation of Agent)",
    "form28": "Form 28 (Small Entity)",
    "patent_certificate": "Patent Certificate",
    "priority_document": "Priority Document",
    "pct_document": "PCT Document",
    "assignment_document": "Assignment Deed",
    "publication_record": "Publication Record",
    "generic": "Document",
    "unknown": "Unrecognised Document",
}


def source_type_label(source_type: str) -> str:
    return _SOURCE_TYPE_LABELS.get(source_type, source_type)


def key_label(key: str) -> str:
    return _KEY_LABELS.get(key, key)


# --------------------------------------------------------------------------
# Section layout. Ordered as a professional reads a matter. Every fact lands in
# exactly one section, chosen by `_section_for` below.
# --------------------------------------------------------------------------

_SECTIONS: list[tuple[str, str]] = [
    ("title", "Title"),
    ("applicants", "Applicants"),
    ("inventors", "Inventors"),
    ("agent", "Agent"),
    ("application", "Application"),
    ("patent", "Patent"),
    ("priority", "Priority"),
    ("pct", "PCT"),
    ("assignment", "Assignment"),
    ("other", "Other Details"),
]


def _section_for(fact: Fact) -> str:
    """Route a fact to exactly one section, by precedence.

    Source-type-specific homes (Priority, Assignment, PCT) are tried before the
    key-namespace homes, so a fact that belongs to one of them is not also
    claimed by the generic Application/Patent sections. `application.number` from
    a PCT document therefore reads under PCT — "what your PCT document says" —
    rather than duplicating the Application row.
    """
    key = fact.key
    if key.startswith("foreignApplications"):
        return "priority"
    if key.startswith("assignee."):
        return "assignment"
    if fact.source_type == "pct_document":
        return "pct"
    if key == "invention.title":
        return "title"
    if key.startswith("applicant."):
        return "applicants"
    if key.startswith("inventor."):
        return "inventors"
    if key.startswith("agent."):
        return "agent"
    if key.startswith("patent.") or key.startswith("patentee."):
        return "patent"
    if key.startswith("application."):
        return "application"
    return "other"


# --------------------------------------------------------------------------
# Conflict policy.
#
# A conflict is only raised for keys that are unambiguously SINGULAR for a
# patent matter — a matter has one title, one application number, one grant
# date. Repeatable keys (applicant/inventor names and their particulars,
# foreign applications) legitimately hold several distinct values, so treating
# "more than one value" as a conflict there would cry wolf on every joint
# application. A false conflict is worse than a missed one: it trains the user
# to dismiss the warning. Widen this set only with a rule that can tell a real
# disagreement from normal multiplicity.
# --------------------------------------------------------------------------

CONFLICTING_KEYS: frozenset[str] = frozenset({
    "invention.title",
    "application.number",
    "application.filingDate",
    "patent.number",
    "patent.grantDate",
})

# --------------------------------------------------------------------------
# Missing-information checklist.
#
# The minimum a straightforward application usually needs. Only these are ever
# reported missing, and only when genuinely absent — the UX rule is to never ask
# for something the documents already provide, and never nag for the long tail.
# --------------------------------------------------------------------------

CORE_FIELDS: list[str] = [
    "invention.title",
    "applicant.name",
    "applicant.address",
    "applicant.nationality",
    "inventor.name",
    "application.number",
    "application.filingDate",
]


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------

def build_workspace_summary(profile: PatentProfile) -> dict[str, Any]:
    """Consolidate one workspace's documents and facts into a UI-ready summary.

    Returns a JSON-serialisable dict:
        {
          workspace_id,
          documents:  [ {document_id, filename, document_type, source_type,
                         status, fact_count, page_count}, … ],
          sections:   [ {id, label, fields:[ {key, label, conflict,
                         values:[ {value, confidence, page,
                                   source_document, source_type,
                                   source_type_label} ] } ] }, … ],
          missing:    [ {key, label}, … ],
          stats:      {document_count, fact_count, conflict_count, missing_count},
        }
    Sections with no facts are omitted. `missing` lists only genuinely-absent
    core fields.
    """
    documents = [_document_row(e) for e in profile.extracts]
    filename_by_id = {e.document_id: e.original_filename for e in profile.extracts}

    all_facts = [f for e in profile.extracts for f in e.facts]
    sections, conflict_count = _build_sections(all_facts, filename_by_id)

    present_keys = {f.key for f in all_facts}
    missing = [
        {"key": key, "label": key_label(key)}
        for key in CORE_FIELDS
        if key not in present_keys
    ]

    return {
        "workspace_id": profile.workspace_id,
        "documents": documents,
        "sections": sections,
        "missing": missing,
        "stats": {
            "document_count": len(documents),
            "fact_count": len(all_facts),
            "conflict_count": conflict_count,
            "missing_count": len(missing),
        },
    }


def _document_row(extract) -> dict[str, Any]:
    """One uploaded document's card: name, detected type, and extraction status."""
    return {
        "document_id": extract.document_id,
        "filename": extract.original_filename,
        "source_type": extract.source_type,
        "document_type": source_type_label(extract.source_type),
        "fact_count": len(extract.facts),
        "page_count": extract.page_count,
        "status": _document_status(extract),
    }


def _document_status(extract) -> str:
    """Machine status the UI turns into friendly text.

    'extracted'    — text was read and facts were found.
    'no_information'— a recognised document type, but nothing we needed was in it.
    'unrecognised' — text could not be read, or the type was not recognised and
                     no facts came out (an unreadable .doc, an image-only scan).
    """
    if extract.facts:
        return "extracted"
    if extract.source_type not in ("unknown", "generic"):
        return "no_information"
    return "unrecognised"


def _build_sections(
    facts: list[Fact], filename_by_id: dict[str, str]
) -> tuple[list[dict[str, Any]], int]:
    """Group facts into ordered sections; return (sections, conflict_count).

    Within a section, facts are grouped by vocabulary key. Each key becomes one
    field carrying every distinct value found, ordered by confidence. A field is
    a conflict when it is a singular key (see CONFLICTING_KEYS) yet the documents
    supplied more than one distinct value for it.
    """
    # section id -> key -> list[Fact]
    grouped: dict[str, dict[str, list[Fact]]] = {sid: {} for sid, _ in _SECTIONS}
    for fact in facts:
        section_id = _section_for(fact)
        grouped[section_id].setdefault(fact.key, []).append(fact)

    sections: list[dict[str, Any]] = []
    conflict_count = 0

    for section_id, label in _SECTIONS:
        by_key = grouped[section_id]
        if not by_key:
            continue

        fields: list[dict[str, Any]] = []
        for key in sorted(by_key, key=_field_order):
            values = _distinct_values(by_key[key], filename_by_id)
            is_conflict = key in CONFLICTING_KEYS and len(values) > 1
            if is_conflict:
                conflict_count += 1
            fields.append({
                "key": key,
                "label": key_label(key),
                "conflict": is_conflict,
                "values": values,
            })

        sections.append({"id": section_id, "label": label, "fields": fields})

    return sections, conflict_count


def _field_order(key: str) -> tuple[int, str]:
    """Stable field ordering inside a section: names first, then the rest."""
    priority = 0 if key.endswith(".name") or key == "invention.title" else 1
    return (priority, key)


def _distinct_values(
    facts: list[Fact], filename_by_id: dict[str, str]
) -> list[dict[str, Any]]:
    """Distinct values for one key, each with full provenance, confidence-first.

    Two documents asserting the same value collapse to a single row that keeps
    the higher confidence — the agreement is not noise the user must reconcile.
    Two documents asserting different values stay as separate rows, which is
    exactly what a conflict looks like once rendered.
    """
    best_by_value: dict[str, Fact] = {}
    for fact in facts:
        marker = str(fact.value)
        current = best_by_value.get(marker)
        if current is None or fact.confidence > current.confidence:
            best_by_value[marker] = fact

    ordered = sorted(best_by_value.values(), key=lambda f: -f.confidence)
    return [_value_row(f, filename_by_id) for f in ordered]


def _value_row(fact: Fact, filename_by_id: dict[str, str]) -> dict[str, Any]:
    return {
        "value": fact.value,
        "confidence": fact.confidence,
        "page": fact.page,
        "source_document": filename_by_id.get(fact.document_id, fact.document_id),
        "source_type": fact.source_type,
        "source_type_label": source_type_label(fact.source_type),
    }
