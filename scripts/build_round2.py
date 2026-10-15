"""Calibration round 2: a second blind set of 30 items with real failures in it (decision 20).

    python scripts/build_round2.py      # writes labels/items-round2.jsonl (seeded, same result every time)

Round 1 (40 items) held no human failures, so kappa couldn't say anything. Round 2 mixes:
- 15 real replies from the harness re-runs (run 1) that the v2 judge failed, from cases not used in round 1. The judge
  gives pass/fail only, so "borderline" isn't available; these are judge fails. The item's quality is the one the
  judge failed.
- 15 synthetic degraded variants of other real replies the judge passed, written by hand (not by a model): 3 robotic
  and 3 cold (tone), 3 rambling and 3 full of internal jargon (clarity), 3 missing one of the guest's requests
  (completeness). Each keeps the facts of the original.
Items are shuffled with a fixed seed. Which items are degraded is recorded only in the `origin` and `degradation`
fields, which the labeling page never shows.
"""

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from hoteleval import store  # noqa: E402
from hoteleval.cases import by_id  # noqa: E402
from hoteleval.labeling import input_text, reply_text  # noqa: E402

RUNS = {"hotel-ops-assistant": "p1-harness-2026-10-14", "guest-request-agent": "p2-harness-2026-10-14"}
OUT = ROOT / "labels" / "items-round2.jsonl"
SEED = 2027

# Real replies the v2 judge failed on the full re-runs, and the quality it failed them on.
REAL = [
    ("hotel-ops-assistant", "a12", "tone"),
    ("hotel-ops-assistant", "q05", "tone"),
    ("hotel-ops-assistant", "a04", "clarity"),
    ("hotel-ops-assistant", "q06", "clarity"),
    ("hotel-ops-assistant", "q23", "clarity"),
    ("hotel-ops-assistant", "q32", "clarity"),
    ("hotel-ops-assistant", "v10", "clarity"),
    ("hotel-ops-assistant", "v18", "clarity"),
    ("hotel-ops-assistant", "v30", "clarity"),
    ("guest-request-agent", "E05", "completeness"),
    ("guest-request-agent", "E08", "clarity"),
    ("guest-request-agent", "E19", "clarity"),
    ("guest-request-agent", "H05", "clarity"),
    ("guest-request-agent", "b02", "clarity"),
    ("guest-request-agent", "b06", "clarity"),
]

