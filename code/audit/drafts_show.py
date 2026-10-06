"""drafts.html: each draft's big idea, then its message map laid into the structure it implies, section by
section, drawn as wireframes. No words yet - the words fill the structure after the owner picks one (drafts.py, "the order")."""
import html
import re

from audit.drafts import ALWAYS, ASK_OWNER, NAMES, structure
from audit.motivations import MOTIVATIONS

CSS = """
:root{--ink:#111214;--body:#33353a;--muted:#63666e;--line:#dcdee3;--wire:#e6e8ec;--wire2:#cfd3da;--page:#f8f9fb;--card:#fff;
--brand:#3b6ffd;--brand-soft:#e2eafe;--tint:#e6f3fa;--warn:#8a5a00;--warn-soft:#fff4de}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--body);font:14px/1.5 Mulish,system-ui,sans-serif}
h1,h2,h3,.lab{font-family:Figtree,system-ui,sans-serif;color:var(--ink);margin:0}
.top{padding:28px 20px 4px;max-width:1640px;margin:0 auto}.top h1{font-size:28px;letter-spacing:-.02em}
.top p{margin:6px 0 0;color:var(--muted)}
.cols{display:grid;gap:20px;padding:20px;max-width:1640px;margin:0 auto;grid-template-columns:minmax(0,1fr)}
@media(min-width:900px){.cols{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1400px){.cols{grid-template-columns:repeat(4,minmax(0,1fr))}}
.col{background:var(--card);border-radius:22px;box-shadow:0 18px 40px rgba(17,18,20,.08);overflow:hidden;min-width:0}
.head{padding:22px;background:var(--brand);color:#fff}.head h2{color:#fff;font-size:22px}.head p{margin:8px 0 0}
.today .head{background:#33353a}.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.meta span{background:rgba(255,255,255,.16);border-radius:999px;padding:3px 10px;font-size:12.5px}
.yes{padding:12px 22px;background:var(--warn-soft);color:var(--warn);font-size:13px}.yes b{display:block}
.sec{padding:14px 22px;border-bottom:1px solid var(--line)}.lab{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--brand)}
.says{margin:6px 0 0;color:var(--ink)}.holds{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
.holds span{font-size:11.5px;border-radius:999px;padding:1px 8px;background:var(--brand-soft);color:#1355f4}
.always{padding:14px 22px;color:var(--muted);font-size:12.5px}
.wf{margin-top:10px;border:1px solid var(--line);border-radius:12px;padding:10px;background:#fff}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:10px;align-items:center}.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.g6{display:grid;grid-template-columns:repeat(6,1fr);gap:5px}
.ln{height:6px;border-radius:3px;background:var(--wire);margin:5px 0}.ln.s{width:45%}.ln.m{width:75%}.ln.h{height:12px;background:var(--wire2)}
.box{border-radius:8px;background:var(--wire);position:relative}.pic{aspect-ratio:4/3}.vid{aspect-ratio:16/9;background:var(--wire2)}
.vid:after{content:"";position:absolute;left:50%;top:50%;transform:translate(-40%,-50%);border-left:10px solid #fff;border-top:6px solid transparent;border-bottom:6px solid transparent}
.logo{height:14px}.num{height:16px;width:60%;background:var(--wire2);border-radius:4px}.q{padding:6px;border-radius:6px;background:var(--wire)}
.btns{display:flex;gap:6px;margin-top:6px}.btn{height:14px;flex:1;border-radius:5px;background:var(--brand)}.btn.o{background:#fff;border:1px solid var(--brand)}
.tint{background:var(--tint);border-radius:10px;padding:10px}.row{display:grid;grid-template-columns:18px 1fr;gap:8px;align-items:center;margin:4px 0}
.dot{width:18px;height:18px;border-radius:50%;background:var(--brand-soft)}.field{height:12px;border:1px solid var(--wire2);border-radius:4px;margin:4px 0}
"""

L = lambda cls="": f'<div class="ln {cls}"></div>'  # noqa: E731
BTNS = '<div class="btns"><div class="btn"></div><div class="btn o"></div></div>'


