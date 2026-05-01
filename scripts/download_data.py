"""
Monthly auto-download of the latest CE / forklift registration Excel
from the Chamber of Commerce website.

Strategy: use Playwright to intercept ALL network responses coming from
the page and its sub-resources, catching /media/*.xlsx URLs regardless of
whether they appear in the rendered DOM.

Usage:
    python scripts/download_data.py           # download + save
    python scripts/download_data.py --dry-run # find URL only, no save

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

INDEX_URL = "https://www.chamber.org.il/sectors/1238/1249/14824/14902/"
BASE_URL  = "https://www.chamber.org.il"
MEDIA_RE  = re.compile(r'(?:https?://[^"\'>\s]*)?/media/\d+/[^"\'>\s]+\.xlsx?', re.IGNORECASE)

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


def _normalise(url: str) -> str:
    """Ensure the URL is absolute."""
    if url.startswith("/"):
        return BASE_URL + url
    return url


async def _find_xlsx_url() -> str | None:
    from playwright.async_api import async_playwright

    found: list[str] = []

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

        # ── intercept every network response ──────────────────────────────────
        async def on_response(response):
            url = response.url
            # 1. URL itself is an xlsx file
            if re.search(r'\.xlsx?', url, re.I):
                print(f"[download_data] Direct xlsx response: {url}")
                found.append(url)
                return
            # 2. Parse response body (JSON / HTML) for /media/*.xlsx patterns
            try:
                ct = response.headers.get("content-type", "")
                if any(t in ct for t in ("json", "html", "text", "javascript")):
                    body = await response.text()
                    matches = MEDIA_RE.findall(body)
                    for m in matches:
                        full = _normalise(m)
                        if full not in found:
                            print(f"[download_data] Found in response body ({url}): {full}")
                            found.append(full)
            except Exception:
                pass

        page.on("response", on_response)

        # ── load the index page ───────────────────────────────────────────────
        print(f"[download_data] Loading {INDEX_URL}")
        await page.goto(INDEX_URL, wait_until="networkidle", timeout=60_000)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(3_000)

        # ── scroll slowly to trigger lazy content ─────────────────────────────
        for pct in [25, 50, 75, 100]:
            await page.evaluate(
                f"window.scrollTo(0, document.body.scrollHeight * {pct/100})"
            )
            await page.wait_for_timeout(2_000)

        # ── try clicking anything that looks like a month/article link ────────
        clickable = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => a.href)
                .filter(h => h.includes('/sectors/') || h.includes('/articles/') ||
                             h.includes('/news/') || h.includes('/items/'));
        }""")
        print(f"[download_data] Sector/article links to try: {clickable[:5]}")

        for link in clickable[:5]:          # try up to 5 sub-pages
            try:
                print(f"[download_data] Visiting sub-page: {link}")
                await page.goto(link, wait_until="networkidle", timeout=30_000)
                await page.wait_for_timeout(3_000)
                if found:
                    break
            except Exception as e:
                print(f"[download_data] Sub-page error: {e}")

        await browser.close()

    print(f"[download_data] All xlsx URLs intercepted: {found}")
    return found[-1] if found else None   # last = most recent


async def _run(dry_run: bool) -> bool:
    url = await _find_xlsx_url()

    if not url:
        print("[download_data] ERROR: Could not find any xlsx URL.")
        return False

    print(f"[download_data] Using URL: {url}")

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

    success = asyncio.run(_run(dry_run=args.dry_run))
    if not success:
        print("[download_data] FAILED — no file was saved.")
        sys.exit(1)
    print("[download_data] Done.")


if __name__ == "__main__":
    main()
