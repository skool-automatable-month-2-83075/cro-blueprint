"""audit.html - the owner's page, cut into sections, each one kept, fixed or cut.

One view, everything said once (Jono, 27 September 2026):
  - the top line: how many of the 21 are in place, how many sections to cut, what to add
  - "Do these first": the three moves that matter most
  - the page itself, one numbered box per section: green keep, amber fix, red cut
  - the sidebar, in the same order as the boxes: one card per section, with the components
    it holds ticked or crossed and up to three notes quoting the exact words
  - "Across the page": things true of the whole page, said once, naming the sections
  - "Add": components the page has nowhere for yet, each with where it goes

Nothing is written here until every section has a verdict. Before that, the page says it
is not finished, so a half-built report can never be mistaken for the real one.
"""
import html
import os
from datetime import date

from .eighteen import GROUPS

CSS = """
* { box-sizing:border-box; margin:0; padding:0; }
:root { --canvas:#f5f4ed; --ivory:#faf9f5; --sand:#e8e6dc; --ink:#141413; --body:#5e5d59; --muted:#87867f;
  --hairline:#f0eee6; --hairline-soft:#e8e6dc; --terracotta:#c96442; --coral:#d97757;
  --keep:#3d7a4a; --keep-bg:rgba(61,122,74,.09); --fix:#b8860b; --fix-line:#d4a017; --fix-bg:rgba(212,160,23,.12);
  --cut:#b53333; --cut-line:#d13b3b; --cut-bg:rgba(181,51,51,.08); --none:#87867f; }
html, body { height:100%; }
body { background:var(--canvas); color:var(--ink); font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",Arial,sans-serif; -webkit-font-smoothing:antialiased; overflow:hidden; }
.display { font-family:"Tiempos Text",Georgia,serif; font-weight:500; }
.mono { font-family:"JetBrains Mono",ui-monospace,Menlo,monospace; }
.top { height:56px; display:flex; align-items:center; gap:16px; padding:0 22px; border-bottom:1px solid var(--hairline-soft); background:var(--ivory); }
.top .mark { display:inline-flex; align-items:center; gap:8px; font-size:17px; color:var(--ink); } .top .mark svg { color:var(--terracotta); }
.top .url { font-size:13px; color:var(--body); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.top .date { margin-left:auto; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); }
.grid { display:grid; grid-template-columns:minmax(0,1fr) 430px; height:calc(100% - 56px); }
.pane { overflow:auto; background:var(--sand); padding:28px 44px 60px; }
.stage { position:relative; margin:0 auto; max-width:1180px; background:#fff; border-radius:6px; overflow:hidden; box-shadow:rgba(0,0,0,.13) 0 8px 40px; }
.stage img { display:block; width:100%; }
.bx { position:absolute; left:.5%; width:99%; display:block; text-decoration:none; border-radius:5px; box-shadow:inset 0 0 0 2.5px var(--c), inset 0 0 0 4.5px rgba(255,255,255,.85); transition:box-shadow .12s, background .12s; }
.bx.sub { left:auto; width:auto; border-radius:4px; box-shadow:inset 0 0 0 2.5px var(--c), 0 0 0 2px rgba(255,255,255,.85); }
.bx.keep { --c:var(--keep); } .bx.fix { --c:var(--fix-line); } .bx.cut { --c:var(--cut-line); background:repeating-linear-gradient(135deg, rgba(209,59,59,.10) 0 10px, rgba(209,59,59,0) 10px 20px); } .bx.none { --c:var(--none); }
.bx .tag { position:absolute; top:6px; left:6px; min-width:24px; height:22px; padding:0 7px; border-radius:5px; background:var(--c); color:#fff; font-family:"JetBrains Mono",ui-monospace,monospace; font-size:12px; font-weight:500; display:grid; place-items:center; box-shadow:0 1px 3px rgba(0,0,0,.25); }
.bx.sub .tag { top:-11px; left:-11px; min-width:26px; height:20px; font-size:11px; }
.bx:hover, .bx.live { box-shadow:inset 0 0 0 3.5px var(--c), inset 0 0 0 5.5px rgba(255,255,255,.9), 0 0 0 9999px rgba(20,20,19,.42); z-index:5; }
.follow { position:absolute; border:2px dashed rgba(61,122,74,.75); border-radius:10px; pointer-events:none; }
.follow span { position:absolute; left:50%; transform:translateX(-50%); white-space:nowrap; width:fit-content; font-size:12px; font-weight:600; color:#fff; background:rgba(61,122,74,.92); padding:5px 10px; border-radius:6px; }
.side { overflow-y:auto; background:var(--ivory); border-left:1px solid var(--hairline-soft); }
.sum { padding:22px 24px 20px; border-bottom:1px solid var(--hairline-soft); }
.mode.draft { background:var(--fix-bg); }
.mode { font-size:13.5px; line-height:1.5; color:var(--ink); background:var(--cut-bg); border-radius:10px; padding:10px 12px; margin-bottom:16px; }
.big { display:flex; align-items:baseline; gap:10px; } .big .n { font-size:46px; letter-spacing:-1.5px; line-height:1; } .big .k { font-size:14px; color:var(--body); }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
.chip { font-size:12.5px; font-weight:600; padding:4px 10px; border-radius:99px; }
.chip.fix { background:var(--fix-bg); color:var(--fix); } .chip.add { background:rgba(20,20,19,.06); color:var(--ink); } .chip.cut { background:var(--cut-bg); color:var(--cut); } .chip.keep { background:var(--keep-bg); color:var(--keep); }
.first { margin-top:18px; } .first h3, .grp { font-size:11px; letter-spacing:1.6px; text-transform:uppercase; color:var(--terracotta); font-family:"JetBrains Mono",ui-monospace,monospace; font-weight:500; }
.first ol { margin:10px 0 0 18px; } .first li { font-size:14px; line-height:1.45; padding:4px 0; }
.grp { padding:20px 24px 8px; }
.card { padding:15px 24px 17px; border-top:1px solid var(--hairline); cursor:pointer; scroll-margin-top:12px; }
.card:hover, .card.lit { background:#fff; } .card.lit { box-shadow:inset 3px 0 0 var(--terracotta); }
.card header { display:grid; grid-template-columns:auto 1fr auto; gap:10px; align-items:start; }
.num { min-width:26px; height:22px; padding:0 6px; border-radius:5px; color:#fff; font-family:"JetBrains Mono",ui-monospace,monospace; font-size:12px; display:grid; place-items:center; margin-top:1px; }
.keep .num, .num.keep { background:var(--keep); } .fix .num, .num.fix { background:var(--fix-line); } .cut .num, .num.cut { background:var(--cut-line); } .none .num { background:var(--none); }
.is { font-size:15px; font-weight:600; line-height:1.3; }
.vd { font-size:11px; letter-spacing:1.2px; text-transform:uppercase; font-weight:600; padding:3px 8px; border-radius:99px; margin-top:1px; white-space:nowrap; }
.keep .vd { color:var(--keep); background:var(--keep-bg); } .fix .vd { color:var(--fix); background:var(--fix-bg); } .cut .vd { color:var(--cut); background:var(--cut-bg); }
.hd { font-size:12.5px; color:var(--muted); margin:4px 0 0 36px; font-style:italic; }
.why { font-size:13.5px; color:var(--body); line-height:1.5; margin:7px 0 0 36px; }
.lines { list-style:none; margin:10px 0 0 36px; }
.lines li { display:grid; grid-template-columns:auto 1fr; gap:9px; font-size:13px; line-height:1.45; padding:5px 0; border-top:1px solid var(--hairline); }
.lines li:first-child { border-top:0; }
.st { font-size:10px; letter-spacing:1px; text-transform:uppercase; font-weight:700; padding:2px 6px; border-radius:4px; height:fit-content; margin-top:1px; white-space:nowrap; }
.st.ok { color:var(--keep); background:var(--keep-bg); } .st.weak { color:var(--fix); background:var(--fix-bg); } .st.missing { color:var(--cut); background:var(--cut-bg); } .st.unchecked { color:var(--body); background:rgba(20,20,19,.06); }
.st.sub { color:#fff; background:var(--fix-line); } .st.sub.keep { background:var(--keep); }
.lines b { font-weight:600; color:var(--ink); } .lines span.nt { color:var(--body); }
.notes { margin:10px 0 0 36px; }
.note { padding:8px 0 0; } .note q { display:block; font-size:12.5px; color:var(--muted); font-style:italic; quotes:none; }
.note p { font-size:13px; color:var(--body); line-height:1.45; margin-top:2px; }
.rw { margin:12px 0 0 36px; border-top:1px solid var(--hairline); padding-top:10px; }
.rw h4 { font-size:10.5px; letter-spacing:1.4px; text-transform:uppercase; color:var(--muted); font-weight:600; margin-bottom:4px; }
.rw .pair { display:grid; grid-template-columns:52px 1fr; gap:2px 8px; font-size:13px; line-height:1.45; padding:7px 0; border-top:1px solid var(--hairline); }
.rw .pair:first-of-type { border-top:0; }
.rw .lb { font-size:10px; letter-spacing:1px; text-transform:uppercase; font-weight:700; padding-top:2px; }
.rw .lb.b { color:var(--muted); } .rw .lb.a { color:var(--keep); }
.rw .bf { color:var(--muted); text-decoration:line-through; text-decoration-color:rgba(135,134,127,.5); } .rw .af { color:var(--ink); }
.st.na { color:var(--muted); background:rgba(20,20,19,.04); }
.note .tag { display:inline-block; font-size:10px; letter-spacing:1px; text-transform:uppercase; font-weight:700; padding:1px 6px; border-radius:4px; margin-right:7px; vertical-align:1px; color:var(--fix); background:var(--fix-bg); }
.note .t-keep { color:var(--keep); background:var(--keep-bg); } .note .t-cut, .note .t-typo { color:var(--cut); background:var(--cut-bg); }
.note .t-add, .note .t-swap, .note .t-move { color:var(--ink); background:rgba(20,20,19,.07); }
.glance { padding:4px 24px 8px; }
.gl { padding:10px 0; border-top:1px solid var(--hairline); } .gl:first-child { border-top:0; }
.gi { font-size:13px; line-height:1.45; padding:6px 0 0; } .gi b { font-weight:600; }
.gn { font-size:12.5px; color:var(--body); margin-top:2px; }
.gh { font-size:14px; padding-bottom:2px; } .gh b { font-weight:700; }
.gi .st { font-size:9.5px; padding:1px 6px; margin-right:4px; vertical-align:1px; }
.gl .wh { color:var(--muted); font-size:11.5px; }
.drop { margin:8px 0 0 36px; font-size:12.5px; line-height:1.45; padding:6px 9px; border-radius:7px; }
.drop b { font-weight:700; } .drop span { color:var(--body); }
.drop.lo { background:var(--keep-bg); } .drop.lo b { color:var(--keep); }
.drop.mid { background:var(--fix-bg); } .drop.mid b { color:var(--fix); }
.drop.hi { background:var(--cut-bg); } .drop.hi b { color:var(--cut); }
.copy { margin:10px 0 0 36px; list-style:none; display:grid; gap:3px; }
.copy li { position:relative; padding-left:16px; font-size:12.5px; line-height:1.45; color:var(--body); }
.copy li:before { content:""; position:absolute; left:2px; top:.5em; width:7px; height:7px; border-radius:50%; }
.copy li b { font-weight:600; color:var(--ink); }
.copy .okc:before { background:var(--keep); } .copy .bad:before { background:var(--cut-line); }
.copy .bad { color:var(--cut); } .copy .bad b { color:var(--cut); }
.anat { margin:8px 0 0 36px; display:flex; flex-wrap:wrap; gap:4px; }
.anat span { font-size:11px; padding:2px 7px; border-radius:99px; }
.anat .has { color:var(--keep); background:var(--keep-bg); } .anat .not { color:var(--cut); background:var(--cut-bg); text-decoration:line-through; text-decoration-color:rgba(181,51,51,.45); }
.fillline { margin:8px 0 0 36px; font-size:12px; color:var(--fix); background:var(--fix-bg); padding:6px 9px; border-radius:7px; line-height:1.45; }
.fillline:before { content:"FILL  "; font-weight:700; letter-spacing:1px; font-size:10px; }
.vfacts { font-size:12px; color:var(--body); margin:6px 0 0 36px; font-family:"JetBrains Mono",ui-monospace,monospace; }
.meas { font-size:12px; color:var(--cut); margin:6px 0 0 36px; font-weight:600; }
.rw .gr { display:inline-block; margin-left:6px; font-size:10.5px; color:var(--muted); font-family:"JetBrains Mono",ui-monospace,monospace; text-decoration:none; white-space:nowrap; }
.count { font-size:12.5px; color:var(--body); margin-top:8px; line-height:1.5; }
.item { padding:12px 24px; border-top:1px solid var(--hairline); display:grid; grid-template-columns:auto 1fr; gap:10px; }
.item .t { font-size:14px; font-weight:600; } .item .d { font-size:13px; color:var(--body); line-height:1.45; margin-top:2px; }
.foot { padding:24px; font-size:12px; color:var(--muted); }
.unfinished { max-width:620px; margin:60px auto; background:var(--ivory); border-radius:16px; padding:32px 36px; box-shadow:rgba(0,0,0,.05) 0 4px 24px; }
.unfinished h1 { font-size:28px; letter-spacing:-.5px; } .unfinished p { color:var(--body); margin-top:10px; line-height:1.55; } .unfinished li { color:var(--body); margin:4px 0 0 18px; font-size:14px; }
@media (max-width:980px) { body { overflow:auto; } .grid { display:flex; flex-direction:column; height:auto; } .side { order:-1; border-left:0; overflow:visible; } .pane { padding:16px; overflow:visible; }
  .top .url, .top .date { display:none; } .card header { grid-template-columns:auto 1fr; } .card .vd { grid-column:2; justify-self:start; } }
"""

