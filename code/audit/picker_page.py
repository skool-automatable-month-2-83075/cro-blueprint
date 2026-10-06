"""The page inside the picker, drawn in the Claude Series kit, the same kit and classes page B uses. Every text element is an empty `data-f` hook the picker fills,
so rotating an option only swaps words. Everything the owner supplies is a dashed placeholder, drawn the way
`components/lp/Slot.tsx` draws one on the dev server; review badges are drawn as samples until real numbers exist.

Layouts come from `drafts.structure()`: hero-video, logo-row, stat-row, tint-card, two-up-left, two-up-right,
rows, video-grid, quote-wall, faq-list, form-split, legal-line."""
import html

# ⛔ NOTHING HERE BELONGS TO ONE BUSINESS (Jono, 29 September 2026: "make it so anyone can run the skill, I
# don't want it built on my social proof"). The name, the phone, the reviews, the client videos and the faces
# come from the page's own drafts/proof.json, set once per build by use(). With no proof file every one of
# them is a placeholder - never another business's proof.
BIZ = {"business": "", "phone": "", "reviews": [], "videos": [], "faces": [], "logos": [], "results_note": "", "stats": [], "public": "",
       "form_button": "", "lead_magnet": "", "next_steps": []}
# Sample numbers only, drawn so the owner sees the finished row. Never shipped: the tag says so.
SAMPLE_BADGES = [("google", 4.9, 127), ("trustpilot", 4.8, 64), ("g2", 4.7, 38), ("trustindex", 4.9, 52)]


def use(biz, public):
    """The business this page is for, and the path from the picker file to the site's public folder."""
    BIZ.clear()
    BIZ.update({"business": "", "phone": "", "reviews": [], "videos": [], "faces": [], "logos": [], "results_note": "", "stats": [],
                "form_button": "", "lead_magnet": "", "next_steps": []}, **biz)
    BIZ["public"] = public


def name():
    return BIZ["business"] or "Your business"


def tel():
    return "tel:+" + "".join(c for c in BIZ["phone"] if c.isdigit()) if BIZ["phone"] else "#"


def form_button():
    """What the form's button says: the business's own words, or a plain default."""
    return BIZ["form_button"] or "Get my quote"


def magnet_hint():
    """What the picture beside the form should show: the thing they get for filling it in."""
    return f"A picture of {BIZ['lead_magnet']}, so they see what they get." if BIZ["lead_magnet"] else "A picture of what they get for filling in the form."


def call_label():
    return f"Call {BIZ['phone']}" if BIZ["phone"] else "Call [your phone number]"


def src(path):
    """A site image path (/images/...) as the picker file sees it; a full URL as it is."""
    return path if path.startswith("http") else BIZ["public"] + path


LOGOS = 6
# How many client videos and written reviews a page shows, placeholders included, inside the blueprint's ranges
# (videos three to nine, reviews six to nine): a short page stops at the floor, a long one fills to the top.
COUNTS = {"short": (3, 6), "medium": (6, 9), "long": (9, 9)}

ICON = {
    "play": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 5.5v13l10.5-6.5z"/></svg>',
    "image": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M4 17l5-4.5 4 3.5 3-2.5 4 3.5"/></svg>',
    "quote": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 17c2-1 3-3 3-6H5V6h5v5c0 4-2 6-5 7zm9 0c2-1 3-3 3-6h-3V6h5v5c0 4-2 6-5 7z"/></svg>',
    "logo": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="7" width="16" height="10" rx="2"/><path d="M8 12h8"/></svg>',
    "file": '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 3.5h7l4 4V20.5H7z"/><path d="M14 3.5v4h4M9.5 12h6M9.5 15.5h6"/></svg>',
}
TICK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.6 2.5L16 9.5"/></svg>'


def e(t):
    return html.escape(str(t))


def slot(label, hint="", note="", blue=False, ratio="16 / 9", icon="image"):
    """An empty slot, as Slot.tsx's EmptySlot draws it on the dev server."""
    return (f'<div class="ph{" ph-blue" if blue else ""}" style="aspect-ratio:{ratio}"><span class="ph-in">{ICON.get(icon, "")}'
            f'<strong>{e(label)}</strong>{f"<span>{e(hint)}</span>" if hint else ""}{f"<em>{e(note)}</em>" if note else ""}</span></div>')


