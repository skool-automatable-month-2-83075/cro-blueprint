"""Load the page at three viewports, headless, and record everything the eye and the DOM can tell.

Per viewport (mobile 390x844, tablet 820x1180, desktop 1366x768): a full-page screenshot, the fold, one
screenshot per section, and the facts - every CTA with its position, every tel: and sms: link, every form and
its fields, every video and image with real and rendered size, fonts and colours in use, sticky elements,
what overflows, text under 14px, tap targets under 44px, head scripts, nav and footer links, meta.
Plus the network: bytes per host, third-party weight, stopwatch load. Never opens a window.

    from audit.capture import capture
    data = capture(url, out_dir)          # out_dir/assets/<viewport>-full.png etc.
"""
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .common import VIEWPORTS, host_of
from .botcheck import BLOCKED, settle

FACTS_JS = r"""
() => {
  const H = window.innerHeight, W = window.innerWidth;
  const vis = e => { if (!e) return false; const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity) > 0.05; };
  const rect = e => { const r = e.getBoundingClientRect(); return { top: Math.round(r.top + window.scrollY), left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height) }; };
  const txt = e => ((e.innerText || e.value || e.getAttribute('aria-label') || '') + '').replace(/\s+/g, ' ').trim();
  const ctaRe = /call|quote|book|contact|get |request|start|check|reserve|price|talk|estimate|schedule|free|apply|buy|order|try|demo|sign ?up|download|claim/i;
  const all = [...document.querySelectorAll('a,button,input[type=submit],input[type=button]')];
  const ctas = all.filter(e => vis(e) && ctaRe.test(txt(e))).map(e => ({ text: txt(e).slice(0, 60), tag: e.tagName.toLowerCase(), href: e.getAttribute('href') || '', ...rect(e), fixed: getComputedStyle(e).position === 'fixed' || !!e.closest('[style*="position: fixed"], [style*="position:fixed"]') }));
  const tel = all.filter(e => /^tel:/i.test(e.getAttribute('href') || '')).map(e => ({ href: e.getAttribute('href'), digits: (e.getAttribute('href') || '').replace(/\D/g, ''), text: txt(e).slice(0, 40), visible: vis(e), ...rect(e) }));
  const sms = all.filter(e => /^sms:/i.test(e.getAttribute('href') || '')).map(e => ({ href: e.getAttribute('href'), text: txt(e).slice(0, 40), visible: vis(e), ...rect(e) }));
  const labelFor = f => { const l = (f.id && document.querySelector('label[for="' + CSS.escape(f.id) + '"]')) || f.closest('label'); return l ? txt(l).slice(0, 60) : ''; };
  // A form is <form>, or - on most React pages - whatever block holds the inputs.
  const formHosts = (() => {
    const real = [...document.querySelectorAll('form')];
    if (real.length) return real;
    const ins = [...document.querySelectorAll('input, textarea, select')].filter(vis);
    if (ins.length < 2) return [];
    let host = ins[0];
    while (host && host !== document.body) {
      const holds = [...host.querySelectorAll('input, textarea, select')].filter(vis).length;
      if (holds >= Math.min(3, ins.length)) break;
      host = host.parentElement;
    }
    return host && host !== document.body ? [host] : [];
  })();
  const forms = formHosts.map(f => {
    const raw = [...f.querySelectorAll('input,select,textarea')].filter(x => !['hidden', 'submit', 'button', 'image'].includes(x.type) && x.tabIndex !== -1);
    const seen = new Set();
    const fields = raw.filter(x => { if (x.type !== 'radio' && x.type !== 'checkbox') return true; if (seen.has(x.name)) return false; seen.add(x.name); return true; })
      .map(x => ({ name: x.name || '', type: x.tagName === 'INPUT' ? x.type : x.tagName.toLowerCase(), autocomplete: x.getAttribute('autocomplete') || '', label: labelFor(x), placeholder: x.placeholder || '', required: x.required, visible: vis(x), inputmode: x.getAttribute('inputMode') || x.getAttribute('inputmode') || '' }));
    const honeypot = [...f.querySelectorAll('input')].some(x => x.tabIndex === -1 || (x.getAttribute('aria-hidden') === 'true') || /fax|honey|website2|url2/i.test(x.name) && !vis(x));
    const btn = f.querySelector('button[type=submit],button:not([type]),input[type=submit]');
    return { fields, selects: fields.filter(x => x.type === 'select').length, textareas: fields.filter(x => x.type === 'textarea').length, radios: fields.filter(x => x.type === 'radio' || x.type === 'checkbox').length,
             tel: fields.some(x => x.type === 'tel'), autocomplete: fields.filter(x => x.autocomplete).length, labelled: fields.filter(x => x.label).length, required: fields.filter(x => x.required).length,
             zip: fields.some(x => /zip|postal|postcode/i.test(x.name + ' ' + x.label + ' ' + x.placeholder)), button: btn ? txt(btn).slice(0, 50) : '', action: f.getAttribute('action') || '', honeypot,
             // options inside a closed select are NOT on screen
             hiddenOptionWords: [...f.querySelectorAll('select')].reduce((n, sel) =>
               n + (sel.multiple || sel.size > 1 ? 0 : [...sel.options].map(o => o.text).join(' ').split(/\s+/).length), 0),
             urlFields: [...f.querySelectorAll('input')].filter(i => i.type === 'url' || /url|website|site|domain/i.test(i.name + ' ' + (i.placeholder || '')))
               .map(i => ({ name: i.name, type: i.type, placeholder: i.placeholder || '', value: i.value || '',
                            pattern: i.getAttribute('pattern') || '',
                            demandsProtocol: i.type === 'url' && !i.getAttribute('pattern') })),
             text: txt(f).slice(0, 2000), privacyLink: !!f.querySelector('a[href*="privacy"]') || !!(f.closest('section') || f.parentElement || f).querySelector('a[href*="privacy"]'), ...rect(f) };
  }).filter(f => f.fields.length >= 2);
  const navLinks = [...document.querySelectorAll('header a[href], nav a[href]')].filter(vis).map(a => ({ href: a.getAttribute('href'), text: txt(a).slice(0, 40) }));
  const footerLinks = [...document.querySelectorAll('footer a[href]')].filter(vis).map(a => ({ href: a.getAttribute('href'), text: txt(a).slice(0, 40) }));
  const links = [...document.querySelectorAll('a[href]')].filter(vis).map(a => { const h = a.getAttribute('href') || ''; return { href: h, abs: a.href, text: txt(a).slice(0, 60), where: (a.closest('header,nav') ? 'nav' : a.closest('footer') ? 'footer' : a.closest('form') ? 'form' : 'body'), ...rect(a) }; })
    .filter(l => l.href && !/^(#|javascript:)/i.test(l.href));
  const videos = [...document.querySelectorAll('video')].map(v => ({ kind: 'video', src: v.currentSrc || v.src || (v.querySelector('source') || {}).src || '', poster: v.poster || '', autoplay: v.autoplay, preload: v.preload, loop: v.loop, muted: v.muted, controls: v.controls, duration: isFinite(v.duration) ? Math.round(v.duration) : null, visible: vis(v), ...rect(v) }));
  const iframes = [...document.querySelectorAll('iframe')].map(f => ({ kind: 'iframe', src: f.src || '', title: f.title || '', visible: vis(f), provider: (/youtube|youtu\.be/i.test(f.src) ? 'youtube' : /vimeo/i.test(f.src) ? 'vimeo' : /wistia/i.test(f.src) ? 'wistia' : /loom/i.test(f.src) ? 'loom' : /calendly|leadconnector|msgsndr|acuity|cal\.com|hubspot.*meetings/i.test(f.src) ? 'calendar' : /google.com\/maps/i.test(f.src) ? 'map' : 'other'), ...rect(f) }));
  const images = [...document.images].filter(i => vis(i) && i.naturalWidth > 0).slice(0, 80).map(i => ({ src: i.currentSrc || i.src, alt: i.alt || '', naturalW: i.naturalWidth, naturalH: i.naturalHeight, loading: i.loading || '', fetchpriority: i.getAttribute('fetchpriority') || '', section: (i.closest('section') ? [...document.querySelectorAll('section')].indexOf(i.closest('section')) : -1), ...rect(i) }));
  // A bar fixed or sticky at the TOP. On a phone, a header that stays put plus a bottom bar is two bars
  // eating the screen - mobiloud.com's Shopify page had both (Jono, 28 Sep 2026: "make sure people only have 1").
  const fixedTop = [...document.querySelectorAll('body *')].filter(e => { const s = getComputedStyle(e); if ((s.position !== 'fixed' && s.position !== 'sticky') || !vis(e)) return false; const r = e.getBoundingClientRect(); return r.top <= 8 && r.height >= 30 && r.height < H * 0.3 && r.width > W * 0.6; })
    .map(e => ({ text: txt(e).slice(0, 60), position: getComputedStyle(e).position, ...rect(e) }))
    .filter((x, i, a) => a.findIndex(y => Math.abs(y.top - x.top) < 4 && Math.abs(y.h - x.h) < 6) === i).slice(0, 3);
  const fixedBottom = [...document.querySelectorAll('body *')].filter(e => { const s = getComputedStyle(e); if ((s.position !== 'fixed' && s.position !== 'sticky') || !vis(e)) return false; const r = e.getBoundingClientRect(); return r.bottom >= H - 8 && r.height < H * 0.35 && r.width > W * 0.6; })
    .map(e => ({ h: Math.round(e.getBoundingClientRect().height), hasTel: !!e.querySelector('a[href^="tel:"]'), hasSms: !!e.querySelector('a[href^="sms:"]'), hasFormLink: !!e.querySelector('a[href^="#"], button'), text: txt(e).slice(0, 80) }));
  const popup = [...document.querySelectorAll('[role=dialog], dialog[open], .modal, .popup, [class*=popup], [class*=modal], [id*=popup]')].some(e => { const r = e.getBoundingClientRect(); return vis(e) && r.width * r.height > 0.4 * W * H; });
  const fonts = new Set(), colors = new Set(), bgs = new Set();
  ['body', 'h1', 'h2', 'h3', 'p', 'a', 'button', 'li', 'span'].forEach(sel => [...document.querySelectorAll(sel)].slice(0, 30).forEach(e => { if (!vis(e)) return; const s = getComputedStyle(e); fonts.add((s.fontFamily.split(',')[0] || '').replace(/["']/g, '').trim()); colors.add(s.color); if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)') bgs.add(s.backgroundColor); }));
  const overflowX = document.documentElement.scrollWidth > W + 2;
  const overflowing = [...document.querySelectorAll('body *')].filter(e => { if (!vis(e)) return false; const r = e.getBoundingClientRect(); return r.right > W + 4 && r.width < W * 3; }).slice(0, 8).map(e => (e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '')));
  let smallText = 0; const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const n = walker.currentNode; if (!n.textContent.trim() || !n.parentElement || !vis(n.parentElement)) continue; if (parseFloat(getComputedStyle(n.parentElement).fontSize) < 12 && n.textContent.trim().length > 12) smallText++; }
  const tapTargets = all.filter(e => vis(e) && e.getBoundingClientRect().top < H * 2).map(e => ({ text: txt(e).slice(0, 30), w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }));
  const smallTaps = tapTargets.filter(t => t.w < 44 || t.h < 44);
  const headScripts = [...document.head.querySelectorAll('script')].map(s => ({ src: s.src || '', inline: !s.src, async: s.async, defer: s.defer, module: s.type === 'module' }));
  const sections = [...document.querySelectorAll('section')].filter(s => {
    if (!vis(s)) return false;
    const r = s.getBoundingClientRect();
    if (r.height < 40) return false;
    // a section whose only child is another section is a wrapper, not a section
    const inner = s.querySelector('section');
    if (inner && Math.abs(inner.getBoundingClientRect().height - r.height) < 24) return false;
    // a section sitting on top of one already kept is the same section
    const mine = Math.round(r.top + window.scrollY);
    return ![...document.querySelectorAll('section')].some(o => {
      if (o === s || !vis(o) || !s.contains(o)) return false;
      const orr = o.getBoundingClientRect();
      return Math.abs(Math.round(orr.top + window.scrollY) - mine) < 24 && Math.abs(orr.height - r.height) < 60;
    });
  }).map((s, i) => {
    // The heading is not always an <h*>. Elementor, Webflow and half of Wordpress ship
    // headings as a styled <p> or <div>, and a section whose heading was missed got typed
    // as "other" - a photography site's video testimonial block did exactly that (Jono, 27 Sep
    // 2026). So: the first <h*>, and failing that the topmost short line of text that is
    // set noticeably larger than the body.
    let h = s.querySelector('h1,h2,h3,h4');
    let heading = h && txt(h) ? txt(h).slice(0, 80) : '';
    if (!heading) {
      const base = parseFloat(getComputedStyle(document.body).fontSize) || 16;
      const cands = [...s.querySelectorAll('p,div,span,strong')].filter(e => {
        if (!vis(e) || e.children.length > 1) return false;
        const t = txt(e);
        if (!t || t.length < 6 || t.length > 90 || t.split(/\s+/).length > 14) return false;
        const st = getComputedStyle(e);
        return parseFloat(st.fontSize) >= base * 1.35 || parseInt(st.fontWeight, 10) >= 600;
      });
      cands.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
      if (cands.length) heading = txt(cands[0]).slice(0, 80);
    }
    return { i, heading, id: s.id || '', words: txt(s).split(/\s+/).filter(Boolean).length, ctas: s.querySelectorAll('a,button').length ? [...s.querySelectorAll('a,button')].filter(e => vis(e) && ctaRe.test(txt(e))).length : 0, ...rect(s) };
  });
  // one section per position: siblings stacked at the same top are the same block
  const bestAt = new Map();
  sections.forEach(x => {
    const k = Math.round(x.top / 24);
    const cur = bestAt.get(k);
    if (!cur || x.h > cur.h || (x.h === cur.h && x.words > cur.words)) bestAt.set(k, x);
  });
  const sectionsDeduped = [...bestAt.values()].sort((a, b) => a.top - b.top).map((x, i) => ({ ...x, i }));

  const meta = n => (document.querySelector('meta[name="' + n + '"]') || {}).content || '';
  const body = document.body.innerText || '';
  const h1 = document.querySelector('h1');
  const h2s = [...document.querySelectorAll('h2')].filter(vis).map(h => txt(h).slice(0, 80));
  const quoteEls = document.querySelectorAll('blockquote, q, [class*=testimonial], [class*=review], [class*=quote]').length;
  const quoteCards = [...document.querySelectorAll('section')].filter(s => { const h = s.querySelector('h1,h2,h3'); return h && /said|words|review|testimonial|clients say/i.test(txt(h)); })
    .reduce((n, s) => n + [...s.querySelectorAll('article, figure, div')].filter(c => vis(c) && c.querySelector('img, svg') && /\w{20,}/.test(txt(c)) && txt(c).length < 600 && !c.querySelector('article, figure')).length, 0);
  const quotes = Math.max(quoteEls, quoteCards);
  // Every block of copy, with where it sits, so the copy scorer can judge it and the markup can box it.
  const blocks = [];
  const secOf = e => { const c = e.closest('section'); return c ? [...document.querySelectorAll('section')].indexOf(c) : -1; };
  [...document.querySelectorAll('li')].filter(vis).forEach(e => { const t = txt(e);
    if (t.length > 8 && t.length < 400 && !e.querySelector('li'))
      blocks.push({ kind: 'bullet', text: t.slice(0, 300), sec: secOf(e), tag: 'li',
                    interactive: !!e.closest('a, button, [role=button], form, label'), ...rect(e) }); });
  // A stat tile: a repeated row whose text starts with a number. No icon, no bold tag -
  // just the figure and what it counts. The cheapest proof on a page, and easy to miss.
  [...document.querySelectorAll('div, li')].filter(vis).forEach(e => {
    const par = e.parentElement;
    if (!par || e.children.length > 3 || e.querySelector('input, form, a[href]')) return;
    const t = txt(e);
    if (!t || t.length < 4 || t.length > 90) return;
    if (!/^[\d$]/.test(t.trim())) return;
    if (/^\d+\s*\/\s*\d+$/.test(t.trim())) return;      // "3 / 5" is a carousel counter
    const sibs = [...par.children].filter(c => vis(c) && /^[\d$]/.test(txt(c).trim()) && txt(c).length < 90);
    if (sibs.length < 2) return;
    if (blocks.some(b => Math.abs(b.top - rect(e).top) < 6 && Math.abs(b.left - rect(e).left) < 6)) return;
    blocks.push({ kind: 'stat', text: t.slice(0, 90), sec: secOf(e), ...rect(e) });
  });

  // The FAQ, question by question with its answer.
  const faq = (() => {
    const out = [];
    const qEls = [...document.querySelectorAll('summary, dt, h2, h3, h4, h5, button, a, p, span, div, li, [role=button], [class*=question i], [class*=accordion i], [class*=faq i]')]
      .filter(e => {
        if (!vis(e) || e.children.length > 2) return false;
        const t = txt(e);
        if (!/\?\s*$/.test(t) || t.length < 10 || t.length > 180) return false;
        // the innermost element carrying the question, so one question is not counted twice
        return ![...e.querySelectorAll('*')].some(c => vis(c) && /\?\s*$/.test(txt(c)) && txt(c).length > 10);
      });
    const seen = new Set();
    qEls.forEach(e => {
      const q = txt(e);
      if (seen.has(q)) return;
      seen.add(q);
      let a = '';
      const det = e.closest('details');
      if (det) a = txt(det).replace(q, '').trim();
      // walk forward from the question until real prose appears
      if (!a) {
        let n = e.nextElementSibling;
        for (let k = 0; k < 3 && n && !a; k++) { const t = txt(n); if (t && !/\?\s*$/.test(t) && t.length > 20) a = t; n = n.nextElementSibling; }
      }
      if (!a && e.parentElement) {
        const host = e.parentElement;
        const t = txt(host).replace(q, '').trim();
        if (t.length > 20 && !/\?\s*$/.test(t)) a = t;
      }
      if (!a && e.parentElement && e.parentElement.parentElement) {
        const t = txt(e.parentElement.parentElement).replace(q, '').trim();
        if (t.length > 20 && t.length < 1200) a = t;
      }
      out.push({ q: q.slice(0, 180), a: (a || '').slice(0, 900), answered: (a || '').trim().length > 20, ...rect(e) });
    });
    return out.slice(0, 20);
  })();

  // A headline figure: a big number with a short label right under or beside it.
  [...document.querySelectorAll('div, span, p, dt, dd')].filter(vis).forEach(e => {
    if (e.children.length > 1) return;
    const t = txt(e).trim();
    if (!/^[\$\d][\d,.$kKmM+%\/a-z ]{0,18}$/.test(t) || t.length < 2) return;
    if (/^\d+\s*\/\s*\d+$/.test(t)) return;          // "3 / 5" is a carousel counter
    if (/^\d{1,2}$/.test(t)) return;                    // a bare step number
    const size = parseFloat(getComputedStyle(e).fontSize) || 0;
    if (size < 22) return;                               // a headline number, not body text
    // walk up until an ancestor's own text says what the number counts
    let host = e, label = '';
    for (let k = 0; k < 4 && host && host.parentElement; k++) {
      host = host.parentElement;
      const full = txt(host);
      if (full && full.length <= 110 && /[a-z]{3,}/i.test(full.replace(t, ''))) {
        const cand = full.replace(/\s+/g, ' ').trim();
        if (/^\d+\s*(?:of|\/)\s*\d+$/i.test(cand)) break;   // "1 of 5" is a carousel counter
        label = cand;
        break;
      }
    }
    if (!label || label.length > 110) return;
    const combined = label.slice(0, 90);
    if (blocks.some(b => b.kind === 'stat' && (b.text === combined || b.text.indexOf(t) === 0))) return;
    if (blocks.some(b => Math.abs(b.top - rect(e).top) < 6 && Math.abs(b.left - rect(e).left) < 6)) return;
    blocks.push({ kind: 'stat', text: combined, sec: secOf(e), ...rect(e) });
  });

  // A tick list: repeated rows, each with an icon and a line of text, no <li> and no bold
  // lead-in. This is how most modern pages build bullets (Jono, 26 September 2026).
  [...document.querySelectorAll('div, li, p')].filter(vis).forEach(e => {
    const par = e.parentElement;
    if (!par || e.querySelector('input, textarea, form')) return;
    const t = txt(e);
    if (!t || t.length < 14 || t.length > 320) return;
    if (!e.querySelector('svg, img[src*=check i], [class*=check i], [class*=icon i]')) return;
    const sibs = [...par.children].filter(c => vis(c) && txt(c).length > 10 && c.querySelector('svg, [class*=icon i]'));
    if (sibs.length < 2) return;                       // one row is not a list
    if (blocks.some(b => b.kind === 'bullet' && Math.abs(b.top - rect(e).top) < 6)) return;
    blocks.push({ kind: 'bullet', text: t.slice(0, 300), sec: secOf(e), tag: e.tagName.toLowerCase(),
                  interactive: !!e.closest('a, button, [role=button], form, label'), ...rect(e) });
  });

  // The same thing built without <li>: a repeated row with a bold lead-in and a line under it.
  [...document.querySelectorAll('strong, b, h3, h4')].filter(vis).forEach(e => {
    const row = e.closest('div, article, section');
    if (!row || row.querySelector('li')) return;
    const t = txt(row);
    if (!t || t.length < 12 || t.length > 320) return;
    const lead = txt(e);
    if (!lead || lead.length > 60 || lead === t) return;
    const sibs = row.parentElement ? [...row.parentElement.children].filter(c => c.querySelector('strong, b, h3, h4')) : [];
    if (sibs.length < 2) return;                      // one is a heading, three is a list
    if (blocks.some(b => b.kind === 'bullet' && Math.abs(b.top - rect(row).top) < 4)) return;
    blocks.push({ kind: 'bullet', text: t.slice(0, 300), lead: lead, sec: secOf(row), tag: row.tagName.toLowerCase(),
                  interactive: !!row.closest('a, button, [role=button], form, label'), ...rect(row) });
  });
  [...document.querySelectorAll('p')].filter(vis).forEach(e => { const t = txt(e); if (t.split(/\s+/).filter(Boolean).length >= 8) blocks.push({ kind: 'para', text: t.slice(0, 600), sec: secOf(e), ...rect(e) }); });
  [...document.querySelectorAll('h2, h3')].filter(vis).forEach(e => { const t = txt(e); if (t) blocks.push({ kind: 'heading', text: t.slice(0, 160), sec: secOf(e), ...rect(e) }); });
  // Anything still saying [like this] or PLACEHOLDER: the owner's own to-do list, left on the page.
  const PH = /\[[^\]]{2,60}\]|placeholder|lorem ipsum|coming soon|your (?:logo|photo|text) here|tbd|video to add|xxx+/i;
  const holders = [];
  const seenPH = new Set();
  [...document.querySelectorAll('body *')].filter(e => vis(e) && e.children.length === 0).forEach(e => {
    const t = txt(e); if (!t || t.length > 120 || !PH.test(t)) return;
    const r = rect(e); const k = r.top + ':' + r.left; if (seenPH.has(k)) return; seenPH.add(k);
    holders.push({ text: t.slice(0, 80), sec: secOf(e), ...r });
  });
  // images whose own alt text admits they are placeholders
  [...document.images].filter(i => vis(i) && PH.test(i.alt || '')).forEach(i => {
    const r = rect(i); const k = r.top + ':' + r.left; if (seenPH.has(k)) return; seenPH.add(k);
    holders.push({ text: (i.alt || '').slice(0, 80), kind: 'image', sec: secOf(i), ...r });
  });
  // a play button with no video behind it
  // The line above the H1. It should make them feel the problem, not announce the brand.
  const eyebrow = (() => { const h = document.querySelector('h1'); if (!h) return null;
    let e = h.previousElementSibling;
    while (e && !txt(e)) e = e.previousElementSibling;
    if (!e && h.parentElement) {
      const above = [...h.parentElement.children].filter(c => c !== h && vis(c) && txt(c) && rect(c).top < rect(h).top);
      e = above.length ? above[above.length - 1] : null;
    }
    if (!e || !vis(e) || !txt(e) || txt(e).length > 140) return null;
    return { text: txt(e), asks: /\?\s*$/.test(txt(e)), ...rect(e) }; })();

  // Initials in a circle standing in for a client photo.
  const initialsClusters = [...document.querySelectorAll('body *')].filter(e => {
    if (!vis(e) || e.querySelector('img')) return false;
    const circles = [...e.querySelectorAll('*')].filter(c => c.children.length === 0 && vis(c) && /^[A-Z]{1,3}$/.test(txt(c)));
    if (circles.length < 2) return false;
    const r = e.getBoundingClientRect();
    if (r.height > 90) return false;
    if (txt(e).replace(/[A-Z\s]/g, '').length > 40) return false;
    return ![...e.children].some(c => [...c.querySelectorAll('*')].filter(x => x.children.length === 0 && /^[A-Z]{1,3}$/.test(txt(x))).length >= circles.length);
  }).slice(0, 4).map(e => ({ count: [...e.querySelectorAll('*')].filter(c => c.children.length === 0 && /^[A-Z]{1,3}$/.test(txt(c))).length, text: txt(e).slice(0, 60), ...rect(e) }));

  // Under every CTA: is there a reassurance line (how fast you answer, free, no card)?
  const ctaReassure = [...document.querySelectorAll('a[href^="#"], a[href*="quote"], button')].filter(e => vis(e) && ctaRe.test(txt(e)))
    .map(e => { const r = e.getBoundingClientRect();
      const near = [...document.querySelectorAll('body *')].filter(x => x.children.length === 0 && vis(x) && txt(x).length > 3 && txt(x).length < 90)
        .filter(x => { const xr = x.getBoundingClientRect();
          return xr.top >= r.bottom - 4 && xr.top < r.bottom + 70 && Math.abs(xr.left - r.left) < 320; })
        .map(x => txt(x));
      return { text: txt(e).slice(0, 40), under: near.join(' · ').slice(0, 120), ...rect(e) }; });

  // A framed slot with no picture in it - the gap in a row of three.
  const emptySlots = [...document.querySelectorAll('body *')].filter(e => {
    if (!vis(e) || e.querySelector('img, video, iframe')) return false;
    const r = e.getBoundingClientRect();
    if (r.width < 150 || r.height < 120) return false;
    const st = getComputedStyle(e);
    const framed = st.borderStyle !== 'none' || st.backgroundColor !== 'rgba(0, 0, 0, 0)' || st.borderRadius !== '0px';
    if (!framed) return false;
    if (e.closest('footer, header, nav')) return false;   // chrome, not a media slot
    if (e.querySelector('a[href]')) return false;          // it holds links, so it holds something
    const t = txt(e);
    if (!t || t.length > 40) return false;
    // a real empty slot announces itself: a bracketed label, or the word placeholder
    if (!/\[[^\]]{2,40}\]|placeholder|coming soon|image|photo|video/i.test(t)) return false;
    return ![...e.querySelectorAll('*')].some(c => { const cr = c.getBoundingClientRect();
      return cr.width > r.width * 0.6 && cr.height > r.height * 0.6 && c.children.length > 0; });
  }).slice(0, 6).map(e => ({ text: txt(e).slice(0, 40), sec: secOf(e), ...rect(e) }));

  // A "load more" control: the page is showing a slice on purpose.
  const loadMore = [...document.querySelectorAll('button, a, [role=button]')].filter(e => vis(e)
    && /\b(?:load|show|see|read|view)\s+(?:more|all|\d+)|more reviews|view all\b/i.test(txt(e)) && txt(e).length < 40)
    .slice(0, 4).map(e => ({ text: txt(e).slice(0, 40), sec: secOf(e), ...rect(e) }));

  // The same picture used more than once on the page.
  const bySrc = {};
  [...document.images].filter(i => vis(i) && i.naturalWidth > 60).forEach(i => {
    const k = (i.currentSrc || i.src || '').split('?')[0];
    (bySrc[k] = bySrc[k] || []).push(rect(i)); });
  const repeatedImages = Object.entries(bySrc).filter(([, v]) => v.length > 1)
    .map(([src, boxes]) => ({ src: src.slice(-60), count: boxes.length,
                              tops: boxes.map(b => b.top), ...boxes[boxes.length - 1] }));

  // The bar at the top: how much of the first screen does it eat?
  // The footer. A cookie banner carrying "footer" in its class name is a page-wide overlay,
  // and matching it made footerBox the whole 7504px page on a B2B site - every section
  // then typed as "footer" (Jono, 27 Sep 2026). So: it has to sit in the bottom third, be a
  // band rather than a page, and the shortest qualifying candidate wins.
  const footerBox = (() => {
    const docH = document.documentElement.scrollHeight;
    const cands = [...document.querySelectorAll('footer, [class*=footer i], [id*=footer i]')]
      .filter(e => {
        const r = rect(e);
        if (!vis(e) || r.h < 40) return false;
        if (r.h > docH * 0.5) return false;          // a band, never most of the page
        if (r.top + r.h < docH * 0.6) return false;  // the footer is at the bottom
        const cls = (e.className || '').toString();
        if (/cookie|consent|gdpr|banner|overlay|modal/i.test(cls)) return false;
        return true;
      });
    if (!cands.length) return null;
    const el = cands.sort((a, b) => rect(a).h - rect(b).h)[0];
    return { text: txt(el).slice(0, 80), ...rect(el) };
  })();

  // The bar at the top. Take the first VISIBLE one sitting at the top of the page - the
  // first match in the DOM is often a hidden mobile menu (Jono, 27 September 2026).
  const topBar = (() => {
    const cands = [...document.querySelectorAll('header, nav, [class*=header i], [class*=navbar i], [role=banner]')]
      .filter(e => { const r = rect(e);
        return vis(e) && r.top < 120 && r.h > 24 && r.w > W * 0.5
          && r.h <= H * 0.25;        // a bar, not a wrapper that swallowed the page
      });
    if (!cands.length) return null;
    const el = cands.sort((a, b) => (rect(a).h - rect(b).h) || (rect(a).top - rect(b).top))[0];
    const r = rect(el);
    return { h: r.h, share: Math.round(100 * r.h / H), text: txt(el).slice(0, 80), ...r };
  })();

  // The H1 and the line under it, each on its own, so the offer and the pitch can be
  // pinned to the exact line rather than to the whole hero.
  const h1El = document.querySelector('h1');
  const h1Box = h1El && vis(h1El) ? { text: txt(h1El).slice(0, 160), ...rect(h1El) } : null;
  const subBox = (() => { if (!h1El) return null; let e = h1El.nextElementSibling;
    while (e && (!txt(e) || txt(e).length < 12)) e = e.nextElementSibling;
    return e && vis(e) && txt(e).length < 400 ? { text: txt(e).slice(0, 240), ...rect(e) } : null; })();

  const fakeVideo = [...document.querySelectorAll('body *')].filter(e => {
    if (!vis(e)) return false;
    const r = e.getBoundingClientRect();
    if (r.width < 200 || r.height < 140) return false;
    if (e.querySelector('video, iframe') || e.closest('form')) return false;
    // exactly one image, and the element is essentially that image's frame - not a whole
    // section that happens to contain a picture somewhere inside it
    const imgs = e.querySelectorAll('img');
    if (imgs.length !== 1) return false;
    const ir = imgs[0].getBoundingClientRect();
    if (ir.width * ir.height < r.width * r.height * 0.55) return false;
    // a play control drawn over it
    const play = [...e.querySelectorAll('svg, [class*=play i], [aria-label*=play i]')]
      .find(x => { const pr = x.getBoundingClientRect();
        return pr.width >= 24 && pr.width <= 140 && Math.abs((pr.left + pr.width / 2) - (ir.left + ir.width / 2)) < ir.width * 0.25; });
    if (!play) return false;
    // and it must admit it is a placeholder, so a real video thumbnail is never called fake
    if (!PH.test(imgs[0].alt || '') && !PH.test(txt(e))) return false;
    // keep the innermost frame
    return ![...e.querySelectorAll('*')].some(c => c.querySelectorAll('img').length === 1
      && c.getBoundingClientRect().width >= 200 && c.getBoundingClientRect().width < r.width);
  }).slice(0, 8).map(e => ({ text: txt(e).slice(0, 60), sec: secOf(e), ...rect(e) }));

  // Testimonial cards: the block, whether a face sits with it, and whether a name is attributed.
  const quoted = [...document.querySelectorAll('div, article, figure, li, p')].filter(e => {
    if (!vis(e) || e.children.length > 8) return false;
    const t = txt(e);
    return t.length > 60 && t.length < 900 && /^[\u201C\u2018"']/.test(t.trim())
      && ![...e.children].some(c => /^[\u201C\u2018"']/.test(txt(c).trim()) && txt(c).length > 60);
  });
  const quoteBlocks = [...new Set([...document.querySelectorAll('blockquote, [class*=testimonial], [class*=review], [class*=quote]')].concat(quoted))].filter(vis)
    .filter(e => txt(e).length > 30 && txt(e).length < 900 && !e.querySelector('blockquote'))
    .map(e => {
      // walk up to three levels: the face is often outside the quote's own box
      let img = e.querySelector('img'), where = 0, host = e;
      for (let k = 1; k <= 3 && !img && host.parentElement; k++) {
        host = host.parentElement;
        if (txt(host).length > txt(e).length * 3) break;   // too far: this is the whole section
        img = host.querySelector('img');
        where = k;
      }
      const real = !!(img && img.naturalWidth > 40 && img.naturalHeight > 40);
      return { text: txt(e).slice(0, 500), sec: secOf(e),
               hasPhoto: real, photoAt: real ? where : null,
               photoSrc: img ? (img.currentSrc || img.src) : '',
               hasInitials: !img && /\b[A-Z]{2,3}\b/.test(txt(e)), ...rect(e) }; });
  // WHERE things sit, for the band walk (Jono, 27 Sep 2026). The report is cut into bands by
  // position; each band is judged from its own screenshot and its own words, so the words
  // need coordinates. Headings include styled <p>/<div> headings, which half of Wordpress ships.
  const baseFs = parseFloat(getComputedStyle(document.body).fontSize) || 16;
  const inFixed = e => { for (let p = e, i = 0; p && p !== document.body && i < 12; p = p.parentElement, i++) {
    const pos = getComputedStyle(p).position; if (pos === 'fixed' || pos === 'sticky') return true; } return false; };
  const headingsAt = [...document.querySelectorAll('h1,h2,h3,h4,p,div,span,strong')].filter(e => {
    if (!vis(e) || inFixed(e)) return false;
    const t = txt(e); if (!t || t.length < 3 || t.length > 120) return false;
    if (/^H[1-4]$/.test(e.tagName)) return true;
    if (e.children.length > 1) return false;
    const st = getComputedStyle(e);
    return parseFloat(st.fontSize) >= baseFs * 1.5 && t.split(/\s+/).length <= 14;
  }).map(e => ({ text: txt(e).slice(0, 120), level: /^H[1-4]$/.test(e.tagName) ? +e.tagName[1] : 5,
                 size: Math.round(parseFloat(getComputedStyle(e).fontSize)), ...rect(e) }))
    .filter((x, i, arr) => arr.findIndex(y => y.text === x.text && Math.abs(y.top - x.top) < 6) === i)
    .slice(0, 250);
  // every visible line of text as the visitor reads it: leaf blocks only, so nothing is doubled
  const textAt = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,td,th,dt,dd,label,button,a,span,div,strong,em')]
    .filter(e => {
      if (!vis(e) || inFixed(e)) return false;
      const t = txt(e); if (!t || t.length < 2 || t.length > 1200) return false;
      return ![...e.children].some(c => vis(c) && txt(c) && !/^(inline|contents)$/.test(getComputedStyle(c).display));
    })
    .map(e => ({ text: txt(e).slice(0, 300), tag: e.tagName.toLowerCase(), ...rect(e) }))
    .filter((x, i, arr) => arr.findIndex(y => y.text === x.text && Math.abs(y.top - x.top) < 4) === i)
    .slice(0, 900);
  // Videos that are not iframes yet: Elementor video widgets (lazy-loaded), lightbox thumbnails
  // and plain links to a video. a photography site builds its nine client videos this way, and the
  // audit saw none of them while it only looked for iframes (Jono, 27 Sep 2026).
  const videoWidgets = (() => {
    const out = [], seen = new Set();
    const idOf = s => { const m = (s || '').match(/(?:v=|youtu\.be\/|\/shorts\/|\/embed\/)([A-Za-z0-9_-]{11})/); return m ? m[1] : ''; };
    const push = (el, url) => {
      const vid = idOf(url); const key = vid || url; if (!key || seen.has(key)) return;
      const r = rect(el); if (r.w < 60 || r.h < 40) return;
      seen.add(key);
      out.push({ provider: vid ? 'youtube' : (/vimeo/.test(url) ? 'vimeo' : 'other'), id: vid,
                 src: vid ? 'https://www.youtube.com/embed/' + vid : url, ...r });
    };
    document.querySelectorAll('[data-settings*="youtube_url"], [data-settings*="vimeo_url"]').forEach(w => {
      let st = {}; try { st = JSON.parse(w.getAttribute('data-settings')); } catch (e) {}
      push(w, st.youtube_url || st.vimeo_url || '');
    });
    document.querySelectorAll('[data-elementor-lightbox]').forEach(w => {
      let st = {}; try { st = JSON.parse(w.getAttribute('data-elementor-lightbox')); } catch (e) {}
      if (st.type === 'video') push(w, st.url || '');
    });
    document.querySelectorAll('a[href*="youtube.com/watch"], a[href*="youtu.be/"], a[href*="vimeo.com/"]').forEach(a => {
      if (a.querySelector('img') || rect(a).h >= 80) push(a, a.href);
    });
    return out.slice(0, 30);
  })();
  // Broken pictures: the ones the visitor sees as a name or an empty box. They were dropped
  // entirely before, so four reviewers on mobiloud.com showing their name where their face
  // should be went unreported (28 Sep 2026).
  const brokenImages = [...document.images].filter(i => {
    const r = i.getBoundingClientRect();
    return r.width > 10 && r.height > 10 && i.complete && i.naturalWidth === 0 && getComputedStyle(i).visibility !== 'hidden';
  }).map(i => ({ alt: (i.alt || '').slice(0, 60), src: (i.currentSrc || i.src || '').slice(0, 200), ...rect(i) })).slice(0, 40);
  // A form that follows the visitor down the page (sticky or fixed). A full-page screenshot shows
  // it once at the top and an empty column below - the code has to say it is there all the way.
  const stickyForm = (() => {
    const i = [...document.querySelectorAll('input:not([type=hidden]), select, textarea')].find(x => x.offsetParent !== null);
    if (!i) return null;
    for (let p = i, k = 0; p && k < 14; p = p.parentElement, k++) {
      const st = getComputedStyle(p);
      if (st.position === 'sticky' || st.position === 'fixed') return { position: st.position, top: st.top, ...rect(p) };
    }
    return null;
  })();
  // Fallback bands for pages that do not use <section>: the children of the one wrapper that
  // holds the page, and the children of anything taller than two screens, three levels down.
  const bandCandidates = (() => {
    const docH = document.documentElement.scrollHeight;
    let host = document.body;
    for (let d = 0; d < 8; d++) {
      const kids = [...host.children].filter(vis);
      const big = kids.filter(k => rect(k).h > docH * 0.8);
      if (big.length === 1) host = big[0]; else break;
    }
    const out = [], seen = new Set();
    const add = (el, depth) => {
      for (const k of [...el.children].filter(vis)) {
        const r = rect(k);
        if (r.h < 80 || r.w < W * 0.6 || seen.has(k)) continue;
        seen.add(k);
        const hd = k.querySelector('h1,h2,h3,h4');
        out.push({ heading: hd ? txt(hd).slice(0, 80) : '', depth, ...r });
        if (r.h > H * 2 && depth < 3) add(k, depth + 1);
      }
    };
    add(host, 0);
    return out.slice(0, 160);
  })();
  const countdown = [...document.querySelectorAll('body *')].some(e => vis(e) && /^\d{1,2}:\d{2}(:\d{2})?$/.test(txt(e)) && e.children.length === 0);
  return {
    title: document.title, metaDescription: meta('description'), robots: meta('robots'), viewportMeta: meta('viewport'), lang: document.documentElement.lang || '',
    canonical: (document.querySelector('link[rel=canonical]') || {}).href || '',
    h1: h1 ? txt(h1) : '', h1Words: h1 ? txt(h1).split(/\s+/).filter(Boolean).length : 0, h1Top: h1 ? rect(h1).top : null, h2s,
    subhead: (() => { if (!h1) return ''; let e = h1.nextElementSibling; while (e && !txt(e)) e = e.nextElementSibling; return e ? txt(e).slice(0, 240) : ''; })(),
    words: body.split(/\s+/).filter(Boolean).length, bullets: document.querySelectorAll('li').length, paras: [...document.querySelectorAll('p')].filter(vis).length,
    ctas, ctasAbove: ctas.filter(c => c.top < H).length, ctasTotal: ctas.length,
    tel, sms, telNumbers: [...new Set(tel.map(t => t.digits))], forms, navLinks, footerLinks, links, videos, iframes, images,
    quotes, fixedBottom, popup, fonts: [...fonts].filter(Boolean), colors: [...colors], backgrounds: [...bgs], overflowX, overflowing, smallText, smallTaps: smallTaps.length, tapTargets: tapTargets.length,
    headScripts, sections: sectionsDeduped, countdown, blocks, quoteBlocks, holders, fakeVideo, eyebrow, initialsClusters, h1Box, subBox, ctaReassure, repeatedImages, topBar, footerBox, emptySlots, loadMore, faq, headingsAt, textAt, bandCandidates, videoWidgets, brokenImages, stickyForm, fixedTop, scrollHeight: document.documentElement.scrollHeight, viewport: { w: W, h: H },
    chat: /intercom|drift\.com|tawk\.to|crisp\.chat|tidio|hubspot.*conversations|livechat|zendesk.*widget|manychat|podium|birdeye/i.test([...document.scripts].map(s => s.src).join(' ') + ' ' + [...document.querySelectorAll('iframe')].map(f => f.src).join(' ')),
    text: body.replace(/\s+/g, ' ').trim().slice(0, 20000),
  };
}
"""