JS = """<script>
(function () {
  var pane = document.querySelector('.pane'), side = document.querySelector('.side');
  function clear() {
    document.querySelectorAll('.bx.live').forEach(function (b) { b.classList.remove('live'); });
    document.querySelectorAll('.card.lit').forEach(function (c) { c.classList.remove('lit'); });
  }
  function show(id, scrollPane) {
    clear();
    var box = document.getElementById('box-' + id);
    var card = document.getElementById('card-' + id.split('-')[0]);
    if (box) {
      box.classList.add('live');
      if (scrollPane && pane) {
        var r = box.getBoundingClientRect(), p = pane.getBoundingClientRect();
        var inView = r.top >= p.top && r.top + Math.min(r.height, p.height) <= p.bottom;
        if (!inView) {
          var want = pane.scrollTop + (r.top - p.top) - (r.height > p.height * 0.9 ? 24 : (p.height - r.height) / 2);
          pane.scrollTo({ top: Math.max(0, want), behavior: 'smooth' });
        }
      }
    }
    if (card) card.classList.add('lit');
  }
  document.querySelectorAll('[data-box]').forEach(function (el) {
    el.addEventListener('mouseenter', function () { show(el.dataset.box, true); });
    el.addEventListener('mouseleave', clear);
    el.addEventListener('click', function (ev) { ev.stopPropagation(); show(el.dataset.box, true); });
  });
  document.querySelectorAll('.bx').forEach(function (box) {
    var id = box.id.replace('box-', '');
    box.addEventListener('mouseenter', function () { show(id, false); });
    box.addEventListener('mouseleave', clear);
    box.addEventListener('click', function (ev) {
      ev.preventDefault(); show(id, false);
      var card = document.getElementById('card-' + id.split('-')[0]);
      if (card) card.scrollIntoView({ block: 'start', behavior: 'smooth' });
    });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') clear(); });
})();
</script>"""