def pill(text):
    return f'<span class="ph-pill">Placeholder · {e(text)}</span>'


def tag(text):
    return f'<span class="ph-tag">{e(text)}</span>'


def _stars(score, color, boxed=False, empty="#d9d9df"):
    out = []
    for i in range(5):
        fill = max(0.0, min(1.0, score - i)) * 100
        if boxed:
            out.append(f'<span class="bg-box" style="background:{empty}"><i style="width:{fill:.0f}%;background:{color}"></i><b>★</b></span>')
        else:
            out.append(f'<span class="bg-star" style="color:{empty}">★<i style="width:{fill:.0f}%;color:{color}">★</i></span>')
    return "".join(out)


def badge(platform, score, count, dark):
    ink, soft, empty = ("#fff", "rgba(255,255,255,.78)", "rgba(255,255,255,.3)") if dark else ("#111214", "#63666e", "#d9d9df")
    mark = {"google": '<span class="bg-mark" style="background:#fff;color:#4285F4;font-family:Arial;font-weight:700">G</span>',
            "trustpilot": '<span class="bg-mark" style="background:#00B67A;color:#fff">★</span>',
            "g2": '<span class="bg-mark" style="background:#FF492C;color:#fff;font-weight:800;font-size:12px">G2</span>',
            "trustindex": '<span class="bg-mark" style="background:#1a8f4f;color:#fff;border-radius:8px">✓</span>'}[platform]
    name = {"google": "Google", "trustpilot": "Trustpilot", "g2": "G2", "trustindex": "Trustindex"}[platform]
    stars = _stars(score, "#00B67A", True, empty) if platform == "trustpilot" else _stars(score, "#FF492C" if platform == "g2" else "#FBBC04", False, empty)
    return (f'<span class="bg" style="color:{ink}">{mark}<span class="bg-txt"><span class="bg-top"><strong>{score:.1f}</strong>{stars}</span>'
            f'<span style="color:{soft}"><strong style="color:{ink}">{name}</strong> · {count} reviews</span></span></span>')


def badges(dark):
    """Only as many as fit one line: the row wraps, and the second row is cut off (ReviewBadge.tsx)."""
    return (f'<div class="bg-wrap">{tag("Sample · swap in your real scores")}<div class="bg-row{" bg-dark" if dark else ""}">'
            + "".join(f'<span class="bg-cell">{badge(p, s, c, dark)}</span>' for p, s, c in SAMPLE_BADGES) + "</div></div>")


def buttons(ask, form_text, blue=False):
    call = f'<a class="cs-btn {"cs-btn-white" if blue else "cs-btn-brand"}" href="{tel()}">{e(call_label())}</a>'
    form = f'<a class="cs-btn cs-btn-quiet" href="#form">{e(form_text)}</a>'
    return f'<div class="cs-actions">{call + form if ask == "call" else form.replace("cs-btn-quiet", "cs-btn-white" if blue else "cs-btn-brand") + call.replace("cs-btn-white", "cs-btn-quiet").replace("cs-btn-brand", "cs-btn-quiet")}</div>'


FIELD = {"field": "cs-field", "ink": "cs-field cs-ink", "paper": "cs-paper"}


def proof_block(faces, dark):
    face = "".join(f'<img src="{src(f)}" alt="">' for f in BIZ["faces"][:3]) or pill("three client faces")
    ticks = "".join(f'<li class="cs-tick">{TICK}{pill(t)}</li>' for t in ("years in business", "clients served", "jobs completed"))
    return (f'<ul class="cs-ticks">{ticks}</ul><div class="cs-faces">{face}{pill("rating line: stars, score, count, platform")}</div>{badges(dark)}')


def founder_slot(dark, ratio="16 / 10"):
    return slot("Founder video · 45 seconds", "Who you are, why you do this, and the offer, filmed for this page.",
                "Until it is filled, visitors see a picture of your work.", dark, ratio, "play")


