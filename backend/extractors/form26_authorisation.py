"""Form 26 extractor — Authorisation of a Patent Agent (Power of Attorney).

Second-highest unserved demand (32 citations), and unusually concentrated: 30 of
the 32 are `agent.name`, which appears on 29 of the 34 forms because almost every
IPO form is signed by the agent. One extracted value therefore pre-fills a field
on nearly every form in the library.

Keys served:
    agent.name       (30)
    agent.inpaNumber  (2)
"""

from __future__ import annotations

from extractors.base import PatternExtractor

# Honorifics printed before the agent's name on the authorisation line. Consumed
# by the pattern rather than captured, so the value is the bare name.
_HONORIFIC = (
    r"(?:M/s\.?\s*)?"
    r"(?:Shri\s*/\s*(?:Smt|Ms)\.?\s*|Shri\s+|Smt\.?\s+|Mr\.?\s+|Mrs\.?\s+|Ms\.?\s+|Dr\.?\s+)?"
)


class Form26AuthorisationExtractor(PatternExtractor):
    """Extracts the authorised agent's identity from a Form 26."""

    EXTRACTOR_VERSION = "form26_authorisation@1"
    SOURCE_TYPE = "form26_authorisation"

    PATTERNS = [
        (
            "agent.name",
            [
                r"Name\s+of\s+(?:the\s+)?(?:authori[sz]ed\s+)?(?:patent\s+)?agent\s*[:\-]\s*"
                r"([^\n\r]{3,100})",
                r"(?:^|\n)\s*(?:Patent\s+)?Agent(?:'s)?\s+Name\s*[:\-]\s*([^\n\r]{3,100})",
                # The operative sentence of the form itself. Note `authori[sz]e`,
                # not `authoris[sz]e` — the latter spells "authorisse"/"authorisze"
                # and silently matches nothing on either spelling.
                r"hereby\s+authori[sz]e\s+" + _HONORIFIC + r"([A-Za-z][^,\n\r]{2,99})",
            ],
            0.85,
        ),
        (
            "agent.inpaNumber",
            [
                # Printed as IN/PA-1234, IN/PA 1234, INPA/1234, IN-PA No. 1234 …
                r"IN\s*[/\-]?\s*PA\s*[-–/]?\s*(?:No\.?)?\s*[:\-]?\s*(\d{1,6})",
                r"(?:Registration|Regn\.?)\s+No\.?\s*(?:of\s+(?:the\s+)?agent)?\s*[:\-]\s*"
                r"(?:IN\s*[/\-]?\s*PA\s*[-–/]?\s*)?(\d{1,6})",
            ],
            0.85,
        ),
    ]

    ACROFORM_MAP = {
        "AgentName": ("agent.name", 0.95),
        "NameOfAgent": ("agent.name", 0.95),
        "INPA": ("agent.inpaNumber", 0.95),
        "AgentRegistration": ("agent.inpaNumber", 0.90),
    }
