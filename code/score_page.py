"""Kept for old muscle memory. The real thing is code/audit/page_audit.py - the full audit at three viewports.

    python3 code/score_page.py <url>   ==   python3 code/audit/page_audit.py <url> --no-lighthouse
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, os.path.join(HERE, "audit", "page_audit.py"), *sys.argv[1:], "--no-lighthouse"]))
