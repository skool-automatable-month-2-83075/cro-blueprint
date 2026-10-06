"""The picker's look: the audit report's own chrome (report_html.CSS, so the two dashboards match), the Claude
Series kit for the page inside it, and the thank-you page drawn after the form."""
import html
import json

from audit import report_html as RH
from audit.picker_js import JS

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Mulish:wght@300;400;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">')

# The picker's additions to the audit chrome. Same tokens, same type, same card rhythm.
CHROME = """
.top .views { margin-left:auto; display:inline-flex; background:var(--sand); border-radius:8px; padding:3px; gap:2px; }
.top .views button, .top .dl { border:0; background:transparent; font:600 12.5px system-ui; color:var(--body); padding:6px 12px; border-radius:6px; cursor:pointer; }
.top .views button.on { background:#fff; color:var(--ink); box-shadow:0 1px 2px rgba(0,0,0,.08); }
.top .dl { background:var(--terracotta); color:#fff; }
.stage { max-width:none; background:transparent; box-shadow:none; overflow:visible; }
.frame { position:relative; margin:0 auto; background:#fff; border-radius:6px; overflow:hidden; box-shadow:rgba(0,0,0,.13) 0 8px 40px; }
.frame + .frame { margin-top:28px; }
.scaler { transform-origin:top left; }
.phone .frame { border-radius:22px; }
.sec { position:relative; }
.sec > .n { position:absolute; top:8px; left:8px; z-index:4; min-width:26px; height:22px; padding:0 7px; border-radius:5px; color:#fff; background:var(--none);
  font-family:"JetBrains Mono",ui-monospace,monospace; font-size:12px; display:grid; place-items:center; box-shadow:0 1px 3px rgba(0,0,0,.25); pointer-events:none; }
.sec > .n.keep { background:var(--keep); } .sec > .n.fix { background:var(--fix-line); } .sec > .n.cut { background:var(--cut-line); }
.locked .sec[data-key]:not([data-key=""]) { cursor:pointer; }
.locked .sec[data-key]:not([data-key=""]):hover { box-shadow:inset 0 0 0 3.5px var(--terracotta), 0 0 0 9999px rgba(20,20,19,.32); z-index:5; }
.sec.live { box-shadow:inset 0 0 0 3.5px var(--terracotta); z-index:4; }
.after { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:11px; letter-spacing:1.6px; text-transform:uppercase; color:var(--terracotta); margin:28px 0 10px; }
.btn-lock { margin-top:16px; width:100%; border:0; border-radius:10px; background:var(--terracotta); color:#fff; font:600 14px system-ui; padding:12px; cursor:pointer; }
.rot { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
.rot button { width:34px; height:34px; border-radius:8px; border:1px solid var(--hairline-soft); background:#fff; font-size:16px; cursor:pointer; color:var(--ink); }
.rot .of { font-size:13px; color:var(--body); } .rot .of b { color:var(--ink); font-size:15px; }
.rot .unlock { width:auto; height:auto; border:0; background:none; border-radius:0; }
.secl .num, .opt .num { background:var(--none); } .secl .num.keep, .opt .num.keep { background:var(--keep); } .secl .num.fix, .opt .num.fix { background:var(--fix-line); } .secl .num.cut, .opt .num.cut { background:var(--cut-line); }
.unlock { margin-left:auto; font-size:12.5px; color:var(--terracotta); background:none; border:0; cursor:pointer; text-decoration:underline; }
.bigidea { font-family:"Tiempos Text",Georgia,serif; font-size:19px; line-height:1.35; color:var(--ink); }
.prom { padding:12px 24px; border-top:1px solid var(--hairline); display:grid; gap:8px; } .prom .t { font-size:14px; line-height:1.4; color:var(--ink); }
.yn { display:flex; gap:6px; } .yn button { border:1px solid var(--hairline-soft); background:#fff; border-radius:7px; padding:5px 12px; font:600 12.5px system-ui; color:var(--body); cursor:pointer; }
.yn button.on { background:var(--keep); border-color:var(--keep); color:#fff; } .yn button.on.no { background:var(--fix-line); border-color:var(--fix-line); }
.mapl { padding:2px 24px 12px; } .mapl ol, .mapl ul { margin:4px 0 0 18px; } .mapl li { font-size:13.5px; line-height:1.45; padding:3px 0; color:var(--ink); }
.mapl li em { font-style:normal; font-family:"JetBrains Mono",ui-monospace,monospace; font-size:11px; color:var(--muted); margin-left:4px; }
.opt { padding:12px 24px; border-top:1px solid var(--hairline); cursor:pointer; display:grid; grid-template-columns:auto 1fr auto; gap:10px; align-items:start; }
.opt .l0 { font-size:11.5px; color:var(--muted); margin-bottom:3px; } .opt .lb { font-size:12.5px; color:var(--body); line-height:1.45; margin-top:4px; }
.opt .lu { margin:5px 0 0 16px; font-size:12.5px; color:var(--body); line-height:1.45; } .opt .lu li { margin:2px 0; } .opt .lu b { color:var(--ink); font-weight:600; }
.opt .l1 { font-weight:600; }
.statpick { display:grid; grid-template-columns:auto 1fr; gap:10px; padding:11px 24px; border-top:1px solid var(--hairline); cursor:pointer; font-size:13.5px; line-height:1.4; }
.statpick:hover, .statpick.on { background:#fff; } .statpick input { margin-top:3px; width:16px; height:16px; accent-color:var(--terracotta); }
.statpick b { font-family:"JetBrains Mono",ui-monospace,monospace; } .statpick .needs { display:block; margin-top:6px; }
.more { display:block; width:calc(100% - 48px); margin:10px 24px 4px; border:1px dashed var(--hairline-soft); background:transparent; border-radius:8px; padding:9px;
  font:600 12.5px system-ui; color:var(--body); cursor:pointer; } .more:hover { background:#fff; }
.opt:hover, .opt.on { background:#fff; } .opt.on { box-shadow:inset 3px 0 0 var(--terracotta); }
.opt .l1 { font-size:13.5px; line-height:1.4; color:var(--ink); } .opt .l2 { font-size:11.5px; color:var(--muted); margin-top:3px; }
.opt .sc { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:13px; font-weight:600; }
.ideal { display:inline-block; font-size:10px; letter-spacing:1px; text-transform:uppercase; font-weight:700; padding:1px 6px; border-radius:4px; color:#6b3fa0; background:rgba(107,63,160,.1); margin-right:6px; vertical-align:1px; }
.needs { margin-top:8px; font-size:12px; color:#6b3fa0; background:rgba(107,63,160,.08); padding:6px 9px; border-radius:7px; line-height:1.45; }
.cur { padding:4px 24px 16px; }
.cur .ang { font-size:12px; font-weight:600; color:var(--body); margin-bottom:8px; }
.bars { display:grid; gap:7px; margin-top:10px; }
.bar { display:grid; grid-template-columns:78px 1fr 34px; gap:8px; align-items:center; font-size:12.5px; }
.bar .tr { height:7px; border-radius:4px; background:var(--hairline-soft); overflow:hidden; } .bar .tr i { display:block; height:100%; border-radius:4px; }
.bar .v { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:12px; text-align:right; }
.bar .raw { grid-column:2 / 4; font-size:11.5px; color:var(--muted); margin-top:-4px; }
.who { display:flex; flex-wrap:wrap; gap:4px; margin-top:10px; } .who span { font-size:11.5px; padding:2px 7px; border-radius:99px; }
.who .ok { color:var(--keep); background:var(--keep-bg); } .who .mid { color:var(--fix); background:var(--fix-bg); } .who .bad { color:var(--cut); background:var(--cut-bg); }
.draftnote { font-size:11.5px; color:var(--muted); margin-top:6px; }
.own { padding:6px 24px 18px; } .own label { display:block; font-size:11px; letter-spacing:1px; text-transform:uppercase; color:var(--muted); margin:10px 0 4px; font-weight:600; }
.own textarea { width:100%; min-height:44px; border:1px solid var(--hairline-soft); border-radius:8px; padding:8px 10px; font:13.5px/1.45 system-ui; color:var(--ink); background:#fff; resize:vertical; }
.own button { margin-top:10px; border:0; border-radius:8px; background:var(--ink); color:#fff; font:600 13px system-ui; padding:9px 14px; cursor:pointer; }
.rep { padding:4px 24px 12px; font-size:13px; line-height:1.5; } .rep li { margin:4px 0 0 18px; } .rep .none { color:var(--keep); }
.verify { padding:10px 24px 18px; font-size:13.5px; line-height:1.5; } .verify label { display:flex; gap:10px; align-items:flex-start; cursor:pointer; }
.verify input { margin-top:4px; width:16px; height:16px; accent-color:var(--keep); }
.verify ol { margin:8px 0 0 44px; color:var(--body); font-size:12.5px; }
.secl { padding:9px 24px; border-top:1px solid var(--hairline); display:grid; grid-template-columns:auto 1fr auto; gap:10px; font-size:13px; cursor:pointer; align-items:center; }
.secl:hover { background:#fff; } .secl .sc { font-family:"JetBrains Mono",ui-monospace,monospace; font-size:12px; }
"""

