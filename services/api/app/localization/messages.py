"""Localised confirmation / alert / notification text (English, Hindi, Tamil).

Templates are pre-translated so the core journey works without the Translation API. Medicine names
are always shown in their standard form alongside the local name staff used (PRD §17).
"""
SUPPORTED = ("en", "hi", "ta")

UNITS = {
    "hi": {"tablet": "गोलियां", "sachet": "पैकेट", "capsule": "कैप्सूल", "bottle": "बोतल"},
    "ta": {"tablet": "மாத்திரைகள்", "sachet": "பாக்கெட்", "capsule": "கேப்ஸ்யூல்", "bottle": "பாட்டில்"},
}

T = {
    "confirm_intro": {
        "en": "Please check the stock I understood:",
        "hi": "कृपया जांचें, मैंने यह स्टॉक समझा:",
        "ta": "நான் புரிந்துகொண்ட இருப்பை சரிபார்க்கவும்:",
    },
    "confirm_outro": {
        "en": "Tap Confirm to save, or correct any line first.",
        "hi": "सहेजने के लिए पुष्टि करें दबाएं, या पहले कोई पंक्ति सुधारें।",
        "ta": "சேமிக்க உறுதிசெய் என்பதை அழுத்தவும், அல்லது முதலில் திருத்தவும்.",
    },
    "finished": {"en": "finished (0)", "hi": "खत्म (0)", "ta": "தீர்ந்துவிட்டது (0)"},
    "missing_qty": {"en": "quantity not heard, please enter", "hi": "मात्रा सुनाई नहीं दी, कृपया भरें",
                    "ta": "அளவு கேட்கவில்லை, தயவுசெய்து உள்ளிடவும்"},
    "unrecognised": {"en": "Not recognised, please review:", "hi": "पहचान नहीं हुई, कृपया जांचें:",
                     "ta": "அடையாளம் காணவில்லை, சரிபார்க்கவும்:"},
    "saved": {"en": "Saved. Stock updated for {n} medicines.", "hi": "सहेजा गया। {n} दवाओं का स्टॉक अपडेट हुआ।",
              "ta": "சேமிக்கப்பட்டது. {n} மருந்துகளின் இருப்பு புதுப்பிக்கப்பட்டது."},
    "transfer_approved": {
        "en": "Transfer approved: {qty} {unit} {medicine} from {from_name} to {to_name}.",
        "hi": "स्थानांतरण स्वीकृत: {qty} {unit} {medicine}, {from_name} से {to_name}।",
        "ta": "இடமாற்றம் அங்கீகரிக்கப்பட்டது: {qty} {unit} {medicine}, {from_name} இலிருந்து {to_name}.",
    },
    "transfer_dispatched": {
        "en": "Dispatched: {qty} {unit} {medicine} from {from_name} to {to_name}. Please confirm receipt.",
        "hi": "भेजा गया: {qty} {unit} {medicine}, {from_name} से {to_name}। कृपया प्राप्ति की पुष्टि करें।",
        "ta": "அனுப்பப்பட்டது: {qty} {unit} {medicine}, {from_name} இலிருந்து {to_name}. பெறுதலை உறுதிசெய்யவும்.",
    },
    "transfer_received": {
        "en": "Received: {qty} {unit} {medicine} at {to_name}.",
        "hi": "प्राप्त हुआ: {qty} {unit} {medicine}, {to_name} में।",
        "ta": "பெறப்பட்டது: {qty} {unit} {medicine}, {to_name}.",
    },
    "alert_stocked_out": {
        "en": "Stocked out: {medicines}.", "hi": "स्टॉक खत्म: {medicines}।", "ta": "இருப்பு தீர்ந்தது: {medicines}.",
    },
    "alert_risk": {
        "en": "High stock-out risk before next supply: {medicines}.",
        "hi": "अगली आपूर्ति से पहले स्टॉक खत्म होने का उच्च जोखिम: {medicines}।",
        "ta": "அடுத்த விநியோகத்திற்கு முன் இருப்பு தீரும் அபாயம் அதிகம்: {medicines}.",
    },
    "alert_surge": {
        "en": "{label}: {medicines} use {ratio}x normal across {n} facilities in {district}. "
              "Possible signal for verification, not a confirmed outbreak.",
        "hi": "{label}: {district} की {n} सुविधाओं में {medicines} का उपयोग सामान्य से {ratio} गुना। "
              "यह सत्यापन हेतु संभावित संकेत है, पुष्ट प्रकोप नहीं।",
        "ta": "{label}: {district} இல் {n} மையங்களில் {medicines} பயன்பாடு வழக்கத்தை விட {ratio} மடங்கு. "
              "இது சரிபார்க்க வேண்டிய சாத்தியமான அறிகுறி, உறுதிப்படுத்தப்பட்ட பரவல் அல்ல.",
    },
}


def lang(code: str | None) -> str:
    return code if code in SUPPORTED else "en"


def t(key: str, language: str, **kw) -> str:
    return T[key][lang(language)].format(**kw)


def unit_word(unit: str, language: str) -> str:
    return UNITS.get(lang(language), {}).get(unit, unit + "s")


def medicine_label(med: dict, spoken: str | None = None) -> str:
    std = f"{med['name']} {med['strength']}"
    if spoken and spoken.lower() not in std.lower():
        return f"{std} ({spoken})"
    return std


def confirmation_text(items: list[dict], unrecognised: list[str], medicines: dict[str, dict], language: str) -> str:
    language = lang(language)
    lines = [t("confirm_intro", language)]
    for it in items:
        med = medicines.get(it.get("drug_code") or "")
        if not med:
            continue
        label = medicine_label(med, it.get("spoken_name"))
        q = it.get("quantity")
        if q is None:
            lines.append(f"• {label}: {t('missing_qty', language)}")
        elif q == 0:
            lines.append(f"• {label}: {t('finished', language)}")
        else:
            lines.append(f"• {label}: {q:,.0f} {unit_word(med['unit'], language)}")
    if unrecognised:
        lines.append(f"{t('unrecognised', language)} {', '.join(unrecognised)}")
    lines.append(t("confirm_outro", language))
    return "\n".join(lines)
