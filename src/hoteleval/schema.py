"""One case schema for both projects. Pure data and validation, no I/O.

A case keeps the project's own labelled fields in `expected` under their original names (so importing changes
nothing about what a case means) and adds the fields every project shares: split, behaviour, tags and origin.
"""

from dataclasses import asdict, dataclass, field

PROJECTS = {
    "hotel-ops-assistant": {"short": "p1", "name": "Project 1: Hotel Operations Knowledge Assistant"},
    "guest-request-agent": {"short": "p2", "name": "Project 2: Guest Request Agent"},
}
SHORT = {v["short"]: k for k, v in PROJECTS.items()}
SPLITS = ("dev", "held-out", "visitor")
BEHAVIOURS = ("answer", "refuse", "escalate", "greeting", "off_topic")
PROPERTIES = ("beach-resort", "mountain-lodge")
ADDED = "added in Project 3"


class CaseError(ValueError):
    """A case that doesn't match the schema."""


@dataclass
class Case:
    id: str
    project: str
    property: str
    category: str
    split: str
    input: dict
    expected: dict
    categories: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    origin: str = ""
    notes: str = ""

    @property
    def uid(self) -> str:
        return f"{PROJECTS[self.project]['short']}/{self.id}"

    @property
    def behaviour(self) -> str:
        return self.expected["behaviour"]

    @property
    def added(self) -> bool:
        return self.origin.startswith("added in Project")  # Project 3 or Project 4

    def text(self) -> str:
        """What the user wrote: the question (Project 1) or the email body (Project 2)."""
        if "question" in self.input:
            return self.input["question"]
        email = self.input.get("email") or {}
        return "\n".join(p for p in (email.get("subject", ""), email.get("body", "")) if p)

    def native(self) -> dict:
        """The case as the project's own metric code expects it."""
        base = {"id": self.id, "property": self.property, "category": self.category, "categories": self.categories}
        return {**base, **self.input, **{k: v for k, v in self.expected.items() if k != "behaviour"}}

    def to_dict(self) -> dict:
        return asdict(self)


def validate(data: dict) -> Case:
    """Build a Case from a dict, raising CaseError with a short reason when a field is wrong."""
    required = ("id", "project", "property", "category", "split", "input", "expected")
    missing = [k for k in required if k not in data]
    if missing:
        raise CaseError(f"{data.get('id', '?')}: missing {', '.join(missing)}")
    if data["project"] not in PROJECTS:
        raise CaseError(f"{data['id']}: unknown project {data['project']!r}")
    if data["split"] not in SPLITS:
        raise CaseError(f"{data['id']}: split must be one of {', '.join(SPLITS)}")
    if data["property"] not in PROPERTIES:
        raise CaseError(f"{data['id']}: unknown property {data['property']!r}")
    behaviour = (data["expected"] or {}).get("behaviour")
    if behaviour not in BEHAVIOURS:
        raise CaseError(f"{data['id']}: expected.behaviour must be one of {', '.join(BEHAVIOURS)}")
    inp = data["input"] or {}
    if not (inp.get("question") or (inp.get("email") or {}).get("body")):
        raise CaseError(f"{data['id']}: input needs a question or an email body")
    known = {f for f in Case.__dataclass_fields__}
    return Case(**{k: v for k, v in data.items() if k in known})


def check_unique(cases: list[Case]) -> None:
    seen = set()
    for c in cases:
        if c.uid in seen:
            raise CaseError(f"duplicate case {c.uid}")
        seen.add(c.uid)
