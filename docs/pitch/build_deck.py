"""Generate the PHC Pulse pitch deck (docs/pitch/PHC_Pulse_pitch.pptx).

    uv run --with python-pptx python docs/pitch/build_deck.py

11 slides structured around the hackathon evaluation criteria (AI / technical 25%, problem-solution fit 20%,
depth & reach across India 20%, deployability & scalability 20%, impact 15%) plus cross-border portability.
Numbers quoted from the demo come from the synthetic dataset and are labelled as such.
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "PHC_Pulse_pitch.pptx"

NAVY = RGBColor(0x0F, 0x1E, 0x3C)
TEAL = RGBColor(0x0B, 0x7A, 0x75)
TEAL_LIGHT = RGBColor(0xE3, 0xF3, 0xF1)
AMBER = RGBColor(0xB4, 0x5B, 0x09)
AMBER_LIGHT = RGBColor(0xFD, 0xF3, 0xE3)
RED = RGBColor(0xB9, 0x1C, 0x1C)
GREY = RGBColor(0x5B, 0x64, 0x72)
LIGHT = RGBColor(0xF3, 0xF5, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

W, H = Inches(13.333), Inches(7.5)
LIVE = "health-resource-network-phc-web-847963771142.asia-south1.run.app"


def text(slide, x, y, w, h, runs, size=18, color=NAVY, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=1.1):
    """Add a text box. `runs` is a string or a list of paragraphs; a paragraph is a string or [(text, style)]."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    paras = [runs] if isinstance(runs, str) else runs
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.line_spacing = spacing
        segs = [(p, {})] if isinstance(p, str) else p
        for seg, style in segs:
            r = para.add_run()
            r.text = seg
            r.font.name = FONT
            r.font.size = Pt(style.get("size", size))
            r.font.bold = style.get("bold", bold)
            r.font.color.rgb = style.get("color", color)
    return box


def bullets(slide, x, y, w, h, items, size=18, color=NAVY, gap=8):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(gap)
        head, _, rest = item.partition("|")
        r = para.add_run()
        r.text = "•  " + head
        r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(size), color
        r.font.bold = bool(rest)
        if rest:
            r2 = para.add_run()
            r2.text = " " + rest
            r2.font.name, r2.font.size, r2.font.color.rgb = FONT, Pt(size), GREY
    return box


def card(slide, x, y, w, h, title, body, fill=LIGHT, accent=TEAL, title_size=17, body_size=14):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.adjustments[0] = 0.08
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y + Inches(0.18), Inches(0.07), h - Inches(0.36))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    text(slide, x + Inches(0.22), y + Inches(0.12), w - Inches(0.35), Inches(0.5), title, size=title_size, bold=True,
         color=NAVY)
    text(slide, x + Inches(0.22), y + Inches(0.58), w - Inches(0.35), h - Inches(0.7), body, size=body_size,
         color=GREY)
    return shp


def pill(slide, x, y, w, h, label, fill=TEAL, color=WHITE, size=14, bold=True):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.adjustments[0] = 0.5
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    tf = shp.text_frame
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = FONT, Pt(size), bold, color
    return shp


def arrow(slide, x1, y1, x2, y2, color=GREY):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = Pt(2)
    ln = c.line._get_or_add_ln()
    tail = ln.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd", {"type": "triangle"})
    ln.append(tail)
    return c


def base(prs, title, criterion=None, number=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = WHITE
    text(s, Inches(0.6), Inches(0.4), Inches(9.8), Inches(0.7), title, size=27, bold=True)
    if criterion:
        pill(s, Inches(10.55), Inches(0.45), Inches(2.25), Inches(0.42), criterion, fill=TEAL_LIGHT, color=TEAL,
             size=12)
    line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.2), Inches(1.1), Inches(0.06))
    line.fill.solid()
    line.fill.fore_color.rgb = TEAL
    line.line.fill.background()
    if number:
        text(s, Inches(12.2), Inches(7.0), Inches(0.8), Inches(0.35), str(number), size=11, color=GREY,
             align=PP_ALIGN.RIGHT)
    text(s, Inches(0.6), Inches(7.0), Inches(8), Inches(0.35), "PHC Pulse · Build with AI · Track 3", size=11,
         color=GREY)
    return s