def hero(ask, form_text, faces, look="field"):
    """The blue field: the words on the left, the founder video beside them."""
    dark = look != "paper"
    return (f'<section class="{FIELD[look]}"><div class="cs-wrap cs-pad-hero"><div class="cs-hero-grid"><div class="cs-stack">'
            f'<p class="cs-label" data-f="eyebrow"></p><h1 class="cs-hero" data-f="h1"></h1><p class="cs-lead" data-f="sub"></p>'
            f'{proof_block(faces, dark)}{buttons(ask, form_text, dark)}</div>{founder_slot(dark)}</div></div></section>')


def form_card(button, faces):
    fields = "".join(f'<label><span>{e(n)}</span><input type="{t}" placeholder="{e(n)}" data-in="{k}"></label>'
                     for n, t, k in (("First name", "text", "first"), ("Last name", "text", "last"), ("Email", "email", "email"), ("Phone", "tel", "phone")))
    return (f'<div class="cs-card cs-form"><form onsubmit="return false">{fields}'
            f'<p class="cs-fine">By sending this you agree we may call and text you about your request.</p>{button}'
            f'<p class="cs-fine">{pill("how fast you call back, once it is real")}</p></form></div>')


def hero_form(ask, form_text, faces, look="paper"):
    """The form in the first screen, beside the headline. The founder video moves to its own band below."""
    dark = look != "paper"
    card = form_card(f'<button class="cs-btn cs-btn-brand" type="button">{e(form_text)}</button>', faces)
    magnet = slot("Lead magnet picture", magnet_hint(), "", dark, "16 / 6", "file")
    return (f'<section class="{FIELD[look]}"><div class="cs-wrap cs-pad-hero"><div class="cs-hero-grid"><div class="cs-stack">'
            f'<p class="cs-label" data-f="eyebrow"></p><h1 class="cs-hero cs-hero-sm" data-f="h1"></h1><p class="cs-lead" data-f="sub"></p>'
            f'{proof_block(faces, dark)}<p class="cs-muted">Rather talk? <a href="{tel()}"><strong>{e(call_label())}</strong></a></p></div>'
            f'<div class="cs-stack">{magnet}{card}</div></div></div></section>')


def hero_center(ask, form_text, faces, look="ink"):
    """Everything centred over a wide founder video: the promise first, the proof straight under it."""
    dark = look != "paper"
    return (f'<section class="{FIELD[look]}"><div class="cs-wrap cs-pad-hero cs-centre"><div class="cs-stack cs-narrow cs-mid">'
            f'<p class="cs-label" data-f="eyebrow"></p><h1 class="cs-hero" data-f="h1"></h1><p class="cs-lead cs-mid" data-f="sub"></p>'
            f'<div class="cs-mid">{buttons(ask, form_text, dark)}</div>{proof_block(faces, dark)}</div>'
            f'<div class="cs-wide">{founder_slot(dark, "21 / 9")}</div></div></section>')


def founder_band(ask, form_text):
    return (f'<section class="cs-section cs-white"><div class="cs-wrap"><div class="cs-split">{founder_slot(False, "16 / 9")}'
            f'<div class="cs-stack"><p class="cs-label">From the founder</p>{pill("one line: who you are and why you do this")}{buttons(ask, form_text)}</div></div></div></section>')


def benefit_compact(ask, form_text, n, white):
    """Paper look: no picture, a big number, the words - a short page stays short."""
    return (f'<section class="cs-section cs-tight{" cs-white" if white else ""}"><div class="cs-wrap"><div class="cs-compact">'
            f'<div class="cs-bignum">0{n}</div>{words_block(ask, form_text, "cs-title cs-title-sm")}</div></div></section>')


def benefit_row(ask, form_text, n, white):
    """Ink look: a numbered row, the words in the middle, a small picture on the right."""
    pic = slot("Picture · this benefit, shown", "A real photo or screenshot that shows this point.", "", False, "4 / 3")
    return (f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap"><div class="cs-brow">'
            f'<div class="cs-bignum cs-bignum-ink">0{n}</div>{words_block(ask, form_text, "cs-title cs-title-sm")}{pic}</div></div></section>')


