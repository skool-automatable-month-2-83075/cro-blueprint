"""Shared bits for the audit modules: paths, slugs, the repo root, small helpers."""
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(HERE)
ROOT = os.path.dirname(CODE)
sys.path.insert(0, CODE)  # so `import _business`, `psi_speed`, `check_page_quality` work

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
load_dotenv(os.path.join(ROOT, "website", ".env.local"))

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
TABLET_UA = "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DESKTOP_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"

VIEWPORTS = {
    "mobile": {"width": 390, "height": 844, "ua": MOBILE_UA, "mobile": True},
    "tablet": {"width": 820, "height": 1180, "ua": TABLET_UA, "mobile": True},
    "desktop": {"width": 1366, "height": 768, "ua": DESKTOP_UA, "mobile": False},
}


def slug_of(url):
    u = urlparse(url)
    path = re.sub(r"[^a-z0-9]+", "-", u.path.lower()).strip("-") or "home"
    host = re.sub(r"[^a-z0-9]+", "-", u.netloc.lower().split(":")[0]).strip("-")
    return f"{host}-{path}"[:80]


def out_dir_for(url, out=None):
    d = out or os.path.join(ROOT, "context", "pages", slug_of(url))
    os.makedirs(os.path.join(d, "assets"), exist_ok=True)
    return d


def cache_dir_for(url):
    d = os.path.join(CODE, "cache", "audit", slug_of(url))
    os.makedirs(d, exist_ok=True)
    return d


def host_of(url):
    return (urlparse(url).hostname or "").lower()


def is_ours(url):
    """Localhost, or the site in SITE_BASE_URL - the pages this repo builds and can test-submit against."""
    h = host_of(url)
    site = host_of(os.environ.get("SITE_BASE_URL", "") or "")
    return h in ("localhost", "127.0.0.1") or (site and (h == site or h == "www." + site or site == "www." + h))


def rel(path):
    return os.path.relpath(path, ROOT)