def picture(slide, path, x, y, w=None, h=None):
    pic = slide.shapes.add_picture(str(path), x, y, width=w, height=h)
    pic.line.color.rgb = RGBColor(0xD8, 0xDE, 0xE6)
    pic.line.width = Pt(1)
    return pic


def build() -> Presentation:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1. Title ---------------------------------------------------------------------------------------------
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = NAVY
    text(s, Inches(0.8), Inches(1.6), Inches(11.5), Inches(1.2), "PHC Pulse", size=60, bold=True, color=WHITE)
    text(s, Inches(0.8), Inches(2.75), Inches(11.5), Inches(1.4),
         "Speak or photograph the stock register. Know where medicines will run out,\n"
         "and move surplus there before they do.", size=26, color=RGBColor(0xC9, 0xE7, 0xE4))
    text(s, Inches(0.8), Inches(4.5), Inches(11.5), Inches(0.5),
         "AI-powered federated health resource & supply chain intelligence for India's Primary Health Centres",
         size=18, color=WHITE)
    for i, lab in enumerate(["Gemini on Vertex AI", "Speech · TTS · Translation", "OR-Tools + Routes API",
                             "BigQuery + BQML", "Cloud Run"]):
        pill(s, Inches(0.8 + i * 2.35), Inches(5.35), Inches(2.2), Inches(0.45), lab, fill=TEAL, size=13)
    text(s, Inches(0.8), Inches(6.45), Inches(11.5), Inches(0.5),
         "Build with AI (Google) hackathon · Track 3 · github.com/ipavanreddy/health-resource-network",
         size=14, color=RGBColor(0x9F, 0xB3, 0xC8))

    # 2. Problem -------------------------------------------------------------------------------------------
    s = base(prs, "One PHC runs out while the next has stock near expiry", "Problem fit · 20%", 2)
    card(s, Inches(0.6), Inches(1.6), Inches(3.9), Inches(2.4), "Invisible stock",
         "Stock lives in paper registers and late spreadsheets. Nobody sees days of cover until a patient is "
         "turned away.")
    card(s, Inches(4.72), Inches(1.6), Inches(3.9), Inches(2.4), "Surges noticed late",
         "A post-flood diarrhoea spike or a dengue season shows up in consumption days before it shows up in "
         "reports.", accent=AMBER)
    card(s, Inches(8.84), Inches(1.6), Inches(3.9), Inches(2.4), "Fragmented systems",
         "Every state exports stock in its own format, codes and units, so nothing is comparable across "
         "facilities, districts or states.", accent=RED)
    text(s, Inches(0.6), Inches(4.35), Inches(12.2), Inches(0.5), "Who feels it", size=20, bold=True)
    bullets(s, Inches(0.6), Inches(4.85), Inches(12.2), Inches(2.0), [
        "PHC staff nurse|reports stock after a full clinic day, often in Tamil or Hindi, often on a basic phone.",
        "District Health Officer|has 30+ facilities and no single view of stock, beds, staff and early warnings.",
        "Patients in rural blocks|a stock-out means a longer trip, or no treatment at all.",
    ], size=17)

    # 3. Solution journey ----------------------------------------------------------------------------------
    s = base(prs, "One journey: spoken report to approved transfer", "Solution", 3)
    steps = [("Report", "Voice, register photo, text or form · EN / HI / TA"),
             ("Confirm", "Gemini extracts; staff confirm; ledger updates"),
             ("See", "Days of cover, beds, staff, readiness 0–100"),
             ("Predict", "8-week forecast, stock-out risk, possible surge"),
             ("Redistribute", "OR-Tools on real drive times + Gemini explanation"),
             ("Approve", "DHO approves → both PHCs notified → received")]
    bw, gap = Inches(1.95), Inches(0.13)
    for i, (h_, b) in enumerate(steps):
        x = Inches(0.6) + i * (bw + gap)
        fill = TEAL if i in (0, 5) else NAVY
        pill(s, x, Inches(1.75), bw, Inches(0.6), h_, fill=fill, size=17)
        text(s, x, Inches(2.5), bw, Inches(1.3), b, size=14, color=GREY, align=PP_ALIGN.CENTER)
        if i < len(steps) - 1:
            arrow(s, x + bw, Inches(2.05), x + bw + gap, Inches(2.05))
    text(s, Inches(0.6), Inches(4.0), Inches(12.2), Inches(0.5), "Two roles, one platform", size=20, bold=True)
    card(s, Inches(0.6), Inches(4.5), Inches(6.0), Inches(2.25), "PHC Staff app (mobile first)",
         "Report stock in their own language, hear it read back, see what is running low, and receive and confirm "
         "transfers.")
    card(s, Inches(6.8), Inches(4.5), Inches(6.0), Inches(2.25), "District Health Officer dashboard",
         "Map of readiness and risk, possible surge clusters to verify, optimiser proposals to approve, emergency "
         "what-if, and cross-state interoperability.", accent=AMBER)

    # 4. Frontline capture ---------------------------------------------------------------------------------
    s = base(prs, "Capture that fits a nurse's evening: talk, or take a photo", "AI / technical · 25%", 4)
    picture(s, ASSETS / "sample-register.png", Inches(0.6), Inches(1.55), w=Inches(6.1))
    text(s, Inches(0.6), Inches(5.85), Inches(6.1), Inches(0.9),
         "Synthetic register page. Gemini reads all six rows, returns closing = null with the cell flagged as "
         "illegible under the ink blot, and flags “Tab. Cetriz” as not in the medicine list.", size=12,
         color=GREY)
    bullets(s, Inches(7.0), Inches(1.6), Inches(5.8), Inches(5.2), [
        "Voice in Tamil / Hindi / English|Cloud Speech-to-Text, then Gemini maps each spoken name to the essential "
        "medicines master. A noisy transcript (“ஓவர் s40”) still resolves to ORS: 40.",
        "Register photo|Gemini multimodal reads handwriting into a strict JSON schema.",
        "Never invents a number|Unstated quantity = null; unknown drug codes rejected; staff confirm before the "
        "ledger changes.",
        "Spoken confirmation|Cloud Text-to-Speech reads the result back in the staff member's language.",
        "Traceable|every AI record stores model, version and prompt version; originals kept in Cloud Storage.",
    ], size=16)

    # 5. Decision layer ------------------------------------------------------------------------------------
    s = base(prs, "Signals to approved transfer, with a human in the loop", "AI / technical · 25%", 5)
    picture(s, ASSETS / "dho-dashboard.png", Inches(0.6), Inches(1.5), w=Inches(7.4))
    text(s, Inches(0.6), Inches(6.7), Inches(7.4), Inches(0.35),
         "Live DHO dashboard, Madurai (synthetic data): surge cluster, proposed routes, Gemini explanation.",
         size=11, color=GREY)
    bullets(s, Inches(8.25), Inches(1.55), Inches(4.6), Inches(5.3), [
        "Forecast|8-week low / expected / high per facility × medicine; stock-out weeks are excluded so censored "
        "demand is not learned.",
        "Early warning|stock-out risk plus surge detection, shown as a possible signal the DHO verifies.",
        "Optimiser|OR-Tools min-cost flow on Routes API drive times; donors never drop below 45 days of "
        "safety stock; near-expiry stock is preferred.",
        "Explanation|Gemini explains each transfer in the officer's language but cannot change quantities.",
        "Approval|nothing moves without the DHO.",
    ], size=15, gap=6)

    # 6. Google AI stack -----------------------------------------------------------------------------------
    s = base(prs, "Google AI doing real work, verified live", "AI / technical · 25%", 6)
    rows = [("Gemini 2.5 Flash (Vertex AI)", "Voice/text extraction, register photo reading, transfer explanations",
             "Live"),
            ("Speech-to-Text · Text-to-Speech · Translation", "Tamil / Hindi voice reports and spoken confirmations",
             "Live"),
            ("OR-Tools", "Min-cost-flow redistribution with safety-stock constraints", "Live"),
            ("Maps Routes API + Maps JS", "Real drive times; facility and route map", "Live"),
            ("BigQuery", "Append-only ledger of stock transactions, transfers and AI outputs", "Live"),
            ("BigQuery ML ARIMA_PLUS", "Shared demand model over 1,536 facility × medicine series", "Trained"),
            ("Cloud Storage", "Original register photos and voice recordings", "Live"),
            ("Cloud Run + Secret Manager", "Three services in asia-south1; keys never in code", "Live")]
    y = Inches(1.55)
    for name, role, status in rows:
        text(s, Inches(0.6), y, Inches(4.6), Inches(0.5), name, size=16, bold=True)
        text(s, Inches(5.25), y, Inches(6.0), Inches(0.5), role, size=15, color=GREY)
        pill(s, Inches(11.5), y + Inches(0.03), Inches(1.25), Inches(0.38), status,
             fill=TEAL if status == "Live" else AMBER, size=12)
        y += Inches(0.6)
    text(s, Inches(0.6), Inches(6.45), Inches(12.2), Inches(0.5),
         "Every adapter has a labelled fallback. The app's badge shows only integrations that pass a start-up probe.",
         size=14, color=TEAL, bold=True)

    # 7. Depth & reach -------------------------------------------------------------------------------------
    s = base(prs, "India's diversity: 3 states, 3 languages, 1 shared model", "Depth & reach · 20%", 7)
    states = [("Tamil Nadu · Madurai", "Post-flood diarrhoea → ORS and zinc", "Tamil voice"),
              ("Uttar Pradesh · Gorakhpur", "Vector-borne season → paracetamol and IV fluids", "Hindi voice"),
              ("Odisha · Koraput", "Malaria season → antimalarial redistribution", "English")]
    for i, (a, b, c) in enumerate(states):
        card(s, Inches(0.6 + i * 4.12), Inches(1.55), Inches(3.95), Inches(1.75), a, f"{b}\n{c}",
             accent=[TEAL, AMBER, NAVY][i])
    text(s, Inches(0.6), Inches(3.55), Inches(12.2), Inches(0.5), "Onboarding a state is a configuration file",
         size=20, bold=True)
    flow = ["State export\n(own codes, units, dates)", "Declarative adapter\n(data/adapters/*.json)",
            "Canonical schema\n(canonical_v1)", "Shared forecast model\n+ shared AI services"]
    for i, f in enumerate(flow):
        x = Inches(0.6) + i * Inches(3.1)
        pill(s, x, Inches(4.15), Inches(2.75), Inches(0.95), f, fill=LIGHT, color=NAVY, size=14)
        if i < 3:
            arrow(s, x + Inches(2.75), Inches(4.62), x + Inches(3.1), Inches(4.62), color=TEAL)
    bullets(s, Inches(0.6), Inches(5.4), Inches(12.2), Inches(1.5), [
        "Per-state config|languages, readiness weights, safety stock, cross-district transfer policy, model choice.",
        "Models travel, data doesn't|states share model weights and accuracy; facility-level data stays in the state.",
    ], size=16)

    # 8. Deployability & scalability -----------------------------------------------------------------------
    s = base(prs, "Deployable today; plugs into existing state systems", "Deployability · 20%", 8)
    card(s, Inches(0.6), Inches(1.55), Inches(6.0), Inches(2.35), "Cloud-native and API-first",
         "Three Cloud Run services (API + two Next.js apps) in asia-south1, one repeatable deploy script, secrets in "
         "Secret Manager, OpenAPI for every endpoint.")
    card(s, Inches(6.8), Inches(1.55), Inches(6.0), Inches(2.35), "Integrates, doesn't replace",
         "Adapters read the stock exports states already produce, so no state has to swap its existing drug "
         "distribution system.", accent=AMBER)
    text(s, Inches(0.6), Inches(4.15), Inches(12.2), Inches(0.5), "Scale path", size=20, bold=True)
    path = ["One PHC", "One block", "One district", "One state", "Many states", "National network"]
    for i, p in enumerate(path):
        x = Inches(0.6) + i * Inches(2.07)
        pill(s, x, Inches(4.75), Inches(1.8), Inches(0.55), p, fill=NAVY if i < 3 else TEAL, size=14)
        if i < len(path) - 1:
            arrow(s, x + Inches(1.8), Inches(5.02), x + Inches(2.07), Inches(5.02))
    bullets(s, Inches(0.6), Inches(5.6), Inches(12.2), Inches(1.3), [
        "Stateless services scale horizontally|BigQuery becomes the read path beyond the pilot; Firestore for "
        "real-time updates.",
        "Works on the phones staff already have|mobile-first web app with voice, no install.",
    ], size=16)

    # 9. Impact --------------------------------------------------------------------------------------------
    s = base(prs, "Fewer stock-outs where rural patients need the medicine", "Impact · 15%", 9)
    stats = [("12", "transfers proposed in one optimiser run for Madurai district"),
             ("~277", "facility-days of stock-out avoided over the next 30 days"),
             ("~53 min", "average drive time per transfer (Google Routes API)"),
             ("0", "donors taken below their 45-day safety stock")]
    for i, (big, small) in enumerate(stats):
        x = Inches(0.6) + i * Inches(3.1)
        text(s, x, Inches(1.6), Inches(2.9), Inches(0.9), big, size=44, bold=True, color=TEAL)
        text(s, x, Inches(2.55), Inches(2.9), Inches(1.0), small, size=15, color=GREY)
    text(s, Inches(0.6), Inches(3.55), Inches(12.2), Inches(0.4),
         "Demo figures from the synthetic Madurai dataset, not a field result.", size=12, color=AMBER)
    bullets(s, Inches(0.6), Inches(4.2), Inches(12.2), Inches(2.6), [
        "Patients|essential medicines on the shelf during floods, dengue and malaria seasons.",
        "Staff|reporting takes seconds instead of an evening of copying; alerts arrive in their own language.",
        "Districts|surplus and near-expiry stock is moved instead of wasted, and surges are seen days earlier.",
        "What a pilot would measure|stock-out days per tracer medicine, reporting freshness, time from alert to "
        "receipt, near-expiry write-offs.",
    ], size=17)

    # 10. Cross-border -------------------------------------------------------------------------------------
    s = base(prs, "Portable beyond India: a template for BRICS health systems", "Portability", 10)
    card(s, Inches(0.6), Inches(1.55), Inches(3.95), Inches(2.6), "Same canonical model",
         "A new country adds an adapter and a drug-code map (for example, to its national essential medicines "
         "list or the WHO EML). Capture, forecasting, optimiser and dashboards are unchanged.")
    card(s, Inches(4.72), Inches(1.55), Inches(3.95), Inches(2.6), "Any language",
         "Gemini, Speech-to-Text, Text-to-Speech and Translation cover Portuguese, Russian, Mandarin, Arabic, "
         "Amharic, isiZulu and more. The UI strings are one table.", accent=AMBER)
    card(s, Inches(8.84), Inches(1.55), Inches(3.95), Inches(2.6), "Data sovereignty",
         "Deploy per country in its own Google Cloud region. Countries share models and aggregate accuracy, "
         "never facility-level records.", accent=NAVY)
    bullets(s, Inches(0.6), Inches(4.5), Inches(12.2), Inches(2.3), [
        "Configurable policy|readiness weights, safety stock and cross-border transfer rules per country.",
        "Shared learning|a regional model registry lets a country with little history start from its neighbours' "
        "model and publish its own accuracy back.",
        "Same problem everywhere|primary care facilities in Brazil, South Africa, Ethiopia and Indonesia face the "
        "same last-mile stock-outs.",
    ], size=17)

    # 11. Ask ----------------------------------------------------------------------------------------------
    s = base(prs, "Try it, and help us pilot it in one district", None, 11)
    card(s, Inches(0.6), Inches(1.55), Inches(6.0), Inches(2.6), "Live now",
         f"PHC Staff: {LIVE}\nDHO dashboard: health-resource-network-officer-dashboard-847963771142.asia-south1"
         ".run.app\nCode: github.com/ipavanreddy/health-resource-network", body_size=13)
    card(s, Inches(6.8), Inches(1.55), Inches(6.0), Inches(2.6), "Next 90 days",
         "District pilot on real stock exports · Firebase Auth + Firestore real-time notifications · weather and "
         "surveillance covariates (Earth Engine) · offline sync for low-connectivity PHCs.", accent=AMBER)
    text(s, Inches(0.6), Inches(4.6), Inches(12.2), Inches(1.2),
         "One polished journey: a nurse speaks, a forecast warns, an optimiser proposes, a person approves, "
         "medicine arrives.", size=24, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    text(s, Inches(0.6), Inches(5.9), Inches(12.2), Inches(0.5),
         "All demo data is synthetic and labelled that way. No patient-level data is stored.", size=13, color=GREY,
         align=PP_ALIGN.CENTER)
    return prs


if __name__ == "__main__":
    deck = build()
    deck.save(OUT)
    print(f"wrote {OUT.relative_to(HERE.parents[1])} ({len(deck.slides)} slides, {Emu(W).inches:.2f} in wide)")
