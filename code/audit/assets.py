"""Open every asset the page carries so the audit knows what it is actually looking at.

Images: downloaded, measured (format, weight, real size against rendered size, alt), flagged when they look like
stock or generated, and laid out on contact sheets of 12 so Claude can Read them and say what each one shows.
Videos: provider, poster, autoplay, preload, duration, and the transcript - YouTube through youtube_transcript_api
(browser "Show transcript" fallback), Loom through its Transcript tab, self-hosted MP4 is not transcribed; a key
exists, otherwise "untranscribed". Links: every href that is not tel, sms, mailto or a fragment is opened in its
own tab, screenshotted, its text kept, and classified - on an ad page every one that is not legal is a leak.
Caps: 40 images, 8 videos, 20 links. Meta and Manus are never opened (BLOCKED_DOMAINS, Jono's rule).
"""
import io
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import sync_playwright

from .common import DESKTOP_UA, host_of

IMAGE_CAP, VIDEO_CAP, LINK_CAP = 40, 16, 20
LINK_TEXT_CHARS, TRANSCRIPT_CHARS = 1500, 15000
BLOCKED_DOMAINS = ("facebook.com", "fb.com", "fb.me", "fb.watch", "instagram.com", "threads.net", "whatsapp.com", "wa.me",
                   "messenger.com", "meta.com", "meta.ai", "oculus.com", "manus.ai", "manus.im", "manusai.com")
STOCK_HOSTS = re.compile(r"unsplash|pexels|pixabay|istock|shutterstock|gettyimages|adobestock|stock\.adobe|freepik|randomuser|pravatar|placeholder|placehold|picsum|loremflickr|dummyimage|thispersondoesnotexist|generated\.photos", re.I)
# a file named for the tool that made it: a B2B site's "ChatGPT-Image-Aug-20-2026" photo was AI-made (28 Sep 2026)
STOCK_NAMES = re.compile(r"photo-\d{6,}|\bstock\b|istock|shutterstock|depositphotos|\bai[-_]?gen|midjourney|dall[-_]?e|leonardo|firefly|freepik|pexels|unsplash|"
                         r"chatgpt|gpt[-_]?image|openai|ideogram|stable[-_]?diffusion|sdxl|imagen|gemini[-_]generated|generated[-_]image|"
                         # stand-in portrait and placeholder sites: a face from these is not a client (28 Sep 2026)
                         r"randomuser\.me|pravatar|thispersondoesnotexist|uifaces|generated\.photos|placeholder|picsum|loremflickr|lorempixel", re.I)


def is_blocked(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


def _youtube_id(url):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else ""


def _youtube_transcript(video_id):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return "(no transcript: pip install youtube-transcript-api)"
    try:
        try:
            snippets = YouTubeTranscriptApi().fetch(video_id)
            parts = [getattr(x, "text", "") for x in snippets]
        except AttributeError:
            parts = [x.get("text", "") for x in YouTubeTranscriptApi.get_transcript(video_id)]
        return " ".join(t.strip() for t in parts if t.strip())[:TRANSCRIPT_CHARS]
    except Exception as e:  # noqa: BLE001
        return f"(no transcript: {' '.join(str(e).split())[:240]})"


_JS_LOOM = """() => { const els = Array.from(document.querySelectorAll('button, a, [role="tab"], span, div')).filter(e => e.children.length === 0 && /^transcript$/i.test((e.textContent || '').trim())); if (!els.length) return false; els[0].click(); return true; }"""
_JS_YT = """() => { const b = document.querySelector('button[aria-label="Show transcript"]'); if (b) { b.click(); return true; } const exp = document.querySelector('#expand, tp-yt-paper-button#expand'); if (exp) exp.click();
  const btn = Array.from(document.querySelectorAll('button, span')).find(x => /show transcript/i.test(x.textContent || '') && x.offsetWidth); if (btn) { btn.click(); return true; } return false; }"""


def _loom_transcript(tab):
    try:
        if not tab.evaluate(_JS_LOOM):
            return ""
        time.sleep(3)
        body = tab.evaluate("() => document.body.innerText") or ""
        idx = body.find("Transcript\n")
        if idx < 0:
            return ""
        chunk = body[idx:]
        m = re.search(r"More actions\n", chunk)
        chunk = chunk[m.end():] if m else chunk
        out = []
        for ln in [l for l in chunk.split("\n") if l.strip()]:
            if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", ln.strip()):
                out.append(f"[{ln.strip()}]")
            elif len(ln) > 400 or ln.strip() in ("Loom", "Comment", "Activity", "Your highlights"):
                break
            else:
                out.append(ln.strip())
        return " ".join(out)[:TRANSCRIPT_CHARS]
    except Exception:
        return ""


def _youtube_browser_transcript(tab):
    try:
        for _ in range(3):
            tab.evaluate(_JS_YT)
            time.sleep(3)
            segs = tab.evaluate("() => Array.from(document.querySelectorAll('ytd-transcript-segment-renderer')).map(s => s.innerText.replace(/\\s+/g, ' ').trim())") or []
            if segs:
                return " ".join(segs)[:TRANSCRIPT_CHARS]
    except Exception:
        pass
    return ""


def _download(url, dest, cap_mb=80):
    try:
        with requests.get(url, headers={"User-Agent": DESKTOP_UA}, stream=True, timeout=60) as r:
            if r.status_code != 200:
                return None, r.status_code
            size = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    size += len(chunk)
                    if size > cap_mb << 20:
                        return None, "too large"
                    f.write(chunk)
            return dest, r.headers.get("content-type", "")
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:60]


