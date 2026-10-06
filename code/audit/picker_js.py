"""The picker's behaviour. Rotate the page types, lock one, click a section, rotate its options or write your own,
watch the whole-page repeat check, sync the form into the thank-you page, verify it, download the picks."""

JS = r"""
(function () {
var D = JSON.parse(document.getElementById('picker-data').textContent);
var STORE = 'picker:' + D.slug, PAGES = Object.keys(D.pages);
var S = { page: PAGES[0], locked: false, picks: {}, own: {}, sel: null, verified: false, view: 'desktop' };
try { var saved = JSON.parse(localStorage.getItem(STORE) || 'null'); if (saved && D.pages[saved.page]) { for (var k in saved) S[k] = saved[k]; } } catch (e) {}
function save() { try { localStorage.setItem(STORE, JSON.stringify(S)); } catch (e) {} }

var NAME = { hero: 'The first screen', logos: 'Client logos', stats: 'The numbers', problem: 'The problem', audit: 'What you get first',
  steps: 'How it works', videos: 'Client videos', reviews: 'Written reviews', terms: 'The terms', faq: 'Questions', close: 'The form', legal: 'The legal line' };
function label(t) { return NAME[t] || (t.indexOf('benefit') === 0 ? 'Benefit ' + t.split('-')[1] : t); }
function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
function br(t) { return esc(t).replace(/\[([^\]]*)\]/g, '<span class="ph-br">[$1]</span>'); }
function tone(v) { return v == null ? '' : v >= 7.5 ? 'keep' : v >= 5 ? 'fix' : 'cut'; }
function colour(v) { return v >= 7.5 ? 'var(--keep)' : v >= 5 ? 'var(--fix-line)' : 'var(--cut-line)'; }
function secs() { return D.pages[S.page].sections; }
function opts(key) { return D.options[key] || []; }
/* The default is the best line that can go live today: an ideal line needs proof first, so it waits one click away. */
function rank(o) { return o.map(function (x, i) { return i; }).sort(function (a, b) { return (!!o[a].ideal - !!o[b].ideal) || (o[b].scores.overall - o[a].scores.overall); }); }
function best(key) { var o = opts(key); return o.length ? rank(o)[0] : null; }
/* The list and the arrows go best first: the overall score, which carries the buyers' read and the four checks. */
var TOP = 3;
/* The best ideal line always makes the top three (Jono, 28 September 2026: "it was a really good idea to show what a good
   headline looks like even if they don't explicitly have the data... this stuff makes a big difference"). */
function ranked(key) {
  var o = opts(key), r = o.map(function (x, i) { return i; }).sort(function (a, b) { return o[b].scores.overall - o[a].scores.overall; });
  var top = r.slice(0, TOP), bestIdeal = r.filter(function (i) { return o[i].ideal; })[0];
  if (bestIdeal != null && !top.some(function (i) { return o[i].ideal; }) && r.length > TOP) {
    r.splice(r.indexOf(bestIdeal), 1); r.splice(TOP - 1, 0, bestIdeal);
  }
  return r;
}
function current(s) {
  if (!s.key) return null;
  if (!S.locked) return s.generic;
  var c = S.picks[s.key];
  if (c === 'own' && S.own[s.key]) return S.own[s.key];
  if (c === -1) return null;
  if (typeof c === 'number' && opts(s.key)[c]) return opts(s.key)[c].fields;
  return s.generic;
}
function currentScores(s) {
  var c = S.picks[s.key];
  if (!S.locked || !s.key || s.special) return null;
  if (c === 'own' && S.own[s.key]) return measure(s.kind, S.own[s.key]);
  if (typeof c === 'number' && opts(s.key)[c]) return opts(s.key)[c].scores;
  return null;
}

/* ---- the four code measures, the same formulas as picker.py measure() ---- */
var LIMIT = D.limits, ABSTRACT = {}, VAGUE = D.vague;
D.abstract.forEach(function (w) { ABSTRACT[w] = 1; });
var OUTCOME = /\b(?:so (?:you|your|that|the|nothing|there|no|every|shoppers|customers|buyers|people)|which means|means (?:you|your|no|more|less)|so they|you(?:'ll| will) (?:get|see|save|have|never|stop)|(?:more|fewer|less) (?:sales|revenue|calls|leads|customers|bookings|jobs|recalls|stops|time|money)|(?:save|saves|saving) (?:you|hours|time|money)|without (?:a|the|any|rebuilding|hiring|paying))\b/i;
var BENEFIT = /\b(?:you|your|you're|yours)\b/i;
var CONCRETE = /\d|\$|\[|\b(?:week|weeks|minute|minutes|hour|hours|day|days|month|months|date|call|calls|phone|email|review|reviews|form)\b/i;
var OWN_WORDS = D.concrete || [];   // the business's own nouns, from the pool's vocabulary
function solid(x) { if (CONCRETE.test(x)) return true; var l = x.toLowerCase(); return OWN_WORDS.some(function (w) { return l.indexOf(w) >= 0; }); }
function flat(f) {
  var out = []; if (!f) return out;
  ['eyebrow', 'h1', 'heading', 'sub', 'body', 'button'].forEach(function (k) { if (f[k]) out.push(f[k]); });
  (f.bullets || []).forEach(function (x) { out.push(x); }); (f.rows || []).forEach(function (x) { out.push(x); });
  (f.items || []).forEach(function (q) { out.push(q[0], q[1]); });
  return out;
}
function syl(w) {
  w = w.toLowerCase().replace(/[^a-z]/g, ''); if (!w) return 0; if (w.length <= 3) return 1;
  w = w.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '').replace(/^y/, '');
  var m = w.match(/[aeiouy]{1,2}/g); return Math.max(1, m ? m.length : 0);
}
function grade(t) {
  var ws = t.match(/[A-Za-z][A-Za-z'-]*/g) || []; if (ws.length < 6) return null;
  var sn = Math.max(1, (t.trim().match(/[.!?]+(?:\s|$)/g) || []).length), sy = 0;
  ws.forEach(function (w) { sy += syl(w); });
  return Math.max(0, Math.round((0.39 * (ws.length / sn) + 11.8 * (sy / ws.length) - 15.59) * 10) / 10);
}
function measure(kind, f) {
  var lines = flat(f), text = lines.join(' '), words = (text.match(/[\w$'+-]+/g) || []).length, limit = LIMIT[kind] || 80;
  var r = words / limit, length = r <= 0.8 ? 10 : Math.max(0, 10 - (r - 0.8) * 12.5);
  var body = lines.filter(function (x) { return [f.heading, f.h1, f.eyebrow, f.button].indexOf(x) < 0; });
  var parts = body.map(function (x) { return (x || '').trim(); }).filter(function (x) { return x.split(/\s+/).length >= 6; })
    .map(function (x) { return /[.!?…]$/.test(x) ? x : x + '.'; });
  var g = grade(parts.join(' ')), reading = g == null || g <= 7 ? 10 : Math.max(0, 10 - (g - 7) * 1.5);
  var rows = body.filter(function (x) { var n = (x || '').split(/\s+/).length; return n >= 3 && n <= 60 && '"“‘\''.indexOf(x.trim()[0]) < 0; });
  var ben = 0, out = 0; rows.forEach(function (x) { if (OUTCOME.test(x)) out++; else if (BENEFIT.test(x)) ben++; });
  var benefits = rows.length ? Math.min(10, 10 * (0.6 * ben + out) / rows.length) : 10;
  var mix = !rows.length ? '-' : (rows.length - ben - out) / rows.length >= 0.6 ? 'mostly features' : out === 0 ? 'benefits, no outcomes' : 'reaches the outcome';
  var low = text.toLowerCase(), ab = [], vg = VAGUE.filter(function (p) { return low.indexOf(p) >= 0; });
  (low.match(/[a-z][a-z-]*/g) || []).forEach(function (w) { if (ABSTRACT[w] && ab.indexOf(w) < 0) ab.push(w); });
  var conc = body.length ? body.filter(solid).length / body.length : 1;
  var clarity = Math.max(0, 10 - 2 * ab.length - 1.5 * vg.length) * (0.6 + 0.4 * conc);
  var sc = { reading: +reading.toFixed(1), length: +length.toFixed(1), benefits: +benefits.toFixed(1), clarity: +clarity.toFixed(1), stays: null, buyers: [],
    raw: { grade: g, words: words, limit: limit, mix: mix, vague: ab.concat(vg) } };
  sc.overall = +((sc.reading + sc.length + sc.benefits + sc.clarity) / 4).toFixed(1);
  return sc;
}

/* ---- the stats strip: the owner picks up to four ---- */
var STAT_MAX = 4;
function chosenStats() {
  if (!S.stats) S.stats = D.stats.filter(function (x) { return !x.needs; }).slice(0, STAT_MAX).map(function (x) { return x.id; });
  return S.stats.map(function (id) { return D.stats.filter(function (x) { return x.id === id; })[0]; }).filter(Boolean);
}
function drawStats(page) {
  var box = page.querySelector('[data-stats]'); if (!box) return;
  box.innerHTML = chosenStats().map(function (x) {
    return '<div><div class="cs-num cs-num-xl">' + br(x.value) + '</div><p class="cs-muted">' + br(x.label) + '</p></div>';
  }).join('');
}
function statsPanel() {
  var ids = chosenStats().map(function (x) { return x.id; });
  return '<div class="grp">The numbers · pick up to ' + STAT_MAX + '</div>' + D.stats.map(function (x) {
    var on = ids.indexOf(x.id) >= 0;
    return '<label class="statpick' + (on ? ' on' : '') + '"><input type="checkbox" data-stat="' + esc(x.id) + '"' + (on ? ' checked' : '') + '>' +
      '<span><b>' + br(x.value) + '</b> ' + br(x.label) + (x.needs ? '<span class="needs">Needs: ' + esc(x.needs) + '</span>' : '') + '</span></label>';
  }).join('');
}

/* ---- the page ---- */
function fill(el, f) {
  el.querySelectorAll('[data-f]').forEach(function (n) {
    var k = n.getAttribute('data-f'), v = f ? f[k] : null;
    if (k === 'bullets') n.innerHTML = (v || []).map(function (x) { return '<li><span>' + br(x) + '</span></li>'; }).join('');
    else if (k === 'rows') n.innerHTML = (v || []).map(function (x, i) {
      var m = String(x).split(/:\s*/), name = m.length > 1 ? m.shift() : '';
      return '<div class="cs-row"><div class="cs-row-name"><b>' + ('0' + (i + 1)).slice(-2) + '</b>' + br(name) + '</div><div class="cs-row-body">' + br(m.join(': ')) + '</div></div>';
    }).join('');
    else if (k === 'items') n.innerHTML = (v || []).map(function (q) { return '<details open><summary>' + br(q[0]) + '</summary><p>' + br(q[1]) + '</p></details>'; }).join('');
    else n.innerHTML = v ? br(v) : '';
  });
}
/* A headline spans three lines at most (Jono, 28 September 2026). The copy is held to it by the sell filter;
   this steps the size down for anything typed in "write your own" that still runs over. */
function fitHeadlines(page) {
  page.querySelectorAll('h1.cs-hero, h2.cs-title').forEach(function (h) {
    h.style.fontSize = '';
    var size = parseFloat(getComputedStyle(h).fontSize), min = h.tagName === 'H1' ? 36 : 24;
    for (var i = 0; i < 30; i++) {
      var lh = parseFloat(getComputedStyle(h).lineHeight) || size * 1.05;
      if (Math.round(h.offsetHeight / lh) <= 3 || size <= min) break;
      size -= 2; h.style.fontSize = size + 'px';
    }
  });
}
function drawPage() {
  document.querySelectorAll('.page').forEach(function (p) { p.hidden = p.getAttribute('data-page') !== S.page; });
  var page = document.querySelector('.page[data-page="' + S.page + '"]');
  document.getElementById('stage').classList.toggle('locked', S.locked);
  drawStats(page);
  secs().forEach(function (s) {
    var el = page.querySelector('.sec[data-n="' + s.n + '"]'); if (!el) return;
    if (s.key && !s.special) fill(el, current(s));
    var sc = currentScores(s), n = el.querySelector('.n');
    n.className = 'n ' + (sc ? tone(sc.overall) : '');
    el.classList.toggle('live', S.locked && S.sel === s.key && !!s.key);
  });
  scale();
}

/* ---- scale the page to the pane: a real 1280px computer layout, or a 390px phone ---- */
function scale() {
  var pane = document.querySelector('.pane'), w = pane.clientWidth - 88, phone = S.view === 'phone';
  document.getElementById('stage').classList.toggle('phone', phone);
  document.querySelectorAll('.page:not([hidden]) .frame').forEach(function (fr) {
    var sc = fr.querySelector('.scaler'), base = phone ? 390 : 1280, k = Math.min(1, w / base);
    sc.style.width = base + 'px'; sc.style.transform = 'scale(' + k + ')';
    fitHeadlines(sc);
    fr.style.width = (base * k) + 'px'; fr.style.height = (sc.offsetHeight * k) + 'px';
  });
}
window.addEventListener('resize', scale);
if (window.ResizeObserver) { var ro = new ResizeObserver(function () { scale(); }); document.querySelectorAll('.scaler').forEach(function (s) { ro.observe(s); }); }

/* ---- the whole page, read at once: every talking point once, a second time only at the close ---- */
var STOP = {}; 'the a an and or to of you your we our it in for is that on with at be are this by from if not no so'.split(' ').forEach(function (w) { STOP[w] = 1; });
function conflicts() {
  var rows = secs().filter(function (s) { return s.key && !s.special; }).map(function (s) { return { s: s, t: flat(current(s)).join(' ') }; });
  rows.push({ s: { type: 'stats', n: 0, ids: [] }, t: chosenStats().map(function (x) { return x.value + ' ' + x.label; }).join(' ') });
  (D.static || []).forEach(function (x) { rows.push({ s: { type: x.type, n: 0, ids: [] }, t: x.text }); });
  var out = [];
  D.repeats.forEach(function (r) {
    var re = new RegExp(r.match, 'gi'), where = [];
    rows.forEach(function (x) { var m = x.t.match(re); if (m) m.forEach(function () { where.push(x.s); }); });
    var n = where.length, atClose = where.some(function (s) { return s.type === 'close'; });
    if (n > r.cap || (n === 2 && r.cap === 2 && !atClose)) out.push({ rule: r, where: where, extra: n - (atClose ? 2 : 1), text: esc(r.label) + ' · said ' + n + ' times: ' + where.map(function (s) { return esc(label(s.type)); }).join(', ') });
  });
  var grams = {};
  rows.forEach(function (x, i) {
    var ws = (x.t.toLowerCase().match(/[a-z0-9$']+/g) || []);
    for (var j = 0; j + 3 < ws.length; j++) {
      var g = ws.slice(j, j + 4); if (g.every(function (w) { return STOP[w]; })) continue;
      g = g.join(' '); grams[g] = grams[g] || {}; grams[g][i] = x.s;
    }
  });
  Object.keys(grams).forEach(function (g) {
    var w = Object.keys(grams[g]).map(function (i) { return grams[g][i]; });
    if (w.length >= 3) out.push({ rule: null, where: w, extra: w.length - 2, text: '"' + esc(g) + '" · in ' + w.length + ' sections' });
  });
  return out;
}
function repeats() { return conflicts().map(function (c) { return c.text; }); }
function excess() { return conflicts().reduce(function (a, c) { return a + c.extra; }, 0); }
/* The default picks: the best-scored option in every section, then any section that repeats a point it does not own
   moves to its best option that does not - so the page starts with every point said once. */
function defaults() {
  secs().forEach(function (s) { if (s.key && !s.special && S.picks[s.key] == null) S.picks[s.key] = -1; });
  var fresh = secs().filter(function (s) { return s.key && !s.special && S.picks[s.key] === -1; });
  fresh.forEach(function (s) { var b = best(s.key); S.picks[s.key] = b == null ? -2 : b; });
  for (var round = 0; round < 6; round++) {
    var cs = conflicts(); if (!cs.length) break;
    var moved = false;
    cs.forEach(function (c) {
      c.where.forEach(function (s) {
        if (!s.key || fresh.indexOf(s) < 0 || s.type === 'close' || (c.rule && s.ids.indexOf(c.rule.id) >= 0)) return;
        var before = excess(), o = opts(s.key), was = S.picks[s.key];
        var order = rank(o);
        for (var k = 0; k < order.length; k++) { S.picks[s.key] = order[k]; if (excess() < before) { moved = true; return; } }
        S.picks[s.key] = was;
      });
    });
    if (!moved) break;
  }
  secs().forEach(function (s) { if (S.picks[s.key] === -2) delete S.picks[s.key]; });
}
/* ---- the sidebar ---- */
function bars(sc) {
  if (!sc) return '';
  var r = sc.raw || {};
  var rows = [['Stays', sc.stays, sc.stays == null ? 'no buyer read yet' : 'will they keep reading, every buyer counted the same'],
    ['Reading', sc.reading, r.grade == null ? 'too short to grade' : 'grade ' + r.grade],
    ['Length', sc.length, r.words + ' of ' + r.limit + ' words'],
    ['Benefits', sc.benefits, r.mix], ['Clarity', sc.clarity, (r.vague || []).length ? 'vague: ' + r.vague.join(', ') : 'nothing vague']];
  return '<div class="bars">' + rows.map(function (x) {
    var v = x[1];
    return '<div class="bar"><span>' + x[0] + '</span><span class="tr"><i style="width:' + (v == null ? 0 : v * 10) + '%;background:' + (v == null ? 'transparent' : colour(v)) + '"></i></span>' +
      '<span class="v">' + (v == null ? '-' : v.toFixed(1)) + '</span><span class="raw">' + esc(x[2]) + '</span></div>';
  }).join('') + '</div>' + (sc.buyers && sc.buyers.length ? '<div class="who">' + sc.buyers.map(function (b) {
    return '<span class="' + (b.risk <= 3 ? 'ok' : b.risk <= 6 ? 'mid' : 'bad') + '">' + esc(b.name) + ' ' + (b.risk <= 3 ? 'stays' : b.risk <= 6 ? 'wavers' : 'leaves') + '</span>';
  }).join('') + '</div>' + (D.approved ? '' : '<div class="draftnote">Buyers not approved yet: their reads are a draft.</div>') : '');
}
function pageScore() {
  var v = secs().map(currentScores).filter(Boolean).map(function (s) { return s.overall; });
  return v.length ? (v.reduce(function (a, b) { return a + b; }, 0) / v.length) : null;
}
var STATE = { here: ['ok', 'In place'], slot: ['weak', 'Placeholder'], sample: ['weak', 'Sample'], page: ['unchecked', 'Every page'], not: ['na', 'Not needed'], missing: ['missing', 'Missing'] };
function unlockedSide() {
  var P = D.pages[S.page];
  var h = '<div class="sum"><div class="rot"><button data-act="prev" aria-label="Previous page type">‹</button><span class="of">Page type <b>' + S.page + '</b> of ' + PAGES.length +
    '</span><button data-act="next" aria-label="Next page type">›</button></div><div class="bigidea">' + esc(P.big_idea) + '</div>' +
    '<div class="chips"><span class="chip add">' + esc(P.motivation) + '</span></div><button class="btn-lock" data-act="lock">Lock in page ' + S.page + '</button></div>';
  h += '<div class="grp">What is different on this page</div><div class="mapl"><ul>' + P.diff.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
  h += promises(P);
  var GROUPS = [['here', 'In place'], ['slot', 'Placeholder'], ['sample', 'Sample'], ['page', 'Every page'], ['missing', 'Missing'], ['not', 'Not needed']];
  h += '<div class="grp">All 24</div>' + GROUPS.map(function (g) {
    var cs = P.components.filter(function (c) { return c.state === g[0]; });
    if (!cs.length) return '';
    var st = STATE[g[0]];
    return '<div class="glance"><div class="gl"><div class="gi"><span class="st ' + st[0] + '">' + g[1] + '</span> <span class="wh">' + cs.length + '</span></div>' +
      cs.map(function (c) { return '<div class="gi"><b>' + c.n + '</b> ' + esc(c.name) + (c.why ? '<div class="gn">' + esc(c.why) + '</div>' : '') + '</div>'; }).join('') + '</div></div>';
  }).join('');
  return h;
}
/* Promises this page type makes that are not in the proof file yet. The owner answers each one. */
function promises(P) {
  if (!P.needs.length) return '';
  S.promises = S.promises || {};
  return '<div class="grp">Can you promise these?</div>' + P.needs.map(function (x) {
    var a = S.promises[x];
    return '<div class="prom"><div class="t">' + br(x) + '</div><div class="yn"><button data-prom="yes" data-p="' + esc(x) + '"' + (a === 'yes' ? ' class="on"' : '') +
      '>Yes</button><button data-prom="no" data-p="' + esc(x) + '"' + (a === 'no' ? ' class="on no"' : '') + '>Not yet</button></div></div>';
  }).join('');
}
/* The whole option, as it would read on the page: the line above, the headline, the words under it, every bullet. */
function preview(x) {
  var f = x.fields, out = '';
  if (f.eyebrow) out += '<div class="l0">' + br(f.eyebrow) + '</div>';
  out += '<div class="l1">' + (x.ideal ? '<span class="ideal">Ideal</span>' : '') + br(f.h1 || f.heading || '') + '</div>';
  ['sub', 'body'].forEach(function (k) { if (f[k]) out += '<div class="lb">' + br(f[k]) + '</div>'; });
  var list = (f.bullets || []).concat(f.rows || []);
  if (list.length) out += '<ul class="lu">' + list.map(function (b) { return '<li>' + br(b) + '</li>'; }).join('') + '</ul>';
  if (f.items) out += '<ul class="lu">' + f.items.map(function (q) { return '<li><b>' + br(q[0]) + '</b> ' + br(q[1]) + '</li>'; }).join('') + '</ul>';
  if (f.button) out += '<div class="lb">Button: ' + br(f.button) + '</div>';
  if (x.ideal) out += '<div class="needs">Needs: ' + esc(x.needs || 'proof on file') + '</div>';
  return out;
}
function ownForm(s) {
  var f = current(s) || {}, keys = Object.keys(s.generic || {}).concat(Object.keys(f)).filter(function (k, i, a) { return a.indexOf(k) === i; });
  return '<div class="grp">Write your own</div><div class="own">' + keys.map(function (k) {
    var v = f[k], t = Array.isArray(v) ? v.map(function (x) { return Array.isArray(x) ? x.join(' | ') : x; }).join('\n') : (v || '');
    return '<label>' + esc(k) + (Array.isArray(v) ? ' · one per line' + (k === 'items' ? ', question | answer' : '') : '') + '</label><textarea data-own="' + esc(k) + '">' + esc(t) + '</textarea>';
  }).join('') + '<button data-act="own">Use mine</button><div id="ownsc"></div></div>';
}
function lockedSide() {
  var P = D.pages[S.page], ps = pageScore(), rep = repeats();
  var ideal = secs().filter(function (s) { var c = S.picks[s.key]; return typeof c === 'number' && opts(s.key)[c] && opts(s.key)[c].ideal; }).length;
  var h = '<div class="sum"><div class="rot"><span class="of">Page <b>' + S.page + '</b> locked</span><button class="unlock" data-act="unlock">Unlock</button></div>' +
    '<div class="bigidea">' + esc(P.big_idea) + '</div>' +
    (ps != null ? '<div class="big" style="margin-top:14px"><span class="n display">' + ps.toFixed(1) + '</span><span class="k">out of 10, the average of every section</span></div>' : '') +
    '<div class="chips"><span class="chip ' + (rep.length ? 'cut' : 'keep') + '">' + (rep.length ? rep.length + ' repeated' : 'Nothing repeated') + '</span>' +
    (ideal ? '<span class="chip add">' + ideal + (ideal > 1 ? ' ideal lines need' : ' ideal line needs') + ' proof</span>' : '') +
    '<span class="chip ' + (S.verified ? 'keep' : 'fix') + '">' + (S.verified ? 'Form verified' : 'Form not verified') + '</span></div></div>';
  h += promises(P);
  if (rep.length) h += '<div class="grp">Said more than once</div><div class="rep"><ul>' + rep.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul></div>';
  var s = secs().filter(function (x) { return x.key && x.key === S.sel; })[0];
  if (s && s.special === 'stats') { h += statsPanel(); s = null; }
  if (s) {
    var o = opts(s.key), c = S.picks[s.key], cur = typeof c === 'number' ? o[c] : null;
    h += '<div class="grp">' + s.n + ' · ' + esc(label(s.type)) + '</div><div class="cur"><div class="draftnote">Carries: ' + s.says.map(esc).join(' · ') + '</div>';
    h += '<div class="rot" style="margin-top:12px"><button data-act="oprev" aria-label="Previous option">‹</button><span class="of">' +
      (c === 'own' ? '<b>Your own</b>' : cur ? 'Number <b>' + (ranked(s.key).indexOf(c) + 1) + '</b> of ' + o.length : 'Generic') + '</span><button data-act="onext" aria-label="Next option">›</button></div>';
    if (cur) h += '<div class="ang">' + (cur.ideal ? '<span class="ideal">Ideal</span>' : '') + esc(cur.angle) + '</div>' + (cur.ideal ? '<div class="needs">Needs: ' + esc(cur.needs || 'proof on file') + '</div>' : '') + bars(cur.scores);
    else if (c === 'own') h += bars(measure(s.kind, S.own[s.key]));
    h += '</div>';
    if (o.length) {
      var r = ranked(s.key), open = (S.more || {})[s.key], row = function (i, pos) {
        var x = o[i];
        return '<div class="opt' + (c === i ? ' on' : '') + '" data-opt="' + i + '"><span class="num ' + tone(x.scores.overall) + '">' + (pos + 1) + '</span><div>' +
          preview(x) + '<div class="l2">' + esc(x.angle) + '</div></div><span class="sc">' + x.scores.overall.toFixed(1) + '</span></div>';
      };
      h += '<div class="grp">The top ' + Math.min(TOP, r.length) + '</div>' + r.slice(0, TOP).map(row).join('');
      if (r.length > TOP) {
        h += '<button class="more" data-act="more">' + (open ? 'Hide the other ' : 'Show ' ) + (r.length - TOP) + (open ? '' : ' more') + '</button>';
        if (open) h += r.slice(TOP).map(function (i, k) { return row(i, k + TOP); }).join('');
      }
    }
    h += ownForm(s);
  }
  h += '<div class="grp">Every section</div>' + secs().filter(function (x) { return x.key; }).map(function (x) {
    if (x.special === 'stats') return '<div class="secl" data-sel="' + esc(x.key) + '"><span class="num">' + x.n + '</span><span>' + esc(label(x.type)) +
      ' <span class="wh" style="color:var(--muted)">' + chosenStats().length + ' picked</span></span><span class="sc"></span></div>';
    var sc = currentScores(x), c = S.picks[x.key];
    return '<div class="secl" data-sel="' + esc(x.key) + '"><span class="num ' + tone(sc && sc.overall) + '">' + x.n + '</span><span>' + esc(label(x.type)) +
      ' <span class="wh" style="color:var(--muted)">' + (c === 'own' ? 'your own' : typeof c === 'number' ? 'number ' + (ranked(x.key).indexOf(c) + 1) : 'generic') + '</span></span><span class="sc">' + (sc ? sc.overall.toFixed(1) : '-') + '</span></div>';
  }).join('');
  h += '<div class="grp">The form and the thank-you page</div><div class="verify"><label><input type="checkbox" data-act="verify"' + (S.verified ? ' checked' : '') +
    '><span>I sent a real test lead through this form, and it worked</span></label><ol><li>It arrived where your leads go.</li><li>You landed on the thank-you page, with your first name on it.</li>' +
    '<li>The conversion fired once.</li></ol></div>';
  return h;
}
function drawSide() { document.getElementById('side').innerHTML = S.locked ? lockedSide() : unlockedSide(); }
function draw() { drawPage(); drawSide(); save(); }

/* ---- actions ---- */
function rotatePage(d) { var i = PAGES.indexOf(S.page); S.page = PAGES[(i + d + PAGES.length) % PAGES.length]; S.sel = null; draw(); }
function rotateOpt(d) {
  var s = secs().filter(function (x) { return x.key === S.sel; })[0]; if (!s) return;
  var r = ranked(s.key), n = r.length; if (!n) return;
  var at = r.indexOf(S.picks[s.key]);
  S.picks[s.key] = r[at < 0 ? (d > 0 ? 0 : n - 1) : (at + d + n) % n]; draw();
}
function lock() {
  S.locked = true;
  defaults();
  var first = secs().filter(function (s) { return s.key; })[0]; S.sel = first ? first.key : null; draw();
}
function select(key, scroll) {
  S.sel = key; draw();
  var side = document.getElementById('side'), cur = side.querySelector('.cur');
  if (cur && cur.previousElementSibling) side.scrollTo({ top: cur.previousElementSibling.offsetTop - 8, behavior: 'smooth' });
  if (scroll) {
    var el = document.querySelector('.page:not([hidden]) .sec[data-key="' + key + '"]'), pane = document.querySelector('.pane');
    if (el) { var r = el.getBoundingClientRect(), p = pane.getBoundingClientRect(); pane.scrollTo({ top: pane.scrollTop + r.top - p.top - 24, behavior: 'smooth' }); }
  }
}
function useOwn() {
  var s = secs().filter(function (x) { return x.key === S.sel; })[0]; if (!s) return;
  var f = {};
  document.querySelectorAll('[data-own]').forEach(function (t) {
    var k = t.getAttribute('data-own'), v = t.value.trim(), was = (current(s) || {})[k], wasList = Array.isArray(was) || Array.isArray((s.generic || {})[k]);
    if (!v) return;
    f[k] = wasList ? v.split('\n').map(function (x) { x = x.trim(); return k === 'items' ? x.split('|').map(function (y) { return y.trim(); }) : x; }).filter(function (x) { return x.length; }) : v;
  });
  S.own[s.key] = f; S.picks[s.key] = 'own'; draw();
}
document.getElementById('side').addEventListener('click', function (e) {
  var st = e.target.closest('[data-stat]');
  if (st) {
    var ids = chosenStats().map(function (x) { return x.id; }), id = st.getAttribute('data-stat'), at = ids.indexOf(id);
    if (at >= 0) ids.splice(at, 1); else if (ids.length < STAT_MAX) ids.push(id); else { st.checked = false; return; }
    S.stats = ids; draw(); return;
  }
  var pr = e.target.closest('[data-prom]');
  if (pr) { S.promises = S.promises || {}; S.promises[pr.getAttribute('data-p')] = pr.getAttribute('data-prom'); draw(); return; }
  var a = e.target.closest('[data-act],[data-opt],[data-sel]'); if (!a) return;
  var act = a.getAttribute('data-act');
  if (act === 'prev') rotatePage(-1); else if (act === 'next') rotatePage(1); else if (act === 'lock') lock();
  else if (act === 'unlock') { S.locked = false; S.sel = null; draw(); }
  else if (act === 'oprev') rotateOpt(-1); else if (act === 'onext') rotateOpt(1); else if (act === 'own') useOwn();
  else if (act === 'verify') { S.verified = a.checked; draw(); }
  else if (act === 'more') { S.more = S.more || {}; S.more[S.sel] = !S.more[S.sel]; draw(); }
  else if (a.hasAttribute('data-opt')) { S.picks[S.sel] = +a.getAttribute('data-opt'); draw(); }
  else if (a.hasAttribute('data-sel')) select(a.getAttribute('data-sel'), true);
});
document.getElementById('side').addEventListener('input', function (e) {
  if (!e.target.hasAttribute('data-own')) return;
  var s = secs().filter(function (x) { return x.key === S.sel; })[0], f = {};
  document.querySelectorAll('[data-own]').forEach(function (t) { f[t.getAttribute('data-own')] = t.value; });
  var box = document.getElementById('ownsc'); if (box && s) box.innerHTML = bars(measure(s.kind, f));
});
document.getElementById('stage').addEventListener('click', function (e) {
  var a = e.target.closest('a'); if (a) e.preventDefault();
  if (!S.locked) return;
  var sec = e.target.closest('.sec'); if (sec && sec.getAttribute('data-key')) select(sec.getAttribute('data-key'), false);
});
document.getElementById('stage').addEventListener('input', function (e) {
  var k = e.target.getAttribute('data-in'); if (!k) return;
  var page = e.target.closest('.page');
  page.querySelectorAll('[data-sync="' + k + '"]').forEach(function (n) { n.textContent = e.target.value || n.getAttribute('data-empty'); });
});
document.querySelectorAll('[data-sync]').forEach(function (n) { n.setAttribute('data-empty', n.textContent); });
document.querySelectorAll('.views button').forEach(function (b) {
  b.addEventListener('click', function () { S.view = b.getAttribute('data-view'); document.querySelectorAll('.views button').forEach(function (x) { x.classList.toggle('on', x === b); }); draw(); });
});
document.addEventListener('keydown', function (e) {
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowRight') { S.locked ? rotateOpt(1) : rotatePage(1); } else if (e.key === 'ArrowLeft') { S.locked ? rotateOpt(-1) : rotatePage(-1); }
});
document.getElementById('dl').addEventListener('click', function () {
  if (!S.locked) { alert('Lock in a page type first.'); return; }
  if (!S.verified && !confirm('The form is not verified yet. Send one real test lead through it first. Download anyway?')) return;
  var P = D.pages[S.page];
  var picks = { page: S.page, big_idea: P.big_idea, verified: S.verified,
    stats: chosenStats(),
    promises: P.needs.map(function (x) { return { promise: x, answer: (S.promises || {})[x] || 'unanswered' }; }), saved: new Date().toISOString(), repeats: repeats().length,
    sections: secs().map(function (s) {
      var c = S.picks[s.key], o = typeof c === 'number' ? opts(s.key)[c] : null;
      return { n: s.n, type: s.type, key: s.key, choice: c === 'own' ? 'own' : o ? 'number ' + (ranked(s.key).indexOf(c) + 1) : s.key ? 'generic' : 'fixed', angle: o ? o.angle : null,
        ideal: !!(o && o.ideal), needs: o && o.ideal ? o.needs : null, fields: current(s), scores: currentScores(s) };
    }) };
  var blob = new Blob([JSON.stringify(picks, null, 1)], { type: 'application/json' }), a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = 'picks.json'; document.body.appendChild(a); a.click(); a.remove();
});
document.querySelectorAll('.views button').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-view') === S.view); });
draw();
})();
"""
