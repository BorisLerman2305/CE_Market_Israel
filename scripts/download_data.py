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
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CHAMBER_URL = "https://www.chamber.org.il/sectors/1238/1249/14824/14902/"

# ── helpers ───────────────────────────────────────────────────────────────────

def _detect_period(raw_bytes: bytes) -> tuple[Path, str]:
    """Return (dest_path, period_label) based on file content."""
    import pandas as pd
    from src.loader import FILE1, FILE2
    raw = pd.read_excel(io.BytesIO(raw_bytes), sheet_name=0, header=None, nrows=4)
    text = raw.to_string()
    if any(y in text for y in ["2026", "2025", "2024"]):
        return FILE1, "2022–2026"
    return FILE2, "2017–2022"


async def _find_and_download(dry_run: bool) -> bool:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=True,
            locale="he-IL",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # ── intercept network requests to catch file downloads ────────────────
        downloaded_url: list[str] = []

        async def handle_response(response):
            ct = response.headers.get("content-type", "")
            url = response.url
            if any(x in ct for x in ["spreadsheet", "excel", "octet-stream"]):
                downloaded_url.append(url)
                print(f"[download_data] Intercepted file response: {url}  ({ct})")
            if url.lower().endswith((".xlsx", ".xls")):
                downloaded_url.append(url)
                print(f"[download_data] Intercepted xlsx URL: {url}")

        page.on("response", handle_response)

        print(f"[download_data] Opening {CHAMBER_URL}")
        await page.goto(CHAMBER_URL, wait_until="networkidle", timeout=45_000)

        # Extra wait for lazy-loaded content
        await page.wait_for_timeout(5_000)

        # ── screenshot for debugging (saved as artifact) ──────────────────────
        screenshot_path = ROOT / "scripts" / "debug_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[download_data] Screenshot saved to {screenshot_path}")

        # ── dump ALL links for inspection ─────────────────────────────────────
        all_links: list[dict] = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]'))
                .map(a => ({href: a.href, text: a.textContent.trim().substring(0, 80)}))
                .filter(l => l.href && !l.href.startsWith('javascript'));
        }""")
        print(f"[download_data] All links on page ({len(all_links)}):")
        for l in all_links:
            print(f"  {l['text']!r:40s}  {l['href']}")

        # ── also check page text for clues ────────────────────────────────────
        page_text = await page.evaluate("() => document.body.innerText")
        print(f"[download_data] Page text snippet: {page_text[:800]}")

        # ── search for Excel links ─────────────────────────────────────────────
        xlsx_links: list[dict] = [
            l for l in all_links
            if ".xlsx" in l["href"].lower() or ".xls" in l["href"].lower()
        ]

        # Fallback: Hebrew download keywords
        if not xlsx_links:
            xlsx_links = [
                l for l in all_links
                if any(kw in (l["text"] + l["href"]).lower()
                       for kw in ["הורד", "download", "קובץ", "excel", "xls", "file", "צמ"])
            ]

        # Fallback: use any URL caught by network interception
        if not xlsx_links and downloaded_url:
            xlsx_links = [{"href": downloaded_url[0], "text": "intercepted"}]

        print(f"[download_data] Excel/download links found: {xlsx_links}")

        if not xlsx_links:
            print("[download_data] ERROR: No download links found on page.")
            await browser.close()
            return False

        if dry_run:
            print("[download_data] Dry-run — skipping actual download.")
            await browser.close()
            return True

        # ── download the first (most recent) file ─────────────────────────────
        link = xlsx_links[0]
        print(f"[download_data] Downloading: {link['href']}")

        raw_bytes: bytes | None = None

        # Method 1: direct HTTP download
        try:
            import urllib.request
            req = urllib.request.Request(
                link["href"],
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw_bytes = resp.read()
            print(f"[download_data] Direct download OK ({len(raw_bytes):,} bytes)")
        except Exception as e:
            print(f"[download_data] Direct download failed: {e}")

        # Method 2: playwright click + download event
        if not raw_bytes:
            try:
                async with page.expect_download(timeout=60_000) as dl_info:
                    await page.click(f"a[href='{link['href']}']")
                download = await dl_info.value
                tmp = await download.path()
                raw_bytes = Path(tmp).read_bytes()
                print(f"[download_data] Click download OK ({len(raw_bytes):,} bytes)")
            except Exception as e:
                print(f"[download_data] Click download failed: {e}")

        if not raw_bytes:
            print("[download_data] ERROR: All download methods failed.")
            await browser.close()
            return False

        # ── detect period and save ─────────────────────────────────────────────
        dest, label = _detect_period(raw_bytes)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw_bytes)
        print(f"[download_data] Saved {len(raw_bytes):,} bytes → {dest}  ({label})")

        await browser.close()
        return True


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Find links but do not save anything")
    args = parser.parse_args()

    success = asyncio.run(_find_and_download(dry_run=args.dry_run))
    if not success:
        print("[download_data] FAILED — no file was saved.")
        sys.exit(1)
    print("[download_data] Done.")


if __name__ == "__main__":
    main()