P1, P2 = "hotel-ops-assistant", "guest-request-agent"
# (project, case, quality, degradation, degraded reply). Facts are kept from the original reply.
DEGRADED = [
    (
        P2,
        "b05",
        "tone",
        "robotic",
        "GUEST INQUIRY RESPONSE.\n\nRe: pet policy. Status: permitted. Dog weight limit: 40 lbs. Maximum dogs per room: 2. "
        "Your dog (25 lb): within limit. Pet fee: $75 per stay, non-refundable [P1]. Restricted areas: pool, restaurant [P1]. "
        "Old review: superseded.\n\nTo proceed, submit dates and room preference. Total to be confirmed by team.\n\nEnd of response.\n"
        "Guest Services, Beach Resort",
    ),
    (
        P2,
        "H04",
        "tone",
        "robotic",
        "Daniel,\n\nRequest received. Request type: add guest (4th) to booking ML-2015, Cabin C2, Fri 13 to Mon 16 Nov. "
        "Request status: forwarded to reservations. Approval required: manager. Extra-person charge: not confirmed.\n\n"
        "Query 2: fire pit hours. Answer: 6:00 PM to 10:00 PM [P1]. Query 3: s'mores kits. Answer: yes, $12, front desk [P1].\n\n"
        "Guest Services, Mountain Lodge",
    ),
    (
        P2,
        "H07",
        "tone",
        "robotic",
        "Ben,\n\nBooking BR-1055 located. Room type: Standard King. Dates: Fri 27 Nov to Sun 29 Nov 2026. Rate: Flexible.\n\n"
        "Policy check: cancellations at least 48 hours before arrival are free of charge [P1]. Result: qualifies. "
        "Action taken: cancellation request submitted for manager review. Booking status: active until confirmation is "
        "issued.\n\nGuest Services, Beach Resort",
    ),
    (
        P2,
        "E22",
        "tone",
        "cold",
        "Mr. Hale,\n\nWe have received your complaint about check-in on Friday. A manager will contact you when one is "
        "available.\n\nGuest Services, Mountain Lodge",
    ),
    (
        P2,
        "H01",
        "tone",
        "cold",
        "Ms. Walsh,\n\nWe note your report that your son touched the cabin fireplace glass. Guests are responsible for "
        "supervising children near the fireplace. A manager will contact you, and the fireplace will be inspected.\n\n"
        "Guest Services, Mountain Lodge",
    ),
    (
        P2,
        "E27",
        "tone",
        "cold",
        "Zoe,\n\nNoise from other guests is not something we control. If you want a different room, these are available "
        "for Mon 2 Nov and Tue 3 Nov: Standard Queen $189 per night, Suite $369 per night, Cabin $249 per night. "
        "Availability is not a reservation. The front desk will call you, and a manager will review the request.\n\n"
        "Guest Services, Mountain Lodge",
    ),
    (
        P2,
        "E15",
        "clarity",
        "rambling",
        "Hello James,\n\nThank you so much for reaching out to us here at the Beach Resort, it's always lovely to hear from "
        "our guests, and of course we know how important it is to stay connected these days, whether for work or for "
        "sharing photos of the beach with friends and family back home, which so many of our guests enjoy doing. On the "
        "subject of the internet, which we think is really what you were asking about, you'll be glad to know that it is "
        "something that comes along with the resort fee, which as it happens is $35 per night plus tax [P3], and that fee "
        "also covers a few other things too. As for actually getting online, the network you'll want to look for is "
        'called "BeachResort-Guest", and in terms of the password, that is something you will find printed on the '
        "sleeve of your key card, so do keep the sleeve handy [P1]. And in case you were wondering where it works, it "
        "covers all the rooms as well as the rooftop pool and the beach chair area, so you really can stay connected "
        "almost anywhere [P1].\n\nGuest Services, Beach Resort",
    ),
    (
        P1,
        "v32",
        "clarity",
        "rambling",
        "So, to answer this one properly it helps to look at a few things together, because weddings involve a lot of "
        "moving parts and the documents touch on several of them in different places. There is a garden lawn and there "
        "is also an indoor event room, and the lawn is the larger of the two, holding up to 150 guests, while the indoor "
        "room is smaller and holds up to 60 [2], which matters depending on the size of the party. Then there is the "
        "question of confirming a date, where a 30% deposit comes into it, and that deposit is non-refundable [2]. Room "
        "blocks are also a factor, needing at least 10 rooms and being released 30 days before arrival [2]. Pricing, "
        "though, is not something quoted at the desk; that goes to the Events Manager [2]. And yes, to come back to the "
        "actual question, Mountain Lodge does host weddings.",
    ),
    (
        P1,
        "q18",
        "clarity",
        "rambling",
        "There are a number of documents that touch on cancellations in one way or another, and it's worth noting that "
        "spa bookings have their own rule where cancelling within 12 hours costs 50% of the treatment price [2], which "
        "may or may not be what is being asked about. Going back to rooms, the terms I could find are brand-wide rather "
        "than specific to Beach Resort, and they depend on the rate: on a non-refundable rate there are no refunds or "
        "date changes unless the General Manager approves [1], whereas flexible rates are different, since with those, "
        "cancelling up to 48 hours before arrival is free, and cancelling later than that, meaning inside the 48 hours, "
        "is charged at one night plus tax [1]. I didn't see a Beach Resort room policy on its own, so a manager would be "
        "the one to check with on that, ideally before quoting anything.",
    ),
    (
        P2,
        "E02",
        "clarity",
        "jargon",
        "Dear James,\n\nPer PROP_POLICY/BR/PARKING (src: policies.md, chunk P1), parking = VALET_ONLY @ $45/nt incl. "
        "in/out [P1]. EV_CHG x2, FCFS [P1].\n\nRes BR-1043 (RT: STD_KING, RM 205, ARR 13NOV26, DEP 15NOV26, LOS 2) -> "
        "parking applies x2 nts. Total TBC by FO team per PMS folio.\n\nWarm regards,\nGuest Services, Beach Resort",
    ),
    (
        P1,
        "v13",
        "clarity",
        "jargon",
        "Per BR policies.md §Airport Transfers (chunk 1, BM25 rank 1): MIA only. Sedan $65 1-way (cap 3 pax), SUV $95 "
        "1-way (cap 6 pax), lead time >= 24h [1]. FLL = not supported; route guest to TNC/taxi [1]. Shared shuttle: no "
        "source hit (escalate per SOP REFUSED rule).",
    ),
    (
        P1,
        "q50",
        "clarity",
        "jargon",
        "NRF rate -> no refund/date change; exception requires GM approval [1] (rule: nonrefundable_exception). FD agent "
        "auth limit = courtesy credit <= $50 w/o approval; > $200 = MOD [2] (rule: refund_over_limit). NRF + courtesy "
        "credit interaction: no source coverage; escalate to MOD before offering.",
    ),
    (
        P2,
        "E26",
        "completeness",
        "missing request",
        "Hello Jack,\n\nThank you for your email, and we look forward to welcoming you on 13 November for your stay "
        "(booking ML-2025).\n\nGuided hike: Our guided hikes run Saturdays at 9:00 AM for $20 per person, and bookings "
        "are made at the front desk by Friday evening [P1]. We have sent a request to our front desk team to sign you up "
        "for Saturday, 14 November at 9:00 AM. They will confirm once it is booked.\n\nWarm regards,\nGuest Services, "
        "Mountain Lodge",
    ),
    (
        P2,
        "E20",
        "completeness",
        "missing request",
        "Hi Noah,\n\nThank you for letting us know. We've asked our housekeeping team to deliver extra towels and a crib to "
        "Room 208. Extra towels are free and delivered within 20 minutes [P2], and cribs are free [P2].\n\nIf anything "
        "else is needed during your stay, just reply to this email.\n\nWarm regards,\nGuest Services, Beach Resort",
    ),
    (
        P2,
        "V07",
        "completeness",
        "missing request",
        "Hello,\n\nThank you for your message. Here are the details for Mountain Lodge:\n\nAirport shuttle: The shuttle to "
        "and from Asheville Regional Airport (AVL) is $35 per person one way. It runs hourly on the hour from 7:00 AM to "
        "9:00 PM, and should be booked at least 12 hours ahead [P1].\n\nIf you have a booking with us, reply from the "
        "email address used to book and we can help with the reservation details.\n\nWarm regards,\nGuest Services, "
        "Mountain Lodge",
    ),
]


