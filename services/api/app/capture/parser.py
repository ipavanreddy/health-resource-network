"""Deterministic stock-report parser used in demo mode (and as a fallback if Gemini fails).

Matches medicine master names / local names (English, Hindi, Tamil) and the quantity that follows each
mention. It never invents quantities: an item without a stated quantity gets quantity=None.
"""
import re

from app.ai.schemas import ExtractedItem, StockExtraction

FINISHED = ["finished", "nil", "none left", "out of stock", "stocked out", "stock out", "zero", "khatam",
            "खत्म", "ख़त्म", "समाप्त", "नहीं बचा", "தீர்ந்துவிட்டது", "தீர்ந்தது", "காலி", "இல்லை"]
SENTENCE = re.compile(r"[.;।\n]+")
NUMBER = re.compile(r"\d+(?:\.\d+)?")
LETTERS = re.compile(r"[^\W\d_]{3,}")


def _is_latin(s: str) -> bool:
    return all(ord(ch) < 128 for ch in s)


def _alias_pattern(alias: str) -> re.Pattern:
    esc = re.escape(alias.lower())
    if _is_latin(alias):
        return re.compile(rf"(?<![a-z0-9]){esc}(?![a-z])")
    return re.compile(esc)


def _find_mentions(text: str, medicines: list[dict]) -> list[tuple[int, int, dict, str]]:
    low = text.lower()
    cands = []
    for m in medicines:
        aliases = {m["name"].lower(), *[a.lower() for a in m.get("local_names", [])]}
        for a in aliases:
            for mt in _alias_pattern(a).finditer(low):
                cands.append((mt.start(), mt.end(), m, a))
    cands.sort(key=lambda c: (-(c[1] - c[0]), c[0]))  # longest alias first
    taken: list[tuple[int, int, dict, str]] = []
    for c in cands:
        if all(c[1] <= t[0] or c[0] >= t[1] for t in taken):
            taken.append(c)
    return sorted(taken, key=lambda c: c[0])


def _quantity(part: str, strength_number: float | None, first_part: bool) -> tuple[float | None, float]:
    """Returns (quantity, confidence penalty multiplier)."""
    low = part.lower()
    nums = [float(n) for n in NUMBER.findall(part)]
    if first_part and strength_number is not None and nums and nums[0] == strength_number:
        if len(nums) > 1:
            nums = nums[1:]
        else:
            return nums[0], 0.6  # "Paracetamol 500": strength or quantity? flag lower confidence
    finished = any(w in low for w in FINISHED)
    if finished and len(nums) == 1 and part.strip().startswith(NUMBER.findall(part)[0]):
        # "Dolo 650 strips none left": the only number sits right after the name (a strength), and the
        # sentence says the medicine is finished.
        return 0.0, 0.7
    if nums:
        return nums[0], 1.0
    if finished:
        return 0.0, 1.0
    return None, 1.0


def parse_stock_text(text: str, medicines: list[dict]) -> StockExtraction:
    text = re.sub(r"(\d),(\d{3})\b", r"\1\2", text or "")
    mentions = _find_mentions(text, medicines)
    items: dict[str, ExtractedItem] = {}
    unrecognised: list[str] = []
    lead = text[: mentions[0][0]] if mentions else text
    for seg in SENTENCE.split(lead):
        if NUMBER.search(seg) and LETTERS.search(seg):
            unrecognised.append(seg.strip(" ,"))
    for k, (start, end, med, alias) in enumerate(mentions):
        span_end = mentions[k + 1][0] if k + 1 < len(mentions) else len(text)
        span = text[end:span_end]
        parts = SENTENCE.split(span)
        # Only the mention's own sentence may carry its quantity: never borrow a number from another sentence.
        qty, penalty = _quantity(parts[0], med.get("strength_number"), True)
        for part in parts[1:]:
            if NUMBER.search(part) and LETTERS.search(part):
                unrecognised.append(part.strip(" ,"))
        exact = alias == med["name"].lower()
        items[med["drug_code"]] = ExtractedItem(
            spoken_name=text[start:end], drug_code=med["drug_code"], quantity=qty, unit=med["unit"],
            match_confidence=round((0.95 if exact else 0.9) * penalty, 2),
        )
    return StockExtraction(items=list(items.values()), unrecognised=unrecognised, requires_confirmation=True)