MARK = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M12 2 L13.4 10.6 L22 12 L13.4 13.4 L12 22 L10.6 13.4 L2 12 L10.6 10.6 Z"/></svg>'
VERDICT_WORD = {"keep": "Keep", "fix": "Fix", "cut": "Cut"}
STATUS_WORD = {"ok": "In place", "weak": "Fix", "missing": "Missing", "unchecked": "Not checked", "n/a": "Not needed"}
STATUS_CLASS = {"ok": "ok", "weak": "weak", "missing": "missing", "unchecked": "unchecked", "n/a": "na"}


def e(s):
    return html.escape(str(s if s is not None else ""))


def _head(title):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{e(title)}</title>'
            f'<style>{CSS}</style></head><body>')


def _topbar(url, today):
    return (f'<div class="top"><span class="mark display">{MARK}Landing page audit</span>'
            f'<span class="url">{e(url)}</span><span class="date">{e(today)}</span></div>')


def write_unfinished(out_dir, url, problems, n_bands):
    """Nothing half-built is ever shown as the report. This says so, plainly."""
    today = date.today().strftime("%d %B %Y")
    H = [_head("Audit not finished"), _topbar(url, today),
         '<div class="unfinished"><h1 class="display">Not finished yet</h1>',
         f'<p>The page was cut into {n_bands} sections. The report is written once every one of them has been '
         'read and given a verdict. What is still open:</p><ul>']
    H += [f"<li>{e(p)}</li>" for p in problems[:30]]
    H.append("</ul></div></body></html>")
    path = os.path.join(out_dir, "audit.html")
    open(path, "w").write("\n".join(H))
    return path


