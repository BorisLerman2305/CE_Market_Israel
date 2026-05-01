"""
src/specs.py — Technical specification lookup via Claude API with persistent JSON cache.

Cache file : data/specs/cache.json
Cache TTL  : 30 days per entry
Model      : claude-haiku-4-5, max_tokens=300
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

# ── Cache setup ───────────────────────────────────────────────────────────────
_CACHE_PATH = Path(__file__).parent.parent / "data" / "specs" / "cache.json"
_TTL_SECONDS = 30 * 24 * 3600  # 30 days

# Singleton cache dict loaded once at import time
_cache: dict = {}


def _load_cache() -> None:
    global _cache
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as fh:
                _cache = json.load(fh)
        except (json.JSONDecodeError, OSError):
            _cache = {}
    else:
        _cache = {}


def _save_cache() -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(_cache, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


# Load at module import
_load_cache()

# ── Field definitions by category group ───────────────────────────────────────
_EXCAVATOR_CATS = {
    "EXCAVATORS", "MINI EXCAVATORS", "TRACK EXCAVATORS", "WHEEL EXCAVATORS",
}
_BACKHOE_CATS = {"WHEEL BACKHOE LOADERS"}
_LOADER_CATS = {"WHEEL - LOADERS", "SKID - STEER - LOADERS", "TRACK LOADERS"}
_DIESEL_FORKLIFT_CATS = {"FORKLIFT TRUCK DIESEL", "FORKLIFT TRUCK LPG"}
_ELECTRIC_FORKLIFT_CATS = {"ELECTRONIC FORKLIFT TRUCK HAND OPERATED", "REACH TRUCK"}
_TELESCOPIC_CATS = {"TELESCOPIC HANDLER"}
_LIFT_CATS = {"LIFT MATE", "SCISSOR LIFT", "BOOM LIFT"}
_ROLLER_CATS = {
    "TANDEN VIBRATORY ROLLER DRIVER SEATED",
    "SINGLE DRUM VIBRATORY ROLLER",
}
_DOZER_CATS = {"CRAWLER DOZERS", "WHEEL DOZERS"}
_GRADER_CATS = {"MOTOR GRADERS"}
_CRANE_CATS = {"MOBILE CRANES", "TOWER CRANES"}


def _fields_for_category(category_en: str) -> list[str]:
    cat = category_en.strip().upper()

    if cat in _EXCAVATOR_CATS:
        return [
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
            'נפח דלי (מ"ק)',
            'עומק חפירה מרבי (מ"מ)',
            'טווח מרבי (מ"מ)',
        ]
    if cat in _BACKHOE_CATS:
        return [
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
            'נפח דלי טוען (מ"ק)',
            'נפח דלי חופר (מ"ק)',
            'עומק חפירה מרבי (מ"מ)',
        ]
    if cat in _LOADER_CATS:
        return [
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
            'נפח דלי (מ"ק)',
            'עומס הרמה מדורג (ק"ג)',
        ]
    if cat in _DIESEL_FORKLIFT_CATS:
        return [
            'קיבולת הרמה (ק"ג)',
            'גובה הרמה מרבי (מ"מ)',
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
        ]
    if cat in _ELECTRIC_FORKLIFT_CATS:
        return [
            'קיבולת הרמה (ק"ג)',
            'גובה הרמה מרבי (מ"מ)',
            'משקל עצמי (ק"ג)',
            "מתח סוללה (V)",
        ]
    if cat in _TELESCOPIC_CATS:
        return [
            'קיבולת הרמה מרבית (ק"ג)',
            'גובה הרמה מרבי (מ"מ)',
            'טווח קדמי מרבי (מ"מ)',
            'משקל עצמי (ק"ג)',
        ]
    if cat in _LIFT_CATS:
        return [
            "גובה עבודה מרבי (מ')",
            'עומס פלטפורמה (ק"ג)',
            'משקל עצמי (ק"ג)',
            "מידות פלטפורמה",
        ]
    # Rollers — match both explicit set and any string containing "ROLLER"
    if cat in _ROLLER_CATS or "ROLLER" in cat:
        return [
            'משקל עצמי (ק"ג)',
            'רוחב גליל (מ"מ)',
            "הספק מנוע (kW)",
            "כוח צנטריפוגלי (kN)",
        ]
    if cat in _DOZER_CATS:
        return [
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
            'נפח להב (מ"ק)',
            "לחץ קרקע (kPa)",
        ]
    if cat in _GRADER_CATS:
        return [
            'משקל עצמי (ק"ג)',
            "הספק מנוע (kW)",
            'רוחב להב (מ"מ)',
        ]
    # Cranes — match both explicit set and any string containing "CRANE"
    if cat in _CRANE_CATS or "CRANE" in cat:
        return [
            "קיבולת הרמה מרבית (טון)",
            "אורך זרוע מרבי (מ')",
            'משקל עצמי (ק"ג)',
        ]

    # Default
    return [
        'משקל עצמי (ק"ג)',
        "הספק מנוע (kW)",
    ]


# ── API key resolution ────────────────────────────────────────────────────────
def _get_api_key() -> str:
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")


# ── Main public function ──────────────────────────────────────────────────────
def get_specs(category_en: str, manufacturer: str, model: str) -> dict | None:
    """
    Return a dict of technical specs for the given machine, or None.

    Results are cached in data/specs/cache.json for 30 days.
    Returns None if:
      - No API key is configured
      - The API call fails
      - All returned spec values are null
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    cache_key = f"{manufacturer}|{model}|{category_en}"
    now = time.time()

    # Check cache
    if cache_key in _cache:
        entry = _cache[cache_key]
        if now - entry.get("fetched", 0) < _TTL_SECONDS:
            specs = entry.get("specs", {})
            filtered = {k: v for k, v in specs.items() if v is not None}
            return filtered if filtered else None

    # Build prompt
    fields = _fields_for_category(category_en)
    fields_json = json.dumps({f: None for f in fields}, ensure_ascii=False)

    prompt = (
        "You are a construction equipment expert. Provide technical specifications for:\n"
        f"Category: {category_en}\n"
        f"Manufacturer: {manufacturer}\n"
        f"Model: {model}\n\n"
        "Return ONLY a JSON object with these exact Hebrew keys and their values as strings "
        "(numbers formatted with commas, units omitted since they are in the key):\n"
        f"{fields_json}\n\n"
        'Use null for unknown values. If you are not confident about a spec, use null.\n'
        'Example: {"משקל עצמי (ק\\"ג)": "12,500", "הספק מנוע (kW)": "55.4"}'
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text.strip()

        # Extract JSON — tolerate markdown code fences
        if "```" in raw_text:
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        specs: dict = json.loads(raw_text)

    except Exception:
        return None

    # Persist to cache
    _cache[cache_key] = {"specs": specs, "fetched": now}
    _save_cache()

    filtered = {k: v for k, v in specs.items() if v is not None}
    return filtered if filtered else None
