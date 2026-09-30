"""Score stock extraction against ai/evaluation/extraction_golden_v1.json.

Uses Gemini when configured, otherwise the demo rule parser (the output says which).
Run: cd services/api && uv run python -m scripts.eval_extraction
"""
import json

from app.capture.extraction import extract_stock
from app.config import REPO_ROOT
from app.store import load_generator

GOLDEN = REPO_ROOT / "ai" / "evaluation" / "extraction_golden_v1.json"


def evaluate() -> dict:
    meds = load_generator().generate().medicines
    cases = json.loads(GOLDEN.read_text())["cases"]
    exact, item_hits, item_total, results = 0, 0, 0, []
    model = None
    for c in cases:
        res, prov = extract_stock(c["text"], c["language"], meds)
        model = f"{prov['model_name']} ({prov['mode']})"
        got = {i.drug_code: i.quantity for i in res.items if i.drug_code}
        exp = c["expected"]
        hits = sum(1 for k, v in exp.items() if k in got and got[k] == v)
        item_hits += hits
        item_total += len(exp)
        ok = got == exp and len(res.unrecognised) == c["unrecognised"]
        exact += ok
        results.append({"id": c["id"], "exact": ok, "got": got, "expected": exp, "unrecognised": res.unrecognised})
    return {"model": model, "cases": len(cases), "exact_match": exact,
            "item_accuracy": round(item_hits / item_total, 3), "results": results}


if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=1))