def logo_row():
    """Client logos. A client named in proof.json is a slot asking for that logo file; the rest are blank slots."""
    named = [slot(n, "logo file needed", "", False, "3 / 1", "logo") for n in BIZ["logos"][:LOGOS]]
    blank = [slot("Client logo", "", "", False, "3 / 1", "logo") for _ in range(max(0, LOGOS - len(named)))]
    return ('<section class="cs-white cs-strip"><div class="cs-wrap"><p class="cs-label cs-center">Trusted by</p><div class="cs-grid-6">'
            + "".join(named + blank) + "</div></div></section>")


def stat_row():
    """The numbers strip. The owner picks up to four in the picker; these four stand in until then."""
    return ('<section class="cs-strip"><div class="cs-wrap"><div class="cs-card-tint cs-grid-4" data-stats>'
            + "".join(f'<div><div class="cs-num cs-num-xl">{e(x["value"])}</div><p class="cs-muted">{e(x["label"])}</p></div>' for x in BIZ["stats"][:4])
            + "</div></div></section>")


def words_block(ask, form_text, title_cls="cs-title"):
    return (f'<div class="cs-stack"><h2 class="{title_cls}" data-f="heading"></h2><p class="cs-lead" data-f="body"></p>'
            f'<ul class="cs-dashes" data-f="bullets"></ul><div class="cs-rows" data-f="rows"></div>{buttons(ask, form_text)}</div>')


def two_up(ask, form_text, flip, pic_label, white):
    pic = slot(pic_label, "A real photo or screenshot that shows this point.", "Until it is filled, visitors see a kit graphic.")
    inner = f'<div class="cs-split">{words_block(ask, form_text) + pic if not flip else pic + words_block(ask, form_text)}</div>'
    return f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap">{inner}</div></section>'


def tint(ask, form_text, pic_label):
    return (f'<section class="cs-section"><div class="cs-wrap"><div class="cs-card-tint cs-split">{words_block(ask, form_text)}'
            f'{slot(pic_label, "A kit graphic that shows the idea, with no names, stars or numbers on it.", "", False, "4 / 3")}</div></div></section>')


def rows(ask, form_text, white):
    return f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap cs-narrow">{words_block(ask, form_text)}</div></section>'


def videos(ask, form_text, white, target=9):
    real = "".join(f'<figure class="cs-video"><div class="cs-thumb"><img src="https://i.ytimg.com/vi/{e(v["id"])}/hqdefault.jpg" alt=""><span class="cs-play">{ICON["play"]}</span></div>'
                   f'<figcaption><strong>{e(v.get("name", ""))}</strong><span>{e(v.get("who", ""))}</span><b>{e(v.get("result", ""))}</b></figcaption></figure>' for v in BIZ["videos"][:target])
    more = "".join(slot("Client video", f"{target} on this page: a phone video, what was broken and what changed.", "", False, "16 / 9", "play")
                   for _ in range(max(0, target - len(BIZ["videos"]))))
    note = f'<p class="cs-muted cs-gap-top">{e(BIZ["results_note"])}</p>' if BIZ["results_note"] else ""
    return (f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap"><div class="cs-stack"><h2 class="cs-title" data-f="heading"></h2>'
            f'<p class="cs-lead" data-f="sub"></p></div><div class="cs-grid-3 cs-gap-top">{real}{more}</div>{note}'
            f'{buttons(ask, form_text)}</div></section>')


def reviews(ask, form_text, faces, white, target=9):
    real = "".join(f'<blockquote class="cs-card cs-quote"><p>{e(r["quote"])}</p><footer>'
                   + (f'<img src="{src(r["photo"])}" alt="">' if r.get("photo") else f'<span class="cs-initial">{e(r["name"][:1])}</span>')
                   + f'<span><strong>{e(r["name"])}</strong><span>{e(r.get("meta", ""))}</span></span></footer></blockquote>' for r in BIZ["reviews"][:target])
    more = "".join(slot("Written review", "Word for word from a paying client, with their name and face.", "", False, "4 / 3", "quote")
                   for _ in range(max(0, target - len(BIZ["reviews"]))))
    return (f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap"><div class="cs-stack"><h2 class="cs-title" data-f="heading"></h2>'
            f'<p class="cs-lead" data-f="sub"></p></div><div class="cs-grid-3 cs-gap-top">{real}{more}</div><div class="cs-gap-top">{badges(False)}</div>'
            f'{buttons(ask, form_text)}</div></section>')