HIDE_OVERLAYS_JS = r"""
() => {
  const W = innerWidth, H = innerHeight; let n = 0; const kinds = [];
  const bad = /cookie|consent|gdpr|ccpa|onetrust|cookiebot|termly|iubenda|osano|truste|cmp-|privacy-banner|intercom|drift-|tawk|crisp|tidio|hs-messages|livechat|zendesk|chat-widget|chatwidget/i;
  for (const e of document.querySelectorAll('body *')) {
    const st = getComputedStyle(e);
    if (st.position !== 'fixed' && st.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    const id = ((e.id || '') + ' ' + ((e.className && e.className.toString()) || '') + ' ' + (e.getAttribute('aria-label') || '')).toLowerCase();
    const text = (e.innerText || '').slice(0, 500).toLowerCase();
    const cookieText = /we use cookies|(?:stores|uses) cookies|accept (?:all )?cookies|cookie (?:policy|settings|preferences)/.test(text);
    const covers = r.width * r.height > W * H * 0.4;
    const dialog = e.getAttribute('role') === 'dialog' || /modal|popup|overlay|lightbox/.test(id);
    if (bad.test(id) || cookieText || (covers && dialog)) {
      const kind = cookieText || /cookie|consent|gdpr|ccpa|onetrust|cookiebot|termly|iubenda|osano|truste|cmp-/.test(id) ? 'cookie'
                 : /intercom|drift-|tawk|crisp|tidio|hs-messages|livechat|zendesk|chat/.test(id) ? 'chat' : 'popup';
      kinds.push(kind); e.style.setProperty('display', 'none', 'important'); n++;
    }
  }
  document.documentElement.style.setProperty('overflow', 'visible', 'important');
  document.body.style.setProperty('overflow', 'visible', 'important');
  return kinds;
}
"""