def _card(c, mode):
    tone = c["verdict"] or "none"
    word = "Leave out" if (tone == "cut" and mode == "homepage") else VERDICT_WORD.get(tone, "")
    H = [f'<article class="card {tone}" id="card-{c["id"]}" data-box="{c["id"]}">',
         f'<header><span class="num">{c["n"]}</span><div class="is">{e(c["is"])}</div>'
         f'<span class="vd">{e(word)}</span></header>']
    if c["heading"] and c["kind"] not in ("nav", "footer") and c["heading"].strip().lower() not in c["is"].lower():
        H.append(f'<div class="hd">"{e(c["heading"][:90])}"</div>')
    if c.get("repeats"):
        H.append(f'<p class="meas">Repeats section {e(c["repeats"])}</p>')
    if c["why"]:
        H.append(f'<p class="why">{e(c["why"])}</p>')
    ig = c.get("image_grade")
    if isinstance(ig, (int, float)) and tone != "cut":
        il = "lo" if ig >= 7 else ("mid" if ig >= 4 else "hi")
        H.append(f'<p class="drop {il}"><b>Pictures: {ig:g}/10</b>' + (f' <span>{e(c["image_why"])}</span>' if c.get("image_why") else "") + "</p>")
    d = c.get("drop_off")
    if isinstance(d, (int, float)):
        level = "lo" if d <= 3 else ("mid" if d <= 6 else "hi")
        H.append(f'<p class="drop {level}"><b>Risk of losing them: {d:g}/10</b>'
                 + (f' <span>{e(c["drop_off_why"])}</span>' if c.get("drop_off_why") else "") + "</p>")
    ch = c.get("chain") or {}
    if tone != "cut" and ch.get("lines") and c["kind"] in ("hero", "body", "steps", "form", "pricing"):
        g = c.get("grade")
        g_bad, l_bad, c_bad = (g or 0) > 10, bool(c.get("long")), ch.get("verdict") != "reaches the outcome"
        chain_txt = {"mostly features": f'{ch["features"]} of {ch["lines"]} lines are bare features',
                     "benefits, no outcomes": f'benefits, but no line says what it leads to',
                     "few outcomes": f'only {ch["outcomes"]} of {ch["lines"]} lines reach the outcome',
                     "reaches the outcome": f'{ch["outcomes"]} of {ch["lines"]} lines reach the outcome'}.get(ch["verdict"], "")
        # a bullet list, one measure per line (Jono, 1 Oct 2026): what was measured, then the reading
        chain_show = chain_txt[0].upper() + chain_txt[1:] if chain_txt else ""
        H.append('<ul class="copy">'
                 + (f'<li class="{"bad" if g_bad else "okc"}"><b>Reading level:</b> grade {g:g}'
                    f'{", over the grade 10 limit" if g_bad else ""}</li>' if g is not None else "")
                 + f'<li class="{"bad" if l_bad else "okc"}"><b>Length:</b> {c["words"]} words'
                   f'{", over the limit of " + str(c["limit"]) if l_bad else ", within the limit of " + str(c["limit"])}</li>'
                 + f'<li class="{"bad" if c_bad else "okc"}"><b>Copy:</b> {e(chain_show)}</li></ul>')
    meas = []
    if c.get("long") and tone != "cut":
        counted = bool((c.get("chain") or {}).get("lines")) and c["kind"] in ("hero", "body", "steps", "form", "pricing")
        lead = "" if counted else f'{c["words"]} words, over the {c["limit"]} people read here: '
        if c.get("few_bullets") and c["kind"] not in ("proof_quotes", "faq"):
            meas.append(lead + "people skip most paragraphs, so turn it into three to five bullets and put the detail under a Read more")
        elif c["kind"] == "proof_quotes" and c.get("has_read_more"):
            pass   # the long reviews are already cut short with a Read more: nothing to fix
        elif c["kind"] == "proof_quotes":
            meas.append(f'{c["words"]} words: keep every review, but cut the long ones to their best line with a Read more')
        else:
            meas.append(lead + "keep the persuasive lines, put the detail under a Read more")
    if (c.get("grade") or 0) > 10 and tone != "cut" and not ch.get("lines"):
        meas.append(f'reads at grade {c["grade"]:g}, over grade 10')
    if c.get("no_graphic") and tone != "cut":
        meas.append("no picture or graphic: show it rather than describe it")
    if c.get("echoes") and tone != "cut":
        n_e = len(c["echoes"])
        meas.append((f'{n_e} boxes say their title twice, starting' if n_e > 1 else "one box says its title twice:")
                    + f' "{c["echoes"][0]["title"]}"')
    if meas:
        line = " · ".join(meas)
        H.append(f'<p class="meas">{e(line[0].upper() + line[1:])}</p>')
    if c.get("placeholders") and tone != "cut":
        H.append('<p class="fillline">' + " · ".join(e(x) for x in c["placeholders"]) + "</p>")
    if c.get("anatomy") and tone != "cut":
        H.append('<p class="anat">' + "".join(f'<span class="{"has" if ok_ else "not"}">{e(name)}</span>' for name, ok_ in c["anatomy"]) + "</p>")
    if c.get("video_facts") and tone != "cut":
        H.append(f'<p class="vfacts">{e(c["video_facts"][0].upper() + c["video_facts"][1:])}</p>')
    lines = []
    for key, tag in (("eyebrow", "a"), ("headline", "b"), ("subheadline", "c")):
        x = c.get(key) or {}
        if (x.get("says") or "").strip():
            good = (x.get("verdict") or "").lower() == "good"
            label = {"eyebrow": "The line above the headline", "headline": "The headline",
                     "subheadline": "The line under the headline"}[key]
            if c.get(f"has_{key}_box"):
                lines.append(f'<li data-box="{c["id"]}-{key}"><span class="st sub{" keep" if good else ""}">{c["n"]}{tag}</span>'
                             f'<div><b>{label}.</b> <span class="nt">{e(x["says"])}</span></div></li>')
            else:
                lines.append(f'<li><span class="st {"ok" if good else "weak"}">{"Keep" if good else "Fix"}</span>'
                             f'<div><b>{label}.</b> <span class="nt">{e(x["says"])}</span></div></li>')
    if tone != "cut":
        for n in sorted(c["holds"]):
            x = c["holds"][n]
            s = (x.get("status") or "").lower()
            if s not in STATUS_WORD:
                continue
            lines.append(f'<li><span class="st {STATUS_CLASS[s]}">{STATUS_WORD[s]}</span><div><b>{e(x.get("name") or "")}.</b> '
                         f'<span class="nt">{e(x.get("note") or "")}</span></div></li>')
    if lines:
        H.append('<ul class="lines">' + "".join(lines) + "</ul>")
    if c.get("rewrites") and tone != "cut":
        H.append('<div class="rw"><h4>Rewrite these lines</h4>')
        for x in c["rewrites"]:
            gb = f'<span class="gr">grade {x["grade_before"]:g}</span>' if x.get("grade_before") is not None else ""
            ga = f'<span class="gr">grade {x["grade_after"]:g}</span>' if x.get("grade_after") is not None else ""
            H.append(f'<div class="pair"><span class="lb b">Before</span><span class="bf">{e(x["before"])}{gb}</span>'
                     f'<span class="lb a">After</span><span class="af">{e(x["after"])}{ga}</span></div>')
        H.append("</div>")
    auto = []
    if c.get("needs_button") and tone != "cut":
        cta = c.get("main_cta") or "the button that goes to your form"
        auto.append({"tag": "Add", "quote": "", "says": f'No way to act here. Add both: the form button, in the same words as the rest ("{cta}"), '
                                                        'and a phone number people can tap beside it.'})
    if c.get("feature_ticks") and tone != "cut":
        auto.append({"tag": "Swap", "quote": "", "says": "The ticks under the headline list features. In the first screen they should be proof "
                                                         "with numbers: years in business, jobs or clients, the rating with its count, the guarantee."})
    if c.get("bland") and tone != "cut":
        auto.append({"tag": "Add", "quote": "", "says": "Nothing here proves it. Add one piece of proof beside the words: a review badge "
                                                        "like Capterra or Google with the stars, a one-line client quote with a face, or a number."})
    said = " ".join((n.get("says") or "") + " " + (n.get("quote") or "") for n in c["notes"]).lower()
    topics = {"No way to act": ("button", "phone"), "The ticks under": ("tick",), "Nothing here proves": ("proof", "badge", "quote")}
    auto = [a for a in auto if not any(a["says"].startswith(k) and any(w in said for w in ws) for k, ws in topics.items())]
    if (c["notes"] or auto) and tone != "cut":
        c = {**c, "notes": auto + c["notes"]}
        H.append('<div class="notes">')
        for x in c["notes"]:
            q = f'<q>"{e(x.get("quote"))}"</q>' if x.get("quote") else ""
            tag = x.get("tag") or "Fix"
            H.append(f'<div class="note">{q}<p><span class="tag t-{tag.lower()}">{e(tag)}</span>{e(x.get("says"))}</p></div>')
        H.append("</div>")
    H.append("</article>")
    return "".join(H)