def run1_outputs(project: str) -> dict:
    outputs, _ = store.load_run(RUNS[project])
    return {o["case_id"]: o for o in outputs if o["run"] == 1}


def build() -> list[dict]:
    outs = {p: run1_outputs(p) for p in RUNS}
    cases = {p: by_id(p) for p in RUNS}
    items = []
    for project, cid, dim in REAL:
        o = outs[project][cid]
        items.append(
            {
                "project": project,
                "dimension": dim,
                "run_id": RUNS[project],
                "case_id": cid,
                "run": 1,
                "property": cases[project][cid].property,
                "input": input_text(cases[project][cid], o),
                "reply": reply_text(o),
                "origin": "real reply (judge failed on a full re-run)",
                "degradation": None,
            }
        )
    for project, cid, dim, kind, text in DEGRADED:
        o = outs[project][cid]
        items.append(
            {
                "project": project,
                "dimension": dim,
                "run_id": RUNS[project],
                "case_id": cid,
                "run": 1,
                "property": cases[project][cid].property,
                "input": input_text(cases[project][cid], o),
                "reply": text,
                "original_reply": reply_text(o),
                "origin": "synthetic degraded variant",
                "degradation": kind,
            }
        )
    random.Random(SEED).shuffle(items)
    for n, item in enumerate(items, 1):
        item["item_id"] = f"r2-{n:02d}"
    return items


def main() -> int:
    items = build()
    store.write_jsonl(OUT, items)
    print(f"wrote {len(items)} items to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
