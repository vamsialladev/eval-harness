"""Judge vs human labels: agreement, Cohen's kappa, precision and recall for "fail", confusion matrix.

A judge metric (dimension) is trusted only when its kappa is at least 0.6 (TRUST_KAPPA); an untrusted metric is
shown as "not trusted" and is never a gate. "Fail" is the positive class: precision = of the replies the judge
failed, how many the human failed; recall = of the replies the human failed, how many the judge caught.
"""

from hoteleval.rubric import DIMENSIONS
from hoteleval.stats import cohen_kappa, wilson

TRUST_KAPPA = 0.6


def confusion(pairs: list[tuple[str, str]]) -> dict:
    """pairs: (human, judge) labels, each 'pass' or 'fail'."""
    tp = sum(h == "fail" and j == "fail" for h, j in pairs)
    fp = sum(h == "pass" and j == "fail" for h, j in pairs)
    fn = sum(h == "fail" and j == "pass" for h, j in pairs)
    tn = sum(h == "pass" and j == "pass" for h, j in pairs)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def agreement_stats(pairs: list[tuple[str, str]]) -> dict:
    n = len(pairs)
    if not n:
        return {
            "n": 0,
            "agreement": None,
            "agreement_ci": None,
            "kappa": None,
            "precision_fail": None,
            "recall_fail": None,
            "confusion": confusion([]),
            "trusted": False,
        }
    c = confusion(pairs)
    agree = (c["tp"] + c["tn"]) / n
    kappa = cohen_kappa([h for h, _ in pairs], [j for _, j in pairs])
    ci = wilson(c["tp"] + c["tn"], n)
    return {
        "n": n,
        "agreement": agree,
        "agreement_ci": list(ci) if ci else None,
        "kappa": kappa,
        "precision_fail": c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else None,
        "recall_fail": c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None,
        "human_fail": c["tp"] + c["fn"],
        "judge_fail": c["tp"] + c["fp"],
        "confusion": c,
        "trusted": kappa is not None and kappa >= TRUST_KAPPA,
    }


def calibrate(items: list[dict], labels: dict, verdicts: dict) -> dict:
    """items: calibration items; labels: item_id -> human label row; verdicts: item_id -> judge verdicts (all three
    dimensions). Each item contributes the one dimension the human labelled."""
    rows = []
    for item in items:
        human = labels.get(item["item_id"])
        judged = verdicts.get(item["item_id"])
        if not human or not judged:
            continue
        j = judged[item["dimension"]]
        rows.append(
            {
                "item_id": item["item_id"],
                "project": item["project"],
                "dimension": item["dimension"],
                "human": human["label"],
                "human_reason": human.get("reason", ""),
                "judge": j["verdict"],
                "judge_reason": j["reason"],
            }
        )
    per_dim = {d: agreement_stats([(r["human"], r["judge"]) for r in rows if r["dimension"] == d]) for d in DIMENSIONS}
    per_project = {
        p: agreement_stats([(r["human"], r["judge"]) for r in rows if r["project"] == p])
        for p in sorted({r["project"] for r in rows})
    }
    return {
        "overall": agreement_stats([(r["human"], r["judge"]) for r in rows]),
        "per_dimension": per_dim,
        "per_project": per_project,
        "trusted": {d: per_dim[d]["trusted"] for d in DIMENSIONS},
        "rows": rows,
    }
