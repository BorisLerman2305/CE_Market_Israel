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

        print(f"[download_data] Opening {CHAMBER_URL}")
        await page.goto(CHAMBER_URL, wait_until="networkidle", timeout=45_000)

        # ── collect all Excel links ───────────────────────────────────────────
        links: list[dict] = await page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a[href]'));
            return anchors
                .filter(a => /\\.xlsx?/i.test(a.href) || /\\.xlsx?/i.test(a.getAttribute('href')))
                .map(a => ({href: a.href, text: a.textContent.trim()}));
        }""")

        # Fallback: look for any link whose text or href suggests a download
        if not links:
            links = await page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors
                    .filter(a => {
                        const t = (a.textContent + a.href).toLowerCase();
                        return t.includes('הורד') || t.includes('download')
                            || t.includes('קובץ') || t.includes('file')
                            || t.includes('excel') || t.includes('xls');
                    })
                    .map(a => ({href: a.href, text: a.textContent.trim()}));
            }""")

        print(f"[download_data] Links found: {links}")

        if not links:
            print("[download_data] ERROR: No download links found on page.")
            await browser.close()
            return False

        if dry_run:
            print("[download_data] Dry-run — skipping actual download.")
            await browser.close()
            return True

        # ── download the first (most recent) file ────────────────────────────
        link = links[0]
        print(f"[download_data] Downloading: {link['href']}")

        try:
            # Direct URL download
            import urllib.request
            req = urllib.request.Request(
                link["href"],
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw_bytes = resp.read()
        except Exception:
            # Fallback: use playwright click-and-wait approach
            async with page.expect_download(timeout=60_000) as dl_info:
                await page.click(f"a[href='{link['href']}']")
            download = await dl_info.value
            tmp = await download.path()
            raw_bytes = Path(tmp).read_bytes()

        # ── detect period and save ────────────────────────────────────────────
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