# The Claude Series kit (the same tokens and classes as page B's series.css), scoped under .cs, with container
# queries in place of media queries so the phone view switches layout inside the picker.
KIT = """
.cs { container:page / inline-size; --cs-blue-700:#0341e7; --cs-blue-600:#1355f4; --cs-blue-500:#3b6ffd; --cs-blue-100:#e2eafe; --cs-blue-050:#f1f5ff;
  --cs-tint:#e6f3fa; --cs-ink-900:#111214; --cs-ink-800:#1b1b1b; --cs-ink-700:#33353a; --cs-ink-500:#63666e; --cs-ink-400:#8b8f98; --cs-ink-200:#dcdee3;
  --cs-ink-050:#f8f9fb; --cs-white:#fff; --cs-display:Figtree,"Helvetica Neue",Arial,sans-serif; --cs-body:Mulish,"Helvetica Neue",Arial,sans-serif;
  font-family:var(--cs-body); font-size:15px; line-height:1.52; color:var(--cs-ink-800); background:var(--cs-ink-050); }
.cs *, .cs *::before { box-sizing:border-box; }
.cs h1, .cs h2, .cs h3 { font-family:var(--cs-display); color:var(--cs-ink-900); font-weight:700; margin:0; }
.cs p { margin:0; } .cs ul { margin:0; padding:0; list-style:none; } .cs a { color:inherit; text-decoration:none; }
.cs [data-f]:empty { display:none; }
.cs-wrap { width:100%; max-width:1180px; margin:0 auto; padding-inline:20px; } .cs-narrow { max-width:820px; }
.cs-section { padding-block:64px; } .cs-strip { padding-block:36px; } .cs-pad-hero { padding-block:56px 72px; }
.cs-white { background:#fff; } .cs-center { text-align:center; } .cs-gap-top { margin-top:28px; }
.cs-stack { display:grid; gap:18px; align-content:start; }
.cs-hero-grid, .cs-split { display:grid; gap:36px; align-items:center; }
.cs-grid-3, .cs-grid-4, .cs-grid-6 { display:grid; gap:16px; grid-template-columns:minmax(0,1fr); }
.cs-grid-6 { grid-template-columns:repeat(2, minmax(0,1fr)); margin-top:14px; } .cs-grid-4 { grid-template-columns:repeat(2, minmax(0,1fr)); }
.cs-hero-grid > *, .cs-split > * { min-width:0; }
@container page (min-width:720px) { .cs-wrap { padding-inline:32px; } .cs-grid-3, .cs-grid-6 { grid-template-columns:repeat(3, minmax(0,1fr)); } }
@container page (min-width:960px) { .cs-section { padding-block:96px; } .cs-hero-grid { grid-template-columns:1.05fr .95fr; gap:56px; }
  .cs-split { grid-template-columns:1fr 1fr; gap:64px; } .cs-grid-4 { grid-template-columns:repeat(4, minmax(0,1fr)); } .cs-grid-6 { grid-template-columns:repeat(6, minmax(0,1fr)); } }
.cs-field { background:linear-gradient(to right, var(--cs-blue-500) 0, var(--cs-blue-500) 93%, var(--cs-blue-700) 93%); color:#fff; }
.cs-field h1, .cs-field h2 { color:#fff; }
.cs-label { font-family:var(--cs-display); font-size:12px; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:var(--cs-blue-600); }
.cs-field .cs-label { color:var(--cs-blue-100); }
.cs-hero { font-size:clamp(40px, 6cqi, 76px); line-height:.98; letter-spacing:-.03em; }
.cs-title { font-size:clamp(30px, 3.8cqi, 48px); line-height:1.05; letter-spacing:-.02em; }
.cs-lead { font-size:19px; font-weight:300; line-height:1.5; color:var(--cs-ink-500); max-width:62ch; } .cs-field .cs-lead { color:var(--cs-blue-100); }
.cs-muted { font-size:13.5px; color:var(--cs-ink-500); } .cs-field .cs-muted { color:var(--cs-blue-100); }
.cs-num { font-family:var(--cs-display); font-weight:700; letter-spacing:-.02em; line-height:1; color:var(--cs-ink-900); } .cs-num-xl { font-size:clamp(34px, 4cqi, 52px); margin-bottom:8px; }
.cs-dashes { display:grid; gap:12px; } .cs-dashes li { display:grid; grid-template-columns:18px 1fr; gap:10px; font-size:16px; line-height:1.5; }
.cs-dashes li::before { content:""; height:1.5px; margin-top:.75em; background:var(--cs-blue-500); }
.cs-card { background:#fff; border-radius:28px; box-shadow:0 18px 40px rgba(17,18,20,.10); padding:28px; }
.cs-card-tint { background:var(--cs-tint); border-radius:28px; padding:32px; } @container page (min-width:720px) { .cs-card-tint { padding:48px; } }
.cs-rows { border-top:1px solid var(--cs-ink-200); } .cs-rows:empty { display:none; }
.cs-row { display:grid; gap:6px 40px; padding:20px 0 20px 18px; border-bottom:1px solid var(--cs-ink-200); border-left:3px solid transparent; }
.cs-row:first-child { border-left-color:var(--cs-blue-500); } @container page (min-width:720px) { .cs-row { grid-template-columns:minmax(160px,1fr) 1.4fr; } }
.cs-row-name { font-family:var(--cs-display); font-size:19px; font-weight:700; color:var(--cs-ink-900); } .cs-row-name b { color:var(--cs-blue-500); margin-right:6px; }
.cs-row-body { font-size:15px; font-weight:300; color:var(--cs-ink-500); line-height:1.6; }
.cs-field .cs-rows, .cs-field .cs-row { border-color:rgba(255,255,255,.3); } .cs-field .cs-row:first-child { border-left-color:#fff; }
.cs-field .cs-row-name { color:#fff; } .cs-field .cs-row-name b { color:var(--cs-blue-100); } .cs-field .cs-row-body { color:var(--cs-blue-100); }
.cs-btn { display:inline-flex; align-items:center; justify-content:center; min-height:50px; padding:0 22px; border-radius:12px; font-family:var(--cs-display); font-size:15.5px; font-weight:600; border:1px solid transparent; cursor:pointer; }
.cs-btn-brand { background:var(--cs-blue-500); color:#fff !important; box-shadow:0 10px 24px rgba(59,111,253,.28); } .cs-btn-white { background:#fff; color:var(--cs-blue-600) !important; }
.cs-btn-quiet { background:#fff; color:var(--cs-ink-900) !important; border-color:var(--cs-ink-200); } .cs-field .cs-btn-quiet { background:transparent; color:#fff !important; border-color:rgba(255,255,255,.7); }
.cs-btn-sm { min-height:40px; font-size:14px; padding:0 16px; }
.cs-actions { display:flex; flex-wrap:wrap; gap:12px; width:100%; max-width:560px; margin-top:6px; } .cs-actions > * { flex:1 1 220px; }
.cs-section .cs-actions { margin-top:26px; }
.cs-ticks { display:grid; gap:10px; } .cs-tick { display:flex; align-items:center; gap:10px; font-family:var(--cs-display); font-weight:600; }
.cs-faces { display:flex; align-items:center; gap:12px; flex-wrap:wrap; } .cs-faces img { width:38px; height:38px; border-radius:50%; object-fit:cover; border:2px solid #fff; margin-right:-18px; }
.cs-faces img:last-of-type { margin-right:4px; }
.cs-faq { border-top:1px solid var(--cs-ink-200); } .cs-faq details { border-bottom:1px solid var(--cs-ink-200); padding:18px 0; }
.cs-faq summary { cursor:pointer; list-style:none; display:flex; justify-content:space-between; gap:16px; font-family:var(--cs-display); font-size:17px; font-weight:600; color:var(--cs-ink-900); }
.cs-faq summary::-webkit-details-marker { display:none; } .cs-faq summary::after { content:"+"; color:var(--cs-blue-500); font-weight:700; }
.cs-faq p { margin-top:10px; font-weight:300; color:var(--cs-ink-500); line-height:1.6; }
.cs-video { margin:0; } .cs-thumb { position:relative; border-radius:14px; overflow:hidden; aspect-ratio:16/9; background:#000; } .cs-thumb img { width:100%; height:100%; object-fit:cover; display:block; }
.cs-play { position:absolute; inset:0; display:grid; place-items:center; color:#fff; } .cs-play svg { width:54px; height:54px; background:rgba(0,0,0,.45); border-radius:50%; padding:14px; }
.cs-video figcaption { display:grid; margin-top:10px; font-size:14px; } .cs-video figcaption span { color:var(--cs-ink-500); } .cs-video figcaption b { color:var(--cs-blue-600); font-family:var(--cs-display); }
.cs-quote { margin:0; padding:24px; display:grid; gap:16px; align-content:space-between; } .cs-quote p { font-size:15.5px; line-height:1.55; }
.cs-quote footer { display:flex; gap:10px; align-items:center; font-size:13px; } .cs-quote footer > span { display:grid; } .cs-quote footer span span { color:var(--cs-ink-500); }
.cs-quote img, .cs-initial { width:40px; height:40px; border-radius:50%; object-fit:cover; display:grid; place-items:center; background:var(--cs-blue-100); color:var(--cs-blue-600); font-weight:700; }
.cs-form form { display:grid; gap:10px; } .cs-form label { display:grid; gap:4px; font-family:var(--cs-display); font-size:13px; font-weight:600; color:var(--cs-ink-700); }
.cs-form input { height:46px; border:1px solid var(--cs-ink-200); border-radius:12px; padding:0 14px; font:15px var(--cs-body); }
.cs-form .cs-btn { width:100%; margin-top:6px; } .cs-fine { font-size:11.5px; color:var(--cs-ink-500); line-height:1.45; }
.cs-top { background:#fff; border-bottom:1px solid var(--cs-ink-200); } .cs-top-in { display:flex; align-items:center; justify-content:space-between; height:68px; }
.cs-mark { font-family:var(--cs-display); font-weight:700; letter-spacing:.2em; font-size:13px; color:var(--cs-ink-900); }
.cs-legal { background:var(--cs-ink-900); color:rgba(255,255,255,.72); font-size:12.5px; padding:18px 0; }
.cs-mbar { display:none; }
@container page (max-width:719px) { .cs-mbar { display:grid; grid-template-columns:1fr 1fr; gap:8px; position:sticky; bottom:0; padding:10px; background:#fff; border-top:1px solid var(--cs-ink-200); z-index:6; }
  .cs-mbar a { display:grid; place-items:center; min-height:48px; border-radius:12px; font-family:var(--cs-display); font-weight:600; background:var(--cs-blue-500); color:#fff; }
  .cs-mbar a + a { background:#fff; color:var(--cs-ink-900); border:1px solid var(--cs-ink-200); } .cs-field { background:var(--cs-blue-500); } }
/* The three looks. Paper: white, ink type, blue only on buttons and labels. Field: the brand-blue duotone. Ink: dark. */
.cs-paper { background:#fff; border-bottom:1px solid var(--cs-ink-200); } .cs-paper .cs-hero { color:var(--cs-ink-900); }
.cs-tintband { background:var(--cs-tint); }
.cs-ink { background:#111214 !important; } .cs-ink .cs-label { color:#8fb0ff; } .cs-ink .cs-lead, .cs-ink .cs-muted { color:#b8bcc4; }
.cs-ink .cs-btn-white { background:var(--cs-blue-500); color:#fff !important; }
.cs-hero-sm { font-size:clamp(34px, 4.6cqi, 60px); }
.cs-centre { text-align:center; } .cs-mid { margin-inline:auto; justify-items:center; } .cs-centre .cs-actions { justify-content:center; margin-inline:auto; }
.cs-centre .cs-ticks { justify-items:center; } .cs-centre .cs-faces, .cs-centre .bg-row { justify-content:center; } .cs-wide { margin-top:40px; }
.cs-tight { padding-block:48px !important; }
.cs-compact { display:grid; gap:20px 48px; } @container page (min-width:960px) { .cs-compact { grid-template-columns:140px 1fr; } }
.cs-brow { display:grid; gap:24px 40px; align-items:center; } @container page (min-width:960px) { .cs-brow { grid-template-columns:120px 1.4fr 1fr; } }
.cs-bignum { font-family:var(--cs-display); font-weight:700; font-size:clamp(56px, 7cqi, 96px); line-height:.9; letter-spacing:-.04em; color:var(--cs-blue-500); }
.cs-bignum-ink { color:var(--cs-ink-900); }
.cs-title-sm { font-size:clamp(26px, 3cqi, 38px); }
/* Placeholders, drawn as Slot.tsx draws them on the dev server */
.ph { min-width:0; overflow:hidden; border-radius:4px; display:grid; place-items:center; padding:20px; text-align:center; border:1px dashed #8b8f98; background:#f4f5f7; }
.ph-in { display:grid; gap:7px; justify-items:center; max-width:38ch; color:#63666e; } .ph-in strong { font-size:14px; font-weight:600; color:#1b1b1b; }
.ph-in span { font-size:12.5px; line-height:1.45; } .ph-in em { font-size:12px; line-height:1.4; }
.ph-blue { border-color:rgba(255,255,255,.55); background:rgba(255,255,255,.05); } .ph-blue .ph-in, .ph-blue .ph-in strong { color:#fff; } .ph-blue .ph-in span, .ph-blue .ph-in em { color:rgba(255,255,255,.78); }
.ph-pill { display:inline-flex; align-items:center; padding:4px 10px; border:1px dashed currentColor; border-radius:8px; font-size:12.5px; font-weight:600; font-family:var(--cs-display); opacity:.92; }
.ph-tag { position:absolute; top:-12px; right:0; z-index:3; padding:4px 10px; border-radius:999px; background:#111214; color:#fff; font-size:10.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; white-space:nowrap; }
.ph-br { outline:1.5px dashed currentColor; outline-offset:2px; border-radius:4px; }
/* Review badges: native, one line, only as many as fit (ReviewBadge.tsx) */
.bg-wrap { position:relative; padding-top:6px; } .bg-row { display:flex; flex-wrap:wrap; align-items:center; row-gap:40px; height:46px; overflow:hidden; }
.bg-cell { display:inline-flex; padding-right:22px; } .bg-cell + .bg-cell { padding-left:22px; border-left:1px solid #dcdee3; } .bg-dark .bg-cell + .bg-cell { border-left-color:rgba(255,255,255,.28); }
.bg { display:inline-flex; align-items:center; gap:10px; height:46px; white-space:nowrap; font-family:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif; }
.bg-mark { width:30px; height:30px; border-radius:50%; display:grid; place-items:center; flex:0 0 auto; font-size:17px; line-height:1; }
.bg-txt { display:grid; gap:3px; font-size:12.5px; line-height:1; } .bg-top { display:inline-flex; align-items:center; gap:7px; } .bg-top strong { font-size:16px; }
.bg-star { position:relative; font-size:16px; line-height:1; } .bg-star i { position:absolute; left:0; top:0; overflow:hidden; font-style:normal; }
.bg-box { position:relative; width:15px; height:15px; display:inline-grid; place-items:center; overflow:hidden; margin-right:2px; } .bg-box i { position:absolute; inset:0; }
.bg-box b { position:relative; color:#fff; font-size:12px; line-height:1; }
"""