def images(cap, cache_dir, assets_dir):
    """Every image the mobile and desktop views showed, downloaded, measured and flagged. Contact sheets of 12."""
    seen, rows = {}, []
    for vp in ("mobile", "desktop"):
        for im in cap["viewports"][vp]["facts"]["images"]:
            src = im["src"]
            if not src or src.startswith("data:") or src in seen:
                if src in seen:
                    seen[src]["rendered"][vp] = {"w": im["w"], "h": im["h"]}
                continue
            seen[src] = {"src": src, "alt": im["alt"], "naturalW": im["naturalW"], "naturalH": im["naturalH"], "loading": im["loading"],
                         "fetchpriority": im["fetchpriority"], "section": im["section"], "top": im["top"], "rendered": {vp: {"w": im["w"], "h": im["h"]}}}
    rows = list(seen.values())[:IMAGE_CAP]
    img_dir = os.path.join(cache_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        Image = None
    for i, r in enumerate(rows):
        name = f"img-{i:02d}" + os.path.splitext(urlparse(r["src"]).path)[1][:5]
        path, ct = _download(r["src"], os.path.join(img_dir, name))
        r["file"] = path
        r["kb"] = round(os.path.getsize(path) / 1024) if path else None
        r["format"] = (ct.split("/")[-1].split(";")[0] if isinstance(ct, str) and "/" in ct else os.path.splitext(name)[1].lstrip(".")) or "?"
        rw = max((v["w"] for v in r["rendered"].values()), default=0)
        r["upscaled"] = bool(rw and r["naturalW"] and rw / max(r["naturalW"], 1) > 1.3)
        r["oversized"] = bool(rw and r["naturalW"] and r["naturalW"] / max(rw, 1) > 2.5 and (r["kb"] or 0) > 150)
        r["stock_suspect"] = bool(STOCK_HOSTS.search(r["src"]) or STOCK_NAMES.search(r["src"]) or STOCK_NAMES.search(r["alt"]))
        r["alt_missing"] = not r["alt"].strip()
        r["big"] = r["naturalW"] >= 300 and r["naturalH"] >= 200
        r["contact_sheet"] = None
    # contact sheets: 12 per sheet, 4 columns, each tile labelled with its index
    sheets = []
    if Image is not None:
        big = [r for r in rows if r.get("file") and r["big"]]
        for s in range(0, len(big), 12):
            batch = big[s:s + 12]
            tile, cols = 360, 4
            rowsn = (len(batch) + cols - 1) // cols
            sheet = Image.new("RGB", (cols * tile, rowsn * (tile + 28)), "white")
            try:
                from PIL import ImageDraw
                draw = ImageDraw.Draw(sheet)
            except Exception:
                draw = None
            for k, r in enumerate(batch):
                try:
                    im = Image.open(r["file"]).convert("RGB")
                    im.thumbnail((tile - 8, tile - 8))
                    x, y = (k % cols) * tile + 4, (k // cols) * (tile + 28) + 24
                    sheet.paste(im, (x, y))
                    if draw:
                        draw.text((x, y - 20), f"#{rows.index(r):02d} {r['naturalW']}x{r['naturalH']} {r['kb']}KB" + (" STOCK?" if r["stock_suspect"] else "") + (" UPSCALED" if r["upscaled"] else ""), fill="black")
                    r["contact_sheet"] = len(sheets)
                except Exception:
                    continue
            p = os.path.join(assets_dir, f"images-sheet-{len(sheets)}.png")
            sheet.save(p)
            sheets.append(p)
    return {"count": len(rows), "items": [{k: v for k, v in r.items() if k != "file"} | {"file": r.get("file")} for r in rows], "sheets": sheets,
            "stock_suspects": sum(1 for r in rows if r["stock_suspect"]), "upscaled": sum(1 for r in rows if r["upscaled"]),
            "alt_missing": sum(1 for r in rows if r["alt_missing"] and r["big"]), "heavy": sum(1 for r in rows if (r["kb"] or 0) > 300)}


def videos(cap, page_url, cache_dir):
    """Every <video> and provider iframe, with its transcript where one can be had."""
    facts = cap["viewports"]["desktop"]["facts"]
    items = []
    for v in facts["videos"][:VIDEO_CAP]:
        items.append({"kind": "self-hosted", "src": urljoin(page_url, v["src"]) if v["src"] else "", "poster": v["poster"], "autoplay": v["autoplay"], "preload": v["preload"],
                      "loop": v["loop"], "muted": v["muted"], "controls": v["controls"], "duration_s": v["duration"], "top": v["top"], "transcript": ""})
    for f in facts["iframes"]:
        if f["provider"] in ("youtube", "vimeo", "wistia", "loom"):
            items.append({"kind": f["provider"], "src": f["src"], "poster": "", "autoplay": "autoplay=1" in f["src"], "preload": "", "loop": False, "muted": False,
                          "controls": True, "duration_s": None, "top": f["top"], "transcript": ""})
    # Video widgets and lightbox thumbnails that are not iframes yet. Same video, same ID:
    # counted once (Jono, 27 Sep 2026 - a photography site's nine client videos were invisible).
    have = {_youtube_id(it["src"]) for it in items if it["kind"] == "youtube"}
    for w in facts.get("videoWidgets") or []:
        if w.get("provider") == "youtube" and w.get("id") and w["id"] not in have:
            have.add(w["id"])
            items.append({"kind": "youtube", "src": w["src"], "poster": "", "autoplay": False, "preload": "", "loop": False,
                          "muted": False, "controls": True, "duration_s": None, "top": w["top"], "transcript": "",
                          "widget": True})
    items = items[:VIDEO_CAP]
    if not items:
        return {"count": 0, "items": [], "third_party": 0, "autoplay": 0, "no_poster": 0}
    vid_dir = os.path.join(cache_dir, "videos")
    os.makedirs(vid_dir, exist_ok=True)
    # A transcript read once is kept, by video ID. YouTube refuses requests after a few crawls in
    # a row, and a refused fetch used to overwrite the good transcript from the run before - the
    # a photography site client videos went from read to "could not retrieve" on a re-crawl (28 Sep 2026).
    tr_cache_path = os.path.join(vid_dir, "transcripts.json")
    try:
        tr_cache = json.load(open(tr_cache_path))
    except (OSError, ValueError):
        tr_cache = {}
    for it in items:
        vid = _youtube_id(it["src"]) if it["kind"] == "youtube" else ""
        if vid and tr_cache.get(vid):
            it["transcript"] = tr_cache[vid]
            it["cached"] = True
    need_browser = [it for it in items if it["kind"] in ("youtube", "loom") and not it.get("cached")]
    if need_browser:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            ctx = b.new_context(user_agent=DESKTOP_UA, viewport={"width": 1280, "height": 800})
            for it in need_browser:
                url = it["src"]
                if it["kind"] == "youtube":
                    vid = _youtube_id(url)
                    t = _youtube_transcript(vid) if vid else ""
                    if not t or t.startswith("(no transcript"):
                        try:
                            tab = ctx.new_page(); tab.goto(f"https://www.youtube.com/watch?v={vid}", wait_until="domcontentloaded", timeout=30000); time.sleep(3)
                            t = _youtube_browser_transcript(tab) or t
                            tab.close()
                        except Exception:
                            pass
                    it["transcript"] = t
                elif it["kind"] == "loom":
                    try:
                        tab = ctx.new_page(); tab.goto(url.replace("/embed/", "/share/"), wait_until="domcontentloaded", timeout=30000); time.sleep(4)
                        it["transcript"] = _loom_transcript(tab); tab.close()
                    except Exception:
                        pass
            b.close()
    for it in items:
        vid = _youtube_id(it["src"]) if it["kind"] == "youtube" else ""
        t = (it.get("transcript") or "").strip()
        if vid and t and not t.startswith("("):
            tr_cache[vid] = t
    try:
        json.dump(tr_cache, open(tr_cache_path, "w"), indent=1)
    except OSError:
        pass
    for i, it in enumerate(items):
        if it["kind"] == "self-hosted" and it["src"]:
            path, ct = _download(it["src"], os.path.join(vid_dir, f"video-{i}.mp4"), cap_mb=120)
            it["kb"] = round(os.path.getsize(path) / 1024) if path else None
            it["transcript"] = "(untranscribed - self-hosted video)" if path else f"(could not download: {ct})"
        elif it["kind"] in ("vimeo", "wistia"):
            it["transcript"] = it["transcript"] or f"(untranscribed - {it['kind']} has no transcript route here)"
        it["transcript_words"] = len([w for w in (it["transcript"] or "").split() if not (it["transcript"] or "").startswith("(")])
    return {"count": len(items), "items": items, "third_party": sum(1 for it in items if it["kind"] != "self-hosted"),
            "autoplay": sum(1 for it in items if it["autoplay"]), "no_poster": sum(1 for it in items if it["kind"] == "self-hosted" and not it["poster"])}


def classify_link(href, abs_url, text, page_host):
    h = host_of(abs_url); t = (text or "").lower(); u = (abs_url or "").lower()
    if re.search(r"privacy|terms|conditions|legal|cookie|accessibility", u + " " + t):
        return "legal"
    if re.search(r"facebook|instagram|linkedin|youtube\.com/(@|channel|c/)|tiktok|x\.com|twitter", u):
        return "social"
    if re.search(r"google\.com/maps|g\.page|yelp\.com|trustpilot|bbb\.org|homestars|houzz|angi\.com", u):
        return "review-profile"
    if h and (h == page_host or h.endswith("." + page_host) or page_host.endswith("." + h)):
        return "internal-exit"
    return "external-exit"


def links(cap, page_url, cache_dir, assets_dir):
    """Open every link that leaves the page. Each one is a leak on an ad page; say what it actually is."""
    page_host = host_of(page_url)
    seen, rows = set(), []
    for vp in ("desktop", "mobile"):
        for l in cap["viewports"][vp]["facts"]["links"]:
            href = l["href"]
            if re.match(r"^(tel:|sms:|mailto:|#|javascript:)", href, re.I):
                continue
            a = l["abs"] or urljoin(page_url, href)
            if a.split("#")[0].rstrip("/") == page_url.split("#")[0].rstrip("/"):
                continue
            if a in seen:
                continue
            seen.add(a)
            rows.append({"href": href, "url": a, "text": l["text"], "where": l["where"], "kind": classify_link(href, a, l["text"], page_host)})
    rows = rows[:LINK_CAP]
    for i, r in enumerate(rows):
        r["blocked"] = is_blocked(r["url"])
        r["title"] = ""; r["page_text"] = ""; r["screenshot"] = ""; r["status"] = ""
    to_open = [r for r in rows if not r["blocked"]]
    if to_open:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            ctx = b.new_context(user_agent=DESKTOP_UA, viewport={"width": 1280, "height": 800})
            for i, r in enumerate(rows):
                if r["blocked"]:
                    r["status"] = "never opened (blocked domain)"
                    continue
                tab = None
                try:
                    tab = ctx.new_page()
                    resp = tab.goto(r["url"], wait_until="domcontentloaded", timeout=25000)
                    time.sleep(2)
                    r["status"] = f"http {resp.status}" if resp else "opened"
                    r["title"] = (tab.title() or "")[:120]
                    r["page_text"] = (tab.evaluate("() => document.body ? document.body.innerText : ''") or "").replace("\n", " ")[:LINK_TEXT_CHARS]
                    shot = os.path.join(assets_dir, f"link-{i:02d}.png")
                    tab.screenshot(path=shot, full_page=False)
                    r["screenshot"] = shot
                except Exception as e:  # noqa: BLE001
                    r["status"] = f"error: {str(e)[:80]}"
                finally:
                    if tab:
                        try:
                            tab.close()
                        except Exception:
                            pass
            b.close()
    leaks = [r for r in rows if r["kind"] not in ("legal",)]
    return {"count": len(rows), "items": rows, "leaks": len(leaks), "by_kind": {k: sum(1 for r in rows if r["kind"] == k) for k in ("legal", "social", "review-profile", "internal-exit", "external-exit")}}


def collect(cap, page_url, cache_dir, assets_dir):
    out = {"images": images(cap, cache_dir, assets_dir), "videos": videos(cap, page_url, cache_dir), "links": links(cap, page_url, cache_dir, assets_dir)}
    json.dump(out, open(os.path.join(cache_dir, "assets.json"), "w"), indent=1, default=str)
    return out
