"""
Monthly auto-download of the latest CE / forklift registration Excel
from the Chamber of Commerce website.

Usage:
    python scripts/download_data.py           # download + save
    python scripts/download_data.py --dry-run # find links only, no save

Requires:
    pip install playwright pandas openpyxl
    playwright install chromium
"""

import asyncio
import io
import re
import sys
import argparse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

INDEX_URL  = "https://www.chamber.org.il/sectors/1238/1249/14824/14902/"
BASE_URL   = "https://www.chamber.org.il"
# Files always live under /media/<id>/ — match both xlsx and xls
MEDIA_RE   = re.compile(r'/media/\d+/[^"\'>\s]+\.xlsx?', re.IGNORECASE)

# ── helpers ───────────────────────────────────────────────────────────────────

def _detect_period(raw_bytes: bytes) -> tuple[Path, str]:
    import pandas as pd
    from src.loader import FILE1, FILE2
    raw = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=0, header=None, nrows=4)
    text = raw.to_string()
    if any(y in text for y in ["2026", "2025", "2024"]):
        return FILE1, "2022–2026"
    return FILE2, "2017–2022"


def _fetch_bytes(url: str) -> bytes:
    """Download a URL using a browser-like User-Agent."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": INDEX_URL,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


async def _scrape_media_links() -> list[str]:
    """
    Open the index page with Playwright (to execute JS), then search the
    rendered HTML for /media/<id>/*.xlsx links.
    Returns absolute URLs, ordered as they appear (last = most recent).
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="he-IL",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        print(f"[download_data] Loading index page …")
        await page.goto(INDEX_URL, wait_until="networkidle", timeout=45_000)

        # Dismiss accessibility widget if present
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(2_000)

        # Scroll to bottom to trigger any lazy-loaded content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(8_000)   # wait for AJAX/lazy content

        # Pull full rendered HTML
        html = await page.content()
        await browser.close()

    # Find all /media/.../צמה... or similar .xlsx links
    matches = MEDIA_RE.findall(html)
    # Deduplicate while preserving order
    seen, unique = set(), []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(BASE_URL + m)

    print(f"[download_data] Media/xlsx links found in HTML: {unique}")
    return unique


async def _find_and_download(dry_run: bool) -> bool:
    links = await _scrape_media_links()

    if not links:
        print("[download_data] ERROR: No /media/*.xlsx links found on page.")
        return False

    # Always use the LAST link (most recent month)
    url = links[-1]
    print(f"[download_data] Latest file URL: {url}")

    if dry_run:
        print("[download_data] Dry-run — skipping download.")
        return True

    raw_bytes = _fetch_bytes(url)
    print(f"[download_data] Downloaded {len(raw_bytes):,} bytes")

    dest, label = _detect_period(raw_bytes)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw_bytes)
    print(f"[download_data] Saved → {dest}  ({label})")
    return True


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    success = asyncio.run(_find_and_download(dry_run=args.dry_run))
    if not success:
        print("[download_data] FAILED — no file was saved.")
        sys.exit(1)
    print("[download_data] Done.")


if __name__ == "__main__":
    main()