def thanks(PG, ask):
    """The thank-you page, drawn after the form. The form's answers carry into it (data-sync), live.
    Its steps are the business's own (proof.json "next_steps"), or three plain ones."""
    call = ask == "call"
    steps = [tuple(x) for x in PG.BIZ["next_steps"]] or [("Now", "We have your details."), ("Next", "A person gets back to you."),
                                                         ("Then", "You decide, with everything in front of you.")]
    rows = "".join(f'<div class="cs-row"><div class="cs-row-name"><b>{i:02d}</b>{html.escape(a)}</div><div class="cs-row-body">{html.escape(b)}</div></div>'
                   for i, (a, b) in enumerate(steps, 1))
    got = html.escape(PG.BIZ["lead_magnet"]) if PG.BIZ["lead_magnet"] else "What we promised"
    line = ('We will call you at <span data-sync="phone">your number</span> ' + PG.pill("how fast you call back, once it is real") + '.'
            if call else f'{got[:1].upper() + got[1:]} is on its way to <span data-sync="email">your email</span>.')
    return (f'<div class="after">After the form · the thank-you page</div><div class="frame"><div class="scaler"><div class="cs">'
            f'<header class="cs-top"><div class="cs-wrap cs-top-in"><span class="cs-mark">{html.escape(PG.name().upper())}</span>'
            f'<a class="cs-btn cs-btn-brand cs-btn-sm" href="{PG.tel()}">{html.escape(PG.call_label())}</a></div></header>'
            f'<section class="cs-field"><div class="cs-wrap cs-section"><div class="cs-split"><div class="cs-stack">'
            f'<h1 class="cs-hero">Thanks, <span data-sync="first">your first name</span>.</h1><p class="cs-lead">{line}</p>'
            f'<div class="cs-rows">{rows}</div></div>'
            + PG.slot("Calendar · book the call now", "Your booking calendar, so they can pick a time instead of waiting.", "", True, "4 / 3", "file")
            + '</div></div></section><footer class="cs-legal"><div class="cs-wrap">No menu on this page. One number to call, and nothing else to click.</div></footer>'
            '</div></div></div>')