def faq(ask, form_text, white):
    return (f'<section class="cs-section{" cs-white" if white else ""}"><div class="cs-wrap cs-narrow"><h2 class="cs-title" data-f="heading"></h2>'
            f'<div class="cs-faq cs-gap-top" data-f="items"></div>{buttons(ask, form_text)}</div></section>')


CLOSE_BUTTON = '<button class="cs-btn cs-btn-brand" type="button" data-f="button"></button>'  # its words are the close's options


def close(faces, look="field"):
    dark = look != "paper"
    band = "cs-tintband" if look == "paper" else FIELD[look]
    return (f'<section class="{band}" id="form"><div class="cs-wrap cs-section"><div class="cs-split"><div class="cs-stack">'
            f'<h2 class="cs-title" data-f="heading"></h2><p class="cs-lead" data-f="body"></p>'
            + slot("Lead magnet picture", magnet_hint(), "", dark, "4 / 3", "file")
            + f'<p class="cs-muted">Or call now: <a href="{tel()}"><strong>{e(BIZ["phone"] or "[your phone number]")}</strong></a></p></div>'
            f'<div>{form_card(CLOSE_BUTTON, faces)}'
            f'<div class="cs-gap-top">{badges(dark)}</div></div></div></div></section>')


def legal():
    return (f'<footer class="cs-legal"><div class="cs-wrap">{e(name())} · {pill("registered business address")} · '
            f'<a href="{tel()}">{e(BIZ["phone"] or "[your phone number]")}</a> · Privacy policy · Terms</div></footer>')


def topline():
    return (f'<header class="cs-top"><div class="cs-wrap cs-top-in"><span class="cs-mark">{e(name().upper())}</span>'
            f'<a class="cs-btn cs-btn-brand cs-btn-sm" href="{tel()}">{e(call_label())}</a></div></header>')


def mobile_bar(ask, form_text):
    return f'<div class="cs-mbar"><a href="{tel()}">Call now</a><a href="#form">{e(form_text)}</a></div>'


def section(s, ask, form_text, faces, white, look="field", length="long"):
    lay, t = s["layout"], s["type"]
    vids, revs = COUNTS.get(length, COUNTS["long"])
    pic = {"audit": "Picture · what they get", "benefit": "Picture · this benefit, shown"}.get(t.split("-")[0], "Picture")
    n = t.split("-")[1] if t.startswith("benefit-") else "1"
    if lay == "hero-video":
        return hero(ask, form_text, faces, look)
    if lay == "hero-form":
        return hero_form(ask, form_text, faces, look)
    if lay == "hero-center":
        return hero_center(ask, form_text, faces, look)
    if lay == "founder-band":
        return founder_band(ask, form_text)
    if lay == "benefit-compact":
        return benefit_compact(ask, form_text, n, white)
    if lay == "benefit-row":
        return benefit_row(ask, form_text, n, white)
    if lay == "logo-row":
        return logo_row()
    if lay == "stat-row":
        return stat_row()
    if lay == "tint-card":
        return tint(ask, form_text, "Graphic · " + ("the terms" if t == "terms" else "the problem"))
    if lay in ("two-up-left", "two-up-right"):
        return two_up(ask, form_text, lay == "two-up-left", pic, white)
    if lay == "rows":
        return rows(ask, form_text, white)
    if lay == "video-grid":
        return videos(ask, form_text, white, vids)
    if lay == "quote-wall":
        return reviews(ask, form_text, faces, white, revs)
    if lay == "faq-list":
        return faq(ask, form_text, white)
    if lay == "form-split":
        return close(faces, look)
    if lay == "legal-line":
        return legal()
    return rows(ask, form_text, white)