VIDEO_THUMBS_JS = r"""
() => {
  const idOf = s => { const m = (s || '').match(/(?:v=|youtu\.be\/|\/shorts\/|\/embed\/)([A-Za-z0-9_-]{11})/); return m ? m[1] : ''; };
  let n = 0;
  const paint = (el, vid) => {
    const r = el.getBoundingClientRect(); if (r.width < 60 || r.height < 40) return;
    const d = document.createElement('div');
    d.style.cssText = 'width:' + r.width + 'px;height:' + r.height + 'px;display:block;position:relative;' +
      'background:#000 url(https://i.ytimg.com/vi/' + vid + '/hqdefault.jpg) center/cover no-repeat';
    // a small play mark in the corner, so it never covers the face in the still
    d.innerHTML = '<span style="position:absolute;left:12px;bottom:12px;width:0;height:0;border-style:solid;border-width:9px 0 9px 15px;border-color:transparent transparent transparent #fff;filter:drop-shadow(0 1px 2px rgba(0,0,0,.6))"></span>';
    el.replaceWith(d); n++;
  };
  document.querySelectorAll('iframe').forEach(f => { const v = idOf(f.src || f.getAttribute('data-src') || f.getAttribute('data-lazy-load')); if (v) paint(f, v); });
  document.querySelectorAll('[data-settings*="youtube_url"]').forEach(w => {
    let st = {}; try { st = JSON.parse(w.getAttribute('data-settings')); } catch (e) {}
    const v = idOf(st.youtube_url); if (!v) return;
    const overlay = w.querySelector('.elementor-custom-embed-image-overlay');
    if (overlay) {
      // a picture the site set itself, lazy-loaded and sometimes never painted
      const url = (st.image_overlay && st.image_overlay.url) || '';
      if (url && getComputedStyle(overlay).backgroundImage === 'none' && !overlay.querySelector('img[src]')) {
        overlay.style.backgroundImage = 'url(' + url + ')'; overlay.style.backgroundSize = 'cover'; overlay.style.backgroundPosition = 'center'; n++;
      }
      return;
    }
    const box = w.querySelector('.elementor-wrapper, .elementor-video, .elementor-fit-aspect-ratio');
    if (box) paint(box, v);
  });
  return n;
}
"""