def own_kit(kit):
    """The owner's own design kit, laid over the default one (Jono, 5 October 2026: "use the same design kit as
    their own website"). It comes from the page's drafts/kit.json, never from this file:
      {"name", "fonts": "<a stylesheet URL>", "tokens": {"--cs-blue-500": "#..."}, "css": "rules scoped under .cs"}
    Returns the font link and the style rules. With no kit.json both are empty and the default kit shows."""
    if not kit:
        return "", ""
    link = f'<link href="{html.escape(kit["fonts"], quote=True)}" rel="stylesheet">' if kit.get("fonts") else ""
    tokens = " ".join(f"{k}:{v};" for k, v in (kit.get("tokens") or {}).items())
    return link, f'\n.cs {{ {tokens} }}\n{kit.get("css", "")}\n'


def document(data, pages, kit=None):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    kit_fonts, kit_rules = own_kit(kit)
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<title>Page picker</title>{FONTS}{kit_fonts}<style>{RH.CSS}{CHROME}{KIT}{kit_rules}</style></head><body>'
            f'<div class="top"><span class="mark display">{RH.MARK}Page picker</span><span class="url">/lp/{html.escape(data["slug"].replace("localhost-lp-", ""))}</span>'
            '<span class="views"><button data-view="desktop" class="on">Computer</button><button data-view="phone">Phone</button></span>'
            '<button class="dl" id="dl">Download my picks</button></div>'
            f'<div class="grid"><div class="pane"><div class="stage" id="stage">{pages}</div></div><aside class="side" id="side"></aside></div>'
            f'<script type="application/json" id="picker-data">{payload}</script>'
            f'<script>{JS}</script></body></html>')