def wire(layout):
    if layout == "hero-video":
        return f'<div class="g2"><div>{L("s")}{L("h")}{L("h m")}{L()}{L("m")}{BTNS}</div><div class="box vid"></div></div>'
    if layout == "logo-row":
        return '<div class="g6">' + '<div class="box logo"></div>' * 6 + "</div>"
    if layout == "stat-row":
        return '<div class="g4">' + f'<div><div class="num"></div>{L("m")}</div>' * 4 + "</div>"
    if layout in ("two-up-left", "two-up-right"):
        words, pic = f'<div>{L("h m")}{L()}{L()}{L("m")}{BTNS}</div>', '<div class="box pic"></div>'
        return f'<div class="g2">{pic + words if layout == "two-up-left" else words + pic}</div>'
    if layout == "tint-card":
        return f'<div class="tint g2"><div>{L("h m")}{L()}{L("m")}</div><div class="box pic"></div></div>'
    if layout == "rows":
        return "".join(f'<div class="row"><div class="dot"></div><div>{L("m")}</div></div>' for _ in range(4)) + BTNS
    if layout == "video-grid":
        return '<div class="g3">' + '<div class="box vid"></div>' * 6 + "</div>"
    if layout == "quote-wall":
        return '<div class="g3">' + f'<div class="q">{L()}{L("m")}{L("s")}</div>' * 6 + "</div>"
    if layout == "cards":
        return '<div class="g3">' + f'<div class="q">{L("h m")}{L()}{L("m")}</div>' * 3 + "</div>" + BTNS
    if layout == "faq-list":
        return "".join(L("m") for _ in range(4)) + BTNS
    if layout == "form-split":
        fields = '<div class="field"></div>' * 4
        return f'<div class="g2"><div class="box pic"></div><div>{fields}<div class="btns"><div class="btn"></div></div></div></div>'
    if layout == "legal-line":
        return L("s")
    return f"{L('h m')}{L()}{L('m')}"


def _h(t):
    return re.sub(r"\[([^\]]*)\]", r"<b>[\1]</b>", html.escape(str(t)))


def column(k, d, pool):
    text = {p["id"]: p["point"] for p in pool["points"]}
    asks = {p["id"] for p in pool["points"] if str(p.get("source", "")).lower() == ASK_OWNER}
    st = structure(d, pool)
    name = "Today" if k == "today" else f"Draft {k}"
    meta = [f"{len(st)} sections"]
    if d.get("ask"):
        meta.insert(0, f"{d['ask']} first")
    if d.get("motivation") in MOTIVATIONS:
        meta.insert(0, MOTIVATIONS[d["motivation"]]["label"])
    out = [f'<div class="col{" today" if k == "today" else ""}"><div class="head"><h2>{name}</h2>']
    if d.get("big_idea"):
        out.append(f"<p>{_h(d['big_idea'])}</p>")
    out.append('<div class="meta">' + "".join(f"<span>{_h(m)}</span>" for m in meta) + "</div></div>")
    need = [text[m["point"]] for m in d.get("message_map") or [] if m.get("point") in asks]
    if need:
        out.append('<div class="yes"><b>Needs your yes</b>' + "<br>".join(_h(x) for x in need) + "</div>")
    for s in st:
        says = "".join(f'<p class="says">{_h(text.get(p, p))}</p>' for p in s.get("says") or [])
        holds = "".join(f"<span>{n} {_h(NAMES.get(n, ''))}</span>" for n in s.get("holds") or [])
        out.append(f'<div class="sec"><div class="lab">{_h(s["type"])}</div>{says}'
                   f'{f"<div class=holds>{holds}</div>" if holds else ""}<div class="wf">{wire(s.get("layout"))}</div></div>')
    if k != "today":
        out.append('<div class="always">On every page: ' + ", ".join(f"{n} {NAMES[n]}" for n in ALWAYS) + "</div>")
    return "".join(out) + "</div>"


def render(pool, drafts, today):
    cols = [column(k, d, pool) for k, d in drafts.items()] + ([column("today", today, pool)] if today else [])
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Three drafts</title><link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@600;700&family=Mulish:wght@400;600&display=swap" rel="stylesheet">'
            f'<style>{CSS}</style></head><body><div class="top"><h1>Three drafts, and today</h1>'
            '</div>'
            f'<div class="cols">{"".join(cols)}</div></body></html>')