def _sizes(req):
    try:
        s = req.sizes()
        return (s.get("responseBodySize") or 0) + (s.get("responseHeadersSize") or 0)
    except Exception:
        return 0


def capture(url, out_dir, section_cap=20):
    assets = os.path.join(out_dir, "assets")
    os.makedirs(assets, exist_ok=True)
    page_host = host_of(url)
    result = {"url": url, "viewports": {}, "network": {}, "status": None}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, vp in VIEWPORTS.items():
            ctx = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]}, user_agent=vp["ua"],
                                      is_mobile=vp["mobile"], has_touch=vp["mobile"], device_scale_factor=2 if vp["mobile"] else 1)
            page = ctx.new_page()
            requests = []
            page.on("requestfinished", lambda r: requests.append(r))
            t0 = time.time()
            resp = page.goto(url, wait_until="load", timeout=60000)
            load_s = round(time.time() - t0, 2)
            status, blocked = settle(page, resp)   # a host's bot check clears itself in a few seconds
            if blocked:
                browser.close()
                sys.exit(BLOCKED.format(url=url))
            if name == "mobile":
                result["status"] = status
                if status and status >= 400:
                    browser.close()
                    sys.exit(f"{url} answered {status}. That is not a page to audit - check the URL.")
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(800)
            # let lazy sections render: scroll through once, then back to the top
            # smooth scrolling would animate every scrollTo and the fold shot would land mid-scroll
            page.add_style_tag(content="html, body { scroll-behavior: auto !important; }")
            total = page.evaluate("() => document.documentElement.scrollHeight")
            # Slow enough for lazy loaders that wait for a section to be on screen: a photography site
            # showed blank video thumbnails when this stepped a full screen every 120ms.
            page.evaluate("""() => document.querySelectorAll('img[loading="lazy"]').forEach(i => { i.loading = 'eager'; })""")
            for y in range(0, min(total, 24000), int(vp["height"] * 0.7)):
                page.evaluate(f"() => window.scrollTo(0, {y})")
                page.wait_for_timeout(260)
            try:
                page.wait_for_function("() => [...document.images].every(i => i.complete)", timeout=8000)
            except Exception:
                pass
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_function("() => window.scrollY === 0", timeout=3000)
            page.wait_for_timeout(500)
            # Open every closed FAQ so the answers can be read. A collapsed accordion hides
            # the text the audit most needs (Jono, 26 September 2026). Closed again after.
            try:
                page.evaluate("() => { document.querySelectorAll('details:not([open])').forEach(d => { d.open = true; }); }")
            except Exception:
                pass
            # One question at a time: open it, read the panel that appears, close it again.
            #
            # Why this is not a body-text diff any more (Jono, 27 Sep 2026): on Elementor the
            # clickable node is an <a class="elementor-toggle-title">, and aria-expanded lives on
            # its PARENT. Reading the attribute off the <a> returned None, "already open" was
            # false, and diffing document.body.innerText missed panels that animate in. Five of
            # eight a DJ site answers came back empty and the report said "no answer showing"
            # about answers that were plainly on the page. So: walk up to the node that actually
            # carries the toggle state, click that, then read the PANEL ELEMENT, not the body.
            faq_answers = []
            try:
                qsel = ("summary, [role=button], button, a.elementor-toggle-title, "
                        ".elementor-tab-title, [class*=accordion i] [class*=title i], "
                        "[class*=question i]")
                qs = page.locator(qsel)
                seen_q = set()
                for qi in range(min(qs.count(), 40)):
                    el = qs.nth(qi)
                    try:
                        question = (el.inner_text() or "").strip()
                        if len(question) < 8 or len(question) > 200:
                            continue
                        if not question.endswith("?"):
                            continue
                        if question in seen_q:
                            continue
                        seen_q.add(question)
                        # the node that really opens: self, or the nearest ancestor with the
                        # toggle state / an accordion-header class
                        toggle = el.element_handle()
                        toggle = page.evaluate_handle("""(e) => {
                            let p = e;
                            for (let i = 0; i < 4 && p; i++) {
                                if (p.hasAttribute('aria-expanded') || p.getAttribute('role') === 'button'
                                    || /tab-title|accordion-(?:header|title|button)|toggle-title/i.test(
                                         (p.className || '').toString())) return p;
                                p = p.parentElement;
                            }
                            return e; }""", toggle).as_element()
                        already = page.evaluate(
                            "(t) => t.getAttribute('aria-expanded') === 'true' || t.hasAttribute('open')"
                            " || /(?:^| )(?:active|open|is-open|expanded)(?: |$)/.test("
                            "     (t.className || '').toString())", toggle)
                        if not already:
                            try:
                                toggle.scroll_into_view_if_needed(timeout=2000)
                                toggle.click(timeout=3000)
                            except Exception:
                                try:
                                    page.evaluate("(t) => t.click()", toggle)
                                except Exception:
                                    pass
                            page.wait_for_timeout(450)
                        # read the PANEL: aria-controls, then the next sibling, then a
                        # descendant content node. Only text that is actually visible counts.
                        ans = page.evaluate("""(t) => {
                            const vis = (n) => {
                                if (!n) return false;
                                const r = n.getBoundingClientRect();
                                const st = getComputedStyle(n);
                                return r.height > 4 && st.visibility !== 'hidden' && st.display !== 'none'
                                       && parseFloat(st.opacity || '1') > 0.05;
                            };
                            const txt = (n) => (n && vis(n)) ? (n.innerText || '').trim() : '';
                            const id = t.getAttribute('aria-controls');
                            if (id) { const p = document.getElementById(id); const v = txt(p); if (v) return v; }
                            let sib = t.nextElementSibling;
                            for (let i = 0; i < 3 && sib; i++) { const v = txt(sib); if (v) return v; sib = sib.nextElementSibling; }
                            const host = t.closest('.elementor-toggle-item, [class*=accordion-item i], '
                                                 + '[class*=toggle-item i], details, li, div');
                            if (host) {
                                const cand = host.querySelector('.elementor-tab-content, [class*=content i], '
                                                              + '[class*=panel i], [class*=answer i], p');
                                const v = txt(cand); if (v) return v;
                            }
                            return ''; }""", toggle) or ""
                        ans = ans.strip()
                        # a panel that is really the question again, or another question, is no answer
                        if ans.lower().startswith(question.lower()[:24]):
                            ans = ans[len(question):].strip()
                        if ans.rstrip().endswith("?") and len(ans.split()) < 12:
                            ans = ""
                        if len(ans.split()) < 4:
                            ans = ""
                        try:
                            bb = toggle.bounding_box()
                        except Exception:
                            bb = None
                        box = ({"top": round(bb["y"] + page.evaluate("() => window.scrollY")),
                                "left": round(bb["x"]), "w": round(bb["width"]), "h": round(bb["height"])}
                               if bb and bb.get("width") else None)
                        faq_answers.append({"q": question[:180], "a": ans[:900], "box": box})
                        if not already:
                            try:
                                toggle.click(timeout=2000)
                                page.wait_for_timeout(120)
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception:
                pass
            # back to the top: a sticky bar measures differently when it is stuck
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_timeout(350)
            facts = page.evaluate(FACTS_JS)
            if faq_answers:
                by_q = {x["q"]: x["a"] for x in faq_answers}
                for item in facts.get("faq", []):
                    got = by_q.get(item.get("q", ""))
                    if got:
                        item["a"] = got
                        item["answered"] = len(got) > 20
                for x in faq_answers:
                    match = next((i for i in facts.get("faq", []) if i.get("q") == x["q"]), None)
                    if match is None:
                        # A question the in-page scan missed. Use the box Playwright measured
                        # when it clicked; never invent one - a fabricated 0,0 draws the pin
                        # in the corner of the page (Jono, 27 September 2026).
                        entry = {"q": x["q"], "a": x["a"], "answered": len(x["a"]) > 20}
                        entry.update(x["box"] or {"top": None, "left": None, "w": None, "h": None})
                        facts.setdefault("faq", []).append(entry)
                    elif x.get("box") and not match.get("h"):
                        match.update(x["box"])
            facts["load_s"] = load_s
            facts["status"] = status
            try:
                facts["overlays_hidden"] = page.evaluate(HIDE_OVERLAYS_JS)
                facts["video_thumbs"] = page.evaluate(VIDEO_THUMBS_JS)
                page.wait_for_timeout(1500 if facts["video_thumbs"] else 200)
            except Exception:
                facts["overlays_hidden"] = 0
            fold = os.path.join(assets, f"{name}-fold.png"); full = os.path.join(assets, f"{name}-full.png")
            page.screenshot(path=fold, full_page=False)
            page.screenshot(path=full, full_page=True)
            shots = {"fold": fold, "full": full, "sections": []}
            secs = page.locator("section")
            n = secs.count()
            if n == 0:
                secs = page.locator("main > *, body > div > *")
                n = secs.count()
            for i in range(min(n, section_cap)):
                el = secs.nth(i)
                try:
                    box = el.bounding_box()
                    if not box or box["height"] < 120:
                        continue
                    p = os.path.join(assets, f"{name}-section-{i:02d}.png")
                    el.screenshot(path=p, timeout=15000)
                    shots["sections"].append({"i": i, "path": p, "h": round(box["height"])})
                except Exception:
                    continue
            # network, from this viewport's load
            by_host, head_third = {}, 0
            for r in requests:
                h = host_of(r.url); b = _sizes(r)
                by_host[h] = by_host.get(h, 0) + b
            first_party = sum(v for h, v in by_host.items() if h == page_host or h.endswith("." + page_host) or page_host.endswith("." + h))
            google_tags = sum(v for h, v in by_host.items() if re.search(r"googletagmanager|google-analytics|googleadservices|doubleclick|gstatic|googleapis", h))
            third = sum(by_host.values()) - first_party - google_tags
            result["viewports"][name] = {"facts": facts, "shots": shots,
                                        "network": {"total_kb": sum(by_host.values()) // 1024, "first_party_kb": first_party // 1024, "google_kb": google_tags // 1024,
                                                    "third_party_kb": max(0, third) // 1024, "requests": len(requests),
                                                    "hosts": sorted(((h, v // 1024) for h, v in by_host.items()), key=lambda x: -x[1])[:12]}}
            ctx.close()
        browser.close()
    m = result["viewports"]["mobile"]["facts"]
    result["network"] = result["viewports"]["mobile"]["network"]
    result["html_text"] = m["text"]
    json.dump(result, open(os.path.join(out_dir, "capture.json"), "w"), indent=1, default=str)
    return result


if __name__ == "__main__":
    from .common import out_dir_for
    u = sys.argv[1]
    d = out_dir_for(u)
    r = capture(u, d)
    for k, v in r["viewports"].items():
        f = v["facts"]
        print(f"{k}: {f['words']} words · {f['ctasAbove']} CTAs above fold · {len(f['forms'])} forms · {len(f['tel'])} tel · {len(f['images'])} images · {len(f['videos']) + len(f['iframes'])} videos/iframes · overflowX {f['overflowX']} · load {f['load_s']}s")
    print("network:", r["network"])