def write(out_dir, url, model, cap):
    today = date.today().strftime("%d %B %Y")
    shot = cap["viewports"]["desktop"]["shots"].get("full")
    src = os.path.relpath(shot, out_dir) if shot else ""
    ph, pw = model["page_h"] or 1, model["page_w"] or 1366
    t = model["tally"]
    # the cards carry the names the owner reads; fill them from the components
    for c in model["cards"]:
        for n, x in c["holds"].items():
            x.setdefault("name", model["components"][n]["name"])

    H = [_head("Landing page audit"), _topbar(url, today), '<div class="grid">']
    # ---- the page, marked up
    H.append(f'<div class="pane"><div class="stage"><img src="{e(src)}" alt="Your page">')
    for b in model["boxes"]:
        top, hgt = 100 * b["top"] / ph, 100 * b["h"] / ph
        if b["left"] is None:
            H.append(f'<a class="bx {b["tone"]}" id="box-{b["id"]}" href="#card-{b["id"]}" '
                     f'style="top:calc({top:.4f}% + 3px);height:calc({hgt:.4f}% - 6px)"><span class="tag">{e(b["label"])}</span></a>')
        else:
            H.append(f'<a class="bx sub {b["tone"]}" id="box-{b["id"]}" href="#card-{b["id"].split("-")[0]}" '
                     f'style="top:{top:.4f}%;height:{hgt:.4f}%;left:{100 * b["left"] / pw:.4f}%;width:{100 * b["w"] / pw:.4f}%">'
                     f'<span class="tag">{e(b["label"])}</span></a>')
    # A form that follows the visitor down the page shows only once in a full-page screenshot, with
    # an empty column below it. Draw where it really is, so no one reads the gap as nothing there.
    sf = (cap["viewports"]["desktop"]["facts"].get("stickyForm") or {})
    if sf.get("top") is not None and sf.get("w"):
        start = sf["top"] + (sf.get("h") or 0) + 24
        end = max((c["top"] for c in model["cards"] if c["kind"] == "footer"), default=ph)
        if end - start > 300:
            # a label every screen or so: the picture sits in a clipped box, so a sticky label cannot follow
            span_h = end - start
            labels = "".join(f'<span style="top:{100 * k / span_h:.3f}%">The form follows the visitor down here</span>'
                             for k in range(40, span_h - 60, 1100))
            H.append(f'<div class="follow" style="top:{100 * start / ph:.4f}%;height:{100 * span_h / ph:.4f}%;'
                     f'left:{100 * sf["left"] / pw:.4f}%;width:{100 * sf["w"] / pw:.4f}%">{labels}</div>')
    H.append("</div></div>")

    # ---- the sidebar
    H.append('<aside class="side"><div class="sum">')
    if model.get("draft"):
        H.append(f'<div class="mode draft"><b>Draft.</b> Scored as if every placeholder is filled with the real thing. '
                 f'It cannot go live until the {len(model.get("fill") or [])} placeholder'
                 f'{"s" if len(model.get("fill") or []) != 1 else ""} under "Fill before launch" '
                 f'{"is" if len(model.get("fill") or []) == 1 else "are"} done.</div>')
    if model["mode"] == "homepage":
        H.append('<div class="mode"><b>This is a homepage, not a landing page.</b> For your ads, build a landing '
                 'page from it: keep the green sections, fix the amber ones, leave out the red ones, and add what is listed at the end.</div>')
    # Always out of the whole list, so the number never changes meaning from page to page, and the
    # chips add up to it (Jono, 28 Sep 2026: "where is this 19 coming from?").
    lo = t.get("left_out") or []
    H.append(f'<div class="big"><span class="n display">{t["ok"]} of {t.get("total", t["of"])}</span>'
             '<span class="k">components in place</span></div><div class="chips">')
    if t["weak"]:
        H.append(f'<span class="chip fix">Fix {t["weak"]}</span>')
    if t["missing"]:
        H.append(f'<span class="chip add">Missing {t["missing"]}</span>')
    if lo:
        H.append(f'<span class="chip add">Not counted {len(lo)}</span>')
    if t["cut"]:
        H.append(f'<span class="chip cut">{"Leave out" if model["mode"] == "homepage" else "Cut"} {t["cut"]} '
                 f'section{"s" if t["cut"] != 1 else ""}</span>')
    H.append("</div>")
    if lo:
        why = {"n/a": "not needed for your business", "unchecked": "could not be checked from outside"}
        H.append('<p class="count">Not counted: '
                 + "; ".join(f"{e(n[0].lower() + n[1:])}, {why[st]}" for n, st in lo) + ".</p>")
    if model["do_first"]:
        H.append('<div class="first"><h3>Do these first</h3><ol>' +
                 "".join(f"<li>{e(x)}</li>" for x in model["do_first"]) + "</ol></div>")
    H.append("</div>")

    H.append('<div class="grp">Section by section</div>')
    H += [_card(c, model["mode"]) for c in model["cards"]]

    # ONE closing list (Jono, 28 Sep 2026: "Across the page", "Add" and "All 24 at a glance" said the same
    # thing three times). Things to remove come first, then every component grouped by status. One that
    # lives in a section points at it; one that belongs to the whole page, or has nowhere to go yet,
    # carries its note here, because this is the only place it is said.
    num = {c["id"]: c["n"] for c in model["cards"]}
    goes = {c["n"]: c.get("goes") for c in model["add"] if not c.get("in_card")}
    comps = sorted(model["components"].values(), key=lambda c: c["n"])
    H.append(f'<div class="grp">All {len(comps)} at a glance</div><div class="glance">')
    if model.get("fill"):
        H.append(f'<div class="gl"><span class="st weak">Fill before launch {len(model["fill"])}</span>'
                 + "".join(f'<div class="gi"><b>{e(x["what"])}</b> <span class="wh">section {x["n"]}</span></div>' for x in model["fill"])
                 + "</div>")
    if model.get("remove"):
        H.append(f'<div class="gl"><span class="st missing">Remove {len(model["remove"])}</span>'
                 + "".join(f'<div class="gi"><b>{e(r["what"])}</b><div class="gn">{e(r["why"])}</div></div>' for r in model["remove"])
                 + "</div>")
    # the 26 in the course slide's five groups, in the slide's order, each part with its verdict
    # (Jono, 2 Oct 2026: "that slideshow has the right sections, like the way it's categorized")
    by_n = {c["n"]: c for c in comps}
    word = {"ok": ("In place", "ok"), "weak": ("Fix", "weak"), "missing": ("Missing", "missing")}
    for gname, ns in GROUPS:
        rows = [by_n[n] for n in ns if n in by_n]
        if not rows:
            continue
        counted = [c for c in rows if c["status"] in ("ok", "weak", "missing")]
        done = sum(1 for c in counted if c["status"] == "ok")
        H.append(f'<div class="gl"><div class="gh"><b>{e(gname)}</b> <span class="wh">{done} of {len(counted)} in place</span></div>')
        for c in rows:
            label, cls = word.get(c["status"], ("Not counted", "na"))
            w = c["where"]
            if w[0] == "card":
                H.append(f'<div class="gi"><span class="st {cls}">{label}</span> <b>{e(c["name"])}</b> '
                         f'<span class="wh">section {num[w[1]]}</span></div>')
            else:
                note = goes.get(c["n"]) or c.get("note") or ""
                H.append(f'<div class="gi"><span class="st {cls}">{label}</span> <b>{e(c["name"])}</b> <span class="wh">whole page</span>'
                         + (f'<div class="gn">{e(note)}</div>' if note else "") + "</div>")
        H.append("</div>")
    H.append("</div>")
    H.append('<div class="foot">Every section of the page has a box and a card, in the same order. '
             'Hover a card to find its section.</div></aside></div>')
    H.append(JS + "</body></html>")
    path = os.path.join(out_dir, "audit.html")
    open(path, "w").write("\n".join(H))
    return path
