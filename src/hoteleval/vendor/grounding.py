"""Numeric grounding: every number in an answer should come from a cited source (or the question).

Used by the eval (as a metric) and by the app at answer time (as a visible warning), so a
price or time that appears nowhere in the cited passages is caught before staff quote it.
"""

import re

CITATION = re.compile(r"\[\d+\]")
NUMBER = re.compile(r"\d[\d,]*(?::\d{2})?")


def numbers_in(text: str) -> set[str]:
    """Numbers normalized so '$1,200' -> '1200' and '2:00' -> '2' (matches '2 PM')."""
    text = CITATION.sub(" ", text)
    out = set()
    for raw in NUMBER.findall(text):
        n = raw.replace(",", "")
        if n.endswith(":00"):
            n = n[:-3]
        out.add(n)
    return out


def ungrounded_numbers(answer: str, cited_chunks: list, question: str = "") -> list[str]:
    """Numbers in the answer that appear in neither the cited passages nor the question.

    Numbers from the question are allowed because a correct answer may repeat them
    ("No, a $300 refund is over the $200 limit"). Wrong numbers *stated* in a question are
    handled by the prompt and by the wrong-premise eval cases, not by this check.
    """
    allowed = numbers_in(" ".join(c["text"] for c in cited_chunks)) | numbers_in(question)
    return sorted(numbers_in(answer) - allowed)
