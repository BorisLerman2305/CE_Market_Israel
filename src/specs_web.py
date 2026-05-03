"""
src/specs_web.py — Free spec lookup: static DB + Volvo CE web-fetch + external links.
No API key required.

Static DB covers ~60 common models. Volvo CE models are also live-fetched when
the static entry is missing, since their site serves clean HTML.
Results are cached in data/specs/cache.json for 30 days.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

# ── Cache (shared with specs.py) ──────────────────────────────────────────────
_CACHE_PATH = Path(__file__).parent.parent / "data" / "specs" / "cache.json"
_TTL = 30 * 24 * 3600

_cache: dict = {}


def _load_cache() -> None:
    global _cache
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}


def _save_cache() -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_load_cache()

# ── Manufacturer product-catalog URLs ─────────────────────────────────────────
MANUFACTURER_SITES: dict[str, str] = {
    "CATERPILLAR":  "https://www.cat.com/en_US/products/new/equipment.html",
    "CAT":          "https://www.cat.com/en_US/products/new/equipment.html",
    "KOMATSU":      "https://www.komatsu.com/en/products/",
    "VOLVO":        "https://www.volvoce.com/europe/en/products/",
    "HITACHI":      "https://www.hitachicm.eu/machines/",
    "JCB":          "https://www.jcb.com/en-gb/products",
    "LIEBHERR":     "https://www.liebherr.com/en/gbr/products/earthmoving/",
    "BOBCAT":       "https://www.bobcat.com/eu/en/equipment",
    "DOOSAN":       "https://www.doosanequipment.com/en",
    "DEVELON":      "https://www.develon-ce.com/en",
    "HYUNDAI":      "https://www.hd-ce.com/en/products.do",
    "SANY":         "https://www.sany.com/en/product",
    "XCMG":         "https://www.xcmg.com/en/product.html",
    "MANITOU":      "https://www.manitou.com/en/products",
    "MERLO":        "https://www.merlo.com/en/products/",
    "JUNGHEINRICH": "https://www.jungheinrich.com/en/products",
    "TOYOTA":       "https://www.toyota-forklifts.eu/en/products",
    "LINDE":        "https://www.linde-mh.com/en/product-solutions/",
    "STILL":        "https://www.still.co.uk/products.aspx",
    "CROWN":        "https://www.crown.com/en-us/forklifts.html",
    "HYSTER":       "https://www.hyster.com/en-eu/forklifts/",
    "YALE":         "https://www.yale.com/en-eu/forklifts/",
    "JLG":          "https://www.jlg.com/en/equipment",
    "GENIE":        "https://www.genielift.com/en/products",
    "HAULOTTE":     "https://www.haulotte.com/en/products",
    "TADANO":       "https://www.tadano.com/en/products/",
    "GROVE":        "https://www.manitowoccranes.com/en/cranes/grove",
    "KOBELCO":      "https://www.kobelco-europe.com/machines/",
    "KUBOTA":       "https://www.kubota.eu/products/construction-equipment/",
    "YANMAR":       "https://www.yanmar.com/eu/en/products/construction/",
    "DYNAPAC":      "https://www.dynapac.com/en/products/",
    "BOMAG":        "https://www.bomag.com/en/products/",
    "HAMM":         "https://www.hamm.eu/en/products/",
    "JOHN DEERE":   "https://www.deere.com/en/construction/",
    "CASE":         "https://www.casece.com/en-gb/products/",
    "NEW HOLLAND":  "https://www.newholland.com/en/construction/",
    "WIRTGEN":      "https://www.wirtgen.de/en-us/products/",
}

# ── Static specs database ─────────────────────────────────────────────────────
# Key: "MANUFACTURER_UPPER|MODEL_UPPER"
# Value: {"url": str, "specs": {Hebrew field: value}}
_S = {
    # ── Track & Mini Excavators — CAT ─────────────────────────────────────────
    "CATERPILLAR|308": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/mini-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "8,360", 'הספק מנוע (kW)': "42.5",
                  'נפח דלי (מ"ק)': "0.27", 'עומק חפירה מרבי (מ"מ)': "4,025",
                  'טווח מרבי (מ"מ)': "6,760"}},
    "CATERPILLAR|312": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/small-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "13,100", 'הספק מנוע (kW)': "55.4",
                  'נפח דלי (מ"ק)': "0.50", 'עומק חפירה מרבי (מ"מ)': "5,560",
                  'טווח מרבי (מ"מ)': "8,350"}},
    "CATERPILLAR|316": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/small-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "16,900", 'הספק מנוע (kW)': "85",
                  'נפח דלי (מ"ק)': "0.68", 'עומק חפירה מרבי (מ"מ)': "6,100",
                  'טווח מרבי (מ"מ)': "9,000"}},
    "CATERPILLAR|320": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/medium-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "22,000", 'הספק מנוע (kW)': "103",
                  'נפח דלי (מ"ק)': "0.90–1.19", 'עומק חפירה מרבי (מ"מ)': "6,740",
                  'טווח מרבי (מ"מ)': "9,930"}},
    "CATERPILLAR|323": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/medium-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "24,000", 'הספק מנוע (kW)': "122",
                  'נפח דלי (מ"ק)': "1.05–1.35", 'עומק חפירה מרבי (מ"מ)': "7,100",
                  'טווח מרבי (מ"מ)': "10,380"}},
    "CATERPILLAR|330": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/medium-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "30,000", 'הספק מנוע (kW)': "150",
                  'נפח דלי (מ"ק)': "1.35–1.73", 'עומק חפירה מרבי (מ"מ)': "7,620",
                  'טווח מרבי (מ"מ)': "11,170"}},
    "CATERPILLAR|336": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/large-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "38,300", 'הספק מנוע (kW)': "194",
                  'נפח דלי (מ"ק)': "1.63–2.5", 'עומק חפירה מרבי (מ"מ)': "8,550",
                  'טווח מרבי (מ"מ)': "12,380"}},
    "CATERPILLAR|349": {
        "url": "https://www.cat.com/en_US/products/new/equipment/excavators/large-excavators.html",
        "specs": {'משקל עצמי (ק"ג)': "51,100", 'הספק מנוע (kW)': "270",
                  'נפח דלי (מ"ק)': "2.4–3.2", 'עומק חפירה מרבי (מ"מ)': "9,290",
                  'טווח מרבי (מ"מ)': "13,200"}},
    # ── Track Excavators — Komatsu ────────────────────────────────────────────
    "KOMATSU|PC78": {
        "url": "https://www.komatsu.com/en/products/excavators/hydraulic-excavators/",
        "specs": {'משקל עצמי (ק"ג)': "8,015", 'הספק מנוע (kW)': "39",
                  'נפח דלי (מ"ק)': "0.26", 'עומק חפירה מרבי (מ"מ)': "4,110",
                  'טווח מרבי (מ"מ)': "6,870"}},
    "KOMATSU|PC138": {
        "url": "https://www.komatsu.com/en/products/excavators/hydraulic-excavators/",
        "specs": {'משקל עצמי (ק"ג)': "14,175", 'הספק מנוע (kW)': "71",
                  'נפח דלי (מ"ק)': "0.50", 'עומק חפירה מרבי (מ"מ)': "5,900",
                  'טווח מרבי (מ"מ)': "8,820"}},
    "KOMATSU|PC210": {
        "url": "https://www.komatsu.com/en/products/excavators/hydraulic-excavators/",
        "specs": {'משקל עצמי (ק"ג)': "21,300", 'הספק מנוע (kW)': "110",
                  'נפח דלי (מ"ק)': "0.90", 'עומק חפירה מרבי (מ"מ)': "6,640",
                  'טווח מרבי (מ"מ)': "9,845"}},
    "KOMATSU|PC290": {
        "url": "https://www.komatsu.com/en/products/excavators/hydraulic-excavators/",
        "specs": {'משקל עצמי (ק"ג)': "29,800", 'הספק מנוע (kW)': "160",
                  'נפח דלי (מ"ק)': "1.20", 'עומק חפירה מרבי (מ"מ)': "7,130",
                  'טווח מרבי (מ"מ)': "10,480"}},
    "KOMATSU|PC360": {
        "url": "https://www.komatsu.com/en/products/excavators/hydraulic-excavators/",
        "specs": {'משקל עצמי (ק"ג)': "36,900", 'הספק מנוע (kW)': "200",
                  'נפח דלי (מ"ק)': "1.80", 'עומק חפירה מרבי (מ"מ)': "7,820",
                  'טווח מרבי (מ"מ)': "11,415"}},
    # ── Track Excavators — Volvo ──────────────────────────────────────────────
    "VOLVO|EC140E": {
        "url": "https://www.volvoce.com/europe/en/products/excavators/ec140e/",
        "specs": {'משקל עצמי (ק"ג)': "13,900", 'הספק מנוע (kW)': "80.5",
                  'נפח דלי (מ"ק)': "0.44–0.79", 'עומק חפירה מרבי (מ"מ)': "5,945",
                  'טווח מרבי (מ"מ)': "8,800"}},
    "VOLVO|EC220E": {
        "url": "https://www.volvoce.com/europe/en/products/excavators/ec220e/",
        "specs": {'משקל עצמי (ק"ג)': "22,000", 'הספק מנוע (kW)': "129",
                  'נפח דלי (מ"ק)': "0.48–1.44", 'עומק חפירה מרבי (מ"מ)': "6,960",
                  'טווח מרבי (מ"מ)': "9,930"}},
    "VOLVO|EC300E": {
        "url": "https://www.volvoce.com/europe/en/products/excavators/ec300e/",
        "specs": {'משקל עצמי (ק"ג)': "30,800", 'הספק מנוע (kW)': "170",
                  'נפח דלי (מ"ק)': "1.1–1.95", 'עומק חפירה מרבי (מ"מ)': "7,540",
                  'טווח מרבי (מ"מ)': "10,840"}},
    "VOLVO|EC380E": {
        "url": "https://www.volvoce.com/europe/en/products/excavators/ec380e/",
        "specs": {'משקל עצמי (ק"ג)': "39,900", 'הספק מנוע (kW)': "205",
                  'נפח דלי (מ"ק)': "1.5–3.1", 'עומק חפירה מרבי (מ"מ)': "8,220",
                  'טווח מרבי (מ"מ)': "11,680"}},
    "VOLVO|EC480E": {
        "url": "https://www.volvoce.com/europe/en/products/excavators/ec480e/",
        "specs": {'משקל עצמי (ק"ג)': "48,300", 'הספק מנוע (kW)': "270",
                  'נפח דלי (מ"ק)': "2.0–3.5", 'עומק חפירה מרבי (מ"מ)': "8,750",
                  'טווח מרבי (מ"מ)': "12,340"}},
    # ── Track Excavators — Hitachi ────────────────────────────────────────────
    "HITACHI|ZX85": {
        "url": "https://www.hitachicm.eu/machines/excavators/",
        "specs": {'משקל עצמי (ק"ג)': "8,760", 'הספק מנוע (kW)': "42",
                  'נפח דלי (מ"ק)': "0.32", 'עומק חפירה מרבי (מ"מ)': "4,375",
                  'טווח מרבי (מ"מ)': "7,175"}},
    "HITACHI|ZX135": {
        "url": "https://www.hitachicm.eu/machines/excavators/",
        "specs": {'משקל עצמי (ק"ג)': "13,500", 'הספק מנוע (kW)': "72.1",
                  'נפח דלי (מ"ק)': "0.50", 'עומק חפירה מרבי (מ"מ)': "6,020",
                  'טווח מרבי (מ"מ)': "8,830"}},
    "HITACHI|ZX210": {
        "url": "https://www.hitachicm.eu/machines/excavators/",
        "specs": {'משקל עצמי (ק"ג)': "21,500", 'הספק מנוע (kW)': "122",
                  'נפח דלי (מ"ק)': "0.90", 'עומק חפירה מרבי (מ"מ)': "6,950",
                  'טווח מרבי (מ"מ)': "10,160"}},
    "HITACHI|ZX350": {
        "url": "https://www.hitachicm.eu/machines/excavators/",
        "specs": {'משקל עצמי (ק"ג)': "35,200", 'הספק מנוע (kW)': "194",
                  'נפח דלי (מ"ק)': "1.50", 'עומק חפירה מרבי (מ"מ)': "8,150",
                  'טווח מרבי (מ"מ)': "11,650"}},
    # ── Track Excavators — Doosan / Develon ───────────────────────────────────
    "DOOSAN|DX140": {
        "url": "https://www.doosanequipment.com/en/excavators",
        "specs": {'משקל עצמי (ק"ג)': "14,500", 'הספק מנוע (kW)': "73",
                  'נפח דלי (מ"ק)': "0.52", 'עומק חפירה מרבי (מ"מ)': "6,005",
                  'טווח מרבי (מ"מ)': "8,875"}},
    "DOOSAN|DX225": {
        "url": "https://www.doosanequipment.com/en/excavators",
        "specs": {'משקל עצמי (ק"ג)': "22,900", 'הספק מנוע (kW)': "124",
                  'נפח דלי (מ"ק)': "0.93", 'עומק חפירה מרבי (מ"מ)': "6,810",
                  'טווח מרבי (מ"מ)': "9,990"}},
    # ── Track Excavators — Hyundai ────────────────────────────────────────────
    "HYUNDAI|HX145": {
        "url": "https://www.hd-ce.com/en/products/excavator.do",
        "specs": {'משקל עצמי (ק"ג)': "14,800", 'הספק מנוע (kW)': "85",
                  'נפח דלי (מ"ק)': "0.55", 'עומק חפירה מרבי (מ"מ)': "6,185",
                  'טווח מרבי (מ"מ)': "9,135"}},
    "HYUNDAI|HX220": {
        "url": "https://www.hd-ce.com/en/products/excavator.do",
        "specs": {'משקל עצמי (ק"ג)': "22,000", 'הספק מנוע (kW)': "122",
                  'נפח דלי (מ"ק)': "0.93", 'עומק חפירה מרבי (מ"מ)': "6,710",
                  'טווח מרבי (מ"מ)': "9,880"}},
    # ── Mini Excavators — Bobcat ──────────────────────────────────────────────
    "BOBCAT|E35": {
        "url": "https://www.bobcat.com/eu/en/equipment/compact-excavators/e35",
        "specs": {'משקל עצמי (ק"ג)': "3,630", 'הספק מנוע (kW)': "18.4",
                  'נפח דלי (מ"ק)': "0.07", 'עומק חפירה מרבי (מ"מ)': "3,175",
                  'טווח מרבי (מ"מ)': "5,260"}},
    "BOBCAT|E50": {
        "url": "https://www.bobcat.com/eu/en/equipment/compact-excavators/e50",
        "specs": {'משקל עצמי (ק"ג)': "5,245", 'הספק מנוע (kW)': "30",
                  'נפח דלי (מ"ק)': "0.13", 'עומק חפירה מרבי (מ"מ)': "3,875",
                  'טווח מרבי (מ"מ)': "6,255"}},
    "BOBCAT|E85": {
        "url": "https://www.bobcat.com/eu/en/equipment/compact-excavators/e85",
        "specs": {'משקל עצמי (ק"ג)': "8,545", 'הספק מנוע (kW)': "42.5",
                  'נפח דלי (מ"ק)': "0.21", 'עומק חפירה מרבי (מ"מ)': "4,660",
                  'טווח מרבי (מ"מ)': "7,330"}},
    # ── Backhoe Loaders ───────────────────────────────────────────────────────
    "JCB|3CX": {
        "url": "https://www.jcb.com/en-gb/products/backhoe-loaders/3cx",
        "specs": {'משקל עצמי (ק"ג)': "8,350", 'הספק מנוע (kW)': "74.2",
                  'נפח דלי טוען (מ"ק)': "1.0", 'נפח דלי חופר (מ"ק)': "0.21",
                  'עומק חפירה מרבי (מ"מ)': "5,880"}},
    "JCB|4CX": {
        "url": "https://www.jcb.com/en-gb/products/backhoe-loaders/4cx",
        "specs": {'משקל עצמי (ק"ג)': "9,960", 'הספק מנוע (kW)': "81",
                  'נפח דלי טוען (מ"ק)': "1.2", 'נפח דלי חופר (מ"ק)': "0.21",
                  'עומק חפירה מרבי (מ"מ)': "5,880"}},
    "CATERPILLAR|432": {
        "url": "https://www.cat.com/en_US/products/new/equipment/backhoe-loaders.html",
        "specs": {'משקל עצמי (ק"ג)': "8,572", 'הספק מנוע (kW)': "69",
                  'נפח דלי טוען (מ"ק)': "1.03", 'נפח דלי חופר (מ"ק)': "0.17",
                  'עומק חפירה מרבי (מ"מ)': "5,900"}},
    # ── Wheel Loaders — CAT ───────────────────────────────────────────────────
    "CATERPILLAR|914": {
        "url": "https://www.cat.com/en_US/products/new/equipment/wheel-loaders/small-wheel-loaders.html",
        "specs": {'משקל עצמי (ק"ג)': "8,755", 'הספק מנוע (kW)': "66.4",
                  'נפח דלי (מ"ק)': "1.30", 'עומס הרמה מדורג (ק"ג)': "3,946"}},
    "CATERPILLAR|930": {
        "url": "https://www.cat.com/en_US/products/new/equipment/wheel-loaders/small-wheel-loaders.html",
        "specs": {'משקל עצמי (ק"ג)': "12,545", 'הספק מנוע (kW)': "92.5",
                  'נפח דלי (מ"ק)': "1.90", 'עומס הרמה מדורג (ק"ג)': "6,101"}},
    "CATERPILLAR|950": {
        "url": "https://www.cat.com/en_US/products/new/equipment/wheel-loaders/medium-wheel-loaders.html",
        "specs": {'משקל עצמי (ק"ג)': "18,660", 'הספק מנוע (kW)': "154",
                  'נפח דלי (מ"ק)': "2.90", 'עומס הרמה מדורג (ק"ג)': "10,307"}},
    "CATERPILLAR|966": {
        "url": "https://www.cat.com/en_US/products/new/equipment/wheel-loaders/medium-wheel-loaders.html",
        "specs": {'משקל עצמי (ק"ג)': "24,040", 'הספק מנוע (kW)': "201",
                  'נפח דלי (מ"ק)': "4.0", 'עומס הרמה מדורג (ק"ג)': "14,151"}},
    # ── Wheel Loaders — Volvo ─────────────────────────────────────────────────
    "VOLVO|L60H": {
        "url": "https://www.volvoce.com/europe/en/products/wheel-loaders/l60h/",
        "specs": {'משקל עצמי (ק"ג)': "11,600", 'הספק מנוע (kW)': "93",
                  'נפח דלי (מ"ק)': "1.8–3.6", 'עומס הרמה מדורג (ק"ג)': "5,700"}},
    "VOLVO|L90H": {
        "url": "https://www.volvoce.com/europe/en/products/wheel-loaders/l90h/",
        "specs": {'משקל עצמי (ק"ג)': "14,500–17,300", 'הספק מנוע (kW)': "137",
                  'נפח דלי (מ"ק)': "2.2–7.0", 'עומס הרמה מדורג (ק"ג)': "10,100"}},
    "VOLVO|L120H": {
        "url": "https://www.volvoce.com/europe/en/products/wheel-loaders/l120h/",
        "specs": {'משקל עצמי (ק"ג)': "19,000–22,700", 'הספק מנוע (kW)': "183",
                  'נפח דלי (מ"ק)': "3.0–8.0", 'עומס הרמה מדורג (ק"ג)': "14,000"}},
    "VOLVO|L150H": {
        "url": "https://www.volvoce.com/europe/en/products/wheel-loaders/l150h/",
        "specs": {'משקל עצמי (ק"ג)': "24,500–28,800", 'הספק מנוע (kW)': "220",
                  'נפח דלי (מ"ק)': "4.0–10.5", 'עומס הרמה מדורג (ק"ג)': "17,500"}},
    # ── Wheel Loaders — Komatsu ───────────────────────────────────────────────
    "KOMATSU|WA200": {
        "url": "https://www.komatsu.com/en/products/wheel-loaders/",
        "specs": {'משקל עצמי (ק"ג)': "12,900", 'הספק מנוע (kW)': "93",
                  'נפח דלי (מ"ק)': "1.90", 'עומס הרמה מדורג (ק"ג)': "6,400"}},
    "KOMATSU|WA270": {
        "url": "https://www.komatsu.com/en/products/wheel-loaders/",
        "specs": {'משקל עצמי (ק"ג)': "14,865", 'הספק מנוע (kW)': "107",
                  'נפח דלי (מ"ק)': "2.30", 'עומס הרמה מדורג (ק"ג)': "8,000"}},
    "KOMATSU|WA380": {
        "url": "https://www.komatsu.com/en/products/wheel-loaders/",
        "specs": {'משקל עצמי (ק"ג)': "18,770", 'הספק מנוע (kW)': "149",
                  'נפח דלי (מ"ק)': "3.0", 'עומס הרמה מדורג (ק"ג)': "11,200"}},
    # ── Skid-Steer Loaders — Bobcat ───────────────────────────────────────────
    "BOBCAT|S510": {
        "url": "https://www.bobcat.com/eu/en/equipment/loaders/skid-steer-loaders/s510",
        "specs": {'משקל עצמי (ק"ג)': "2,700", 'הספק מנוע (kW)': "47.5",
                  'נפח דלי (מ"ק)': "0.35", 'עומס הרמה מדורג (ק"ג)': "842"}},
    "BOBCAT|S630": {
        "url": "https://www.bobcat.com/eu/en/equipment/loaders/skid-steer-loaders/s630",
        "specs": {'משקל עצמי (ק"ג)': "3,387", 'הספק מנוע (kW)': "47.5",
                  'נפח דלי (מ"ק)': "0.44", 'עומס הרמה מדורג (ק"ג)': "1,093"}},
    "BOBCAT|S770": {
        "url": "https://www.bobcat.com/eu/en/equipment/loaders/skid-steer-loaders/s770",
        "specs": {'משקל עצמי (ק"ג)': "4,481", 'הספק מנוע (kW)': "68.5",
                  'נפח דלי (מ"ק)': "0.57", 'עומס הרמה מדורג (ק"ג)': "1,565"}},
    # ── Diesel Forklifts — Toyota ─────────────────────────────────────────────
    "TOYOTA|8FD25": {
        "url": "https://www.toyota-forklifts.eu/en/products/internal-combustion-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,500", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "3,949", 'הספק מנוע (kW)': "43"}},
    "TOYOTA|8FD30": {
        "url": "https://www.toyota-forklifts.eu/en/products/internal-combustion-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "3,000", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "4,245", 'הספק מנוע (kW)': "43"}},
    "TOYOTA|8FD35": {
        "url": "https://www.toyota-forklifts.eu/en/products/internal-combustion-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "3,500", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "4,825", 'הספק מנוע (kW)': "51"}},
    # ── Diesel Forklifts — Jungheinrich ───────────────────────────────────────
    "JUNGHEINRICH|DFG316": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/diesel-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "1,600", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "2,780", 'הספק מנוע (kW)': "30"}},
    "JUNGHEINRICH|DFG320": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/diesel-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,000", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "3,140", 'הספק מנוע (kW)': "30"}},
    "JUNGHEINRICH|DFG425": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/diesel-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,500", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "3,450", 'הספק מנוע (kW)': "36"}},
    # ── Electric Forklifts — Jungheinrich ─────────────────────────────────────
    "JUNGHEINRICH|EFG115": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "1,500", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "2,350", 'מתח סוללה (V)': "48"}},
    "JUNGHEINRICH|EFG220": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,000", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "3,450", 'מתח סוללה (V)': "80"}},
    "JUNGHEINRICH|EFG425": {
        "url": "https://www.jungheinrich.com/en/products/industrial-trucks/forklifts/counterbalance-forklifts/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,500", 'גובה הרמה מרבי (מ"מ)': "3,300",
                  'משקל עצמי (ק"ג)': "3,750", 'מתח סוללה (V)': "80"}},
    # ── Electric Forklifts — Toyota ───────────────────────────────────────────
    "TOYOTA|8FBE15": {
        "url": "https://www.toyota-forklifts.eu/en/products/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "1,500", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "2,050", 'מתח סוללה (V)': "48"}},
    "TOYOTA|8FBE20": {
        "url": "https://www.toyota-forklifts.eu/en/products/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,000", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "2,630", 'מתח סוללה (V)': "48"}},
    "TOYOTA|8FBE25": {
        "url": "https://www.toyota-forklifts.eu/en/products/electric-forklifts/",
        "specs": {'קיבולת הרמה (ק"ג)': "2,500", 'גובה הרמה מרבי (מ"מ)': "3,000",
                  'משקל עצמי (ק"ג)': "3,080", 'מתח סוללה (V)': "80"}},
    # ── Telescopic Handlers — Manitou ─────────────────────────────────────────
    "MANITOU|MT625": {
        "url": "https://www.manitou.com/en/telehandlers/rough-terrain-telescopic-handlers/",
        "specs": {'קיבולת הרמה מרבית (ק"ג)': "2,500", 'גובה הרמה מרבי (מ"מ)': "5,800",
                  'טווח קדמי מרבי (מ"מ)': "3,400", 'משקל עצמי (ק"ג)': "4,690"}},
    "MANITOU|MT732": {
        "url": "https://www.manitou.com/en/telehandlers/rough-terrain-telescopic-handlers/",
        "specs": {'קיבולת הרמה מרבית (ק"ג)': "3,200", 'גובה הרמה מרבי (מ"מ)': "7,000",
                  'טווח קדמי מרבי (מ"מ)': "4,200", 'משקל עצמי (ק"ג)': "6,700"}},
    "MANITOU|MT932": {
        "url": "https://www.manitou.com/en/telehandlers/rough-terrain-telescopic-handlers/",
        "specs": {'קיבולת הרמה מרבית (ק"ג)': "3,200", 'גובה הרמה מרבי (מ"מ)': "8,900",
                  'טווח קדמי מרבי (מ"מ)': "5,300", 'משקל עצמי (ק"ג)': "8,100"}},
    "MANITOU|MT1440": {
        "url": "https://www.manitou.com/en/telehandlers/rough-terrain-telescopic-handlers/",
        "specs": {'קיבולת הרמה מרבית (ק"ג)': "4,000", 'גובה הרמה מרבי (מ"מ)': "13,600",
                  'טווח קדמי מרבי (מ"מ)': "9,900", 'משקל עצמי (ק"ג)': "14,800"}},
    "MERLO|P40.17": {
        "url": "https://www.merlo.com/en/products/turbofarmer/",
        "specs": {'קיבולת הרמה מרבית (ק"ג)': "4,000", 'גובה הרמה מרבי (מ"מ)': "16,700",
                  'טווח קדמי מרבי (מ"מ)': "12,900", 'משקל עצמי (ק"ג)': "13,000"}},
    # ── Scissor Lifts — JLG ───────────────────────────────────────────────────
    "JLG|1930ES": {
        "url": "https://www.jlg.com/en/equipment/scissor-lifts/electric-scissor-lifts/1930es",
        "specs": {"גובה עבודה מרבי (מ')": "7.79", 'עומס פלטפורמה (ק"ג)': "454",
                  'משקל עצמי (ק"ג)': "1,497", "מידות פלטפורמה": "2.24 × 0.81 מ'"}},
    "JLG|2630ES": {
        "url": "https://www.jlg.com/en/equipment/scissor-lifts/electric-scissor-lifts/",
        "specs": {"גובה עבודה מרבי (מ')": "9.92", 'עומס פלטפורמה (ק"ג)': "454",
                  'משקל עצמי (ק"ג)': "2,431", "מידות פלטפורמה": "2.51 × 0.81 מ'"}},
    "JLG|3246ES": {
        "url": "https://www.jlg.com/en/equipment/scissor-lifts/electric-scissor-lifts/3246es",
        "specs": {"גובה עבודה מרבי (מ')": "11.75", 'עומס פלטפורמה (ק"ג)': "544",
                  'משקל עצמי (ק"ג)': "2,994", "מידות פלטפורמה": "2.77 × 1.37 מ'"}},
    # ── Scissor Lifts — Genie ─────────────────────────────────────────────────
    "GENIE|GS-1930": {
        "url": "https://www.genielift.com/en/products/scissor-lifts/electric-scissor-lifts/gs-1930",
        "specs": {"גובה עבודה מרבי (מ')": "7.79", 'עומס פלטפורמה (ק"ג)': "340",
                  'משקל עצמי (ק"ג)': "1,417", "מידות פלטפורמה": "2.24 × 0.76 מ'"}},
    "GENIE|GS-3246": {
        "url": "https://www.genielift.com/en/products/scissor-lifts/electric-scissor-lifts/gs-3246",
        "specs": {"גובה עבודה מרבי (מ')": "11.75", 'עומס פלטפורמה (ק"ג)': "544",
                  'משקל עצמי (ק"ג)': "2,821", "מידות פלטפורמה": "2.51 × 1.17 מ'"}},
    # ── Boom Lifts — JLG ──────────────────────────────────────────────────────
    "JLG|450AJ": {
        "url": "https://www.jlg.com/en/equipment/boom-lifts/articulating-boom-lifts/450aj",
        "specs": {"גובה עבודה מרבי (מ')": "15.72", 'עומס פלטפורמה (ק"ג)': "227",
                  'משקל עצמי (ק"ג)': "7,394", "מידות פלטפורמה": "0.91 × 0.76 מ'"}},
    "JLG|600AJ": {
        "url": "https://www.jlg.com/en/equipment/boom-lifts/articulating-boom-lifts/600aj",
        "specs": {"גובה עבודה מרבי (מ')": "20.39", 'עומס פלטפורמה (ק"ג)': "227",
                  'משקל עצמי (ק"ג)': "8,346", "מידות פלטפורמה": "0.91 × 0.76 מ'"}},
    "HAULOTTE|COMPACT 12": {
        "url": "https://www.haulotte.com/en/products/scissor-lifts/",
        "specs": {"גובה עבודה מרבי (מ')": "12.0", 'עומס פלטפורמה (ק"ג)': "230",
                  'משקל עצמי (ק"ג)': "2,080", "מידות פלטפורמה": "2.29 × 0.75 מ'"}},
    # ── Vibratory Rollers ─────────────────────────────────────────────────────
    "DYNAPAC|CA2500D": {
        "url": "https://www.dynapac.com/en/products/compactors/soil-compactors/single-drum/",
        "specs": {'משקל עצמי (ק"ג)': "12,570", 'רוחב גליל (מ"מ)': "2,130",
                  'הספק מנוע (kW)': "97", 'כוח צנטריפוגלי (kN)': "250"}},
    "BOMAG|BW138AD": {
        "url": "https://www.bomag.com/en/products/soil-compactors/tandem-rollers/",
        "specs": {'משקל עצמי (ק"ג)': "4,230", 'רוחב גליל (מ"מ)': "1,380",
                  'הספק מנוע (kW)': "29", 'כוח צנטריפוגלי (kN)': "45"}},
    "BOMAG|BW177D": {
        "url": "https://www.bomag.com/en/products/soil-compactors/single-drum-compactors/",
        "specs": {'משקל עצמי (ק"ג)': "10,300", 'רוחב גליל (מ"מ)': "1,680",
                  'הספק מנוע (kW)': "93", 'כוח צנטריפוגלי (kN)': "196"}},
    # ── Crawler Dozers — CAT ──────────────────────────────────────────────────
    "CATERPILLAR|D5": {
        "url": "https://www.cat.com/en_US/products/new/equipment/dozers/small-dozers.html",
        "specs": {'משקל עצמי (ק"ג)': "12,500", 'הספק מנוע (kW)': "94.6",
                  'נפח להב (מ"ק)': "2.50", 'לחץ קרקע (kPa)': "48"}},
    "CATERPILLAR|D6": {
        "url": "https://www.cat.com/en_US/products/new/equipment/dozers/medium-dozers.html",
        "specs": {'משקל עצמי (ק"ג)': "20,950", 'הספק מנוע (kW)': "153",
                  'נפח להב (מ"ק)': "3.50", 'לחץ קרקע (kPa)': "63"}},
    "CATERPILLAR|D8": {
        "url": "https://www.cat.com/en_US/products/new/equipment/dozers/large-dozers.html",
        "specs": {'משקל עצמי (ק"ג)': "38,145", 'הספק מנוע (kW)': "231",
                  'נפח להב (מ"ק)': "7.60", 'לחץ קרקע (kPa)': "70"}},
    "CATERPILLAR|D9T": {
        "url": "https://www.cat.com/en_US/products/new/equipment/dozers/large-dozers.html",
        "specs": {'משקל עצמי (ק"ג)': "49,830", 'הספק מנוע (kW)': "305",
                  'נפח להב (מ"ק)': "10.5", 'לחץ קרקע (kPa)': "76"}},
    "KOMATSU|D51": {
        "url": "https://www.komatsu.com/en/products/crawler-dozers/",
        "specs": {'משקל עצמי (ק"ג)': "11,760", 'הספק מנוע (kW)': "84",
                  'נפח להב (מ"ק)': "2.50", 'לחץ קרקע (kPa)': "43"}},
    "KOMATSU|D65": {
        "url": "https://www.komatsu.com/en/products/crawler-dozers/",
        "specs": {'משקל עצמי (ק"ג)': "21,250", 'הספק מנוע (kW)': "149",
                  'נפח להב (מ"ק)': "3.90", 'לחץ קרקע (kPa)': "63"}},
    # ── Mobile Cranes ─────────────────────────────────────────────────────────
    "TADANO|GR-500EX": {
        "url": "https://www.tadano.com/en/products/rough-terrain-cranes/",
        "specs": {"קיבולת הרמה מרבית (טון)": "50", "אורך זרוע מרבי (מ')": "43.5",
                  'משקל עצמי (ק"ג)': "36,800"}},
    "TADANO|GR-700EX": {
        "url": "https://www.tadano.com/en/products/rough-terrain-cranes/",
        "specs": {"קיבולת הרמה מרבית (טון)": "70", "אורך זרוע מרבי (מ')": "47.2",
                  'משקל עצמי (ק"ג)': "52,000"}},
    "LIEBHERR|LTM 1060-3.1": {
        "url": "https://www.liebherr.com/en/gbr/products/cranes/mobile-cranes/ltm-mobile-cranes/",
        "specs": {"קיבולת הרמה מרבית (טון)": "60", "אורך זרוע מרבי (מ')": "52",
                  'משקל עצמי (ק"ג)': "36,000"}},
    "LIEBHERR|LTM 1100-4.2": {
        "url": "https://www.liebherr.com/en/gbr/products/cranes/mobile-cranes/ltm-mobile-cranes/",
        "specs": {"קיבולת הרמה מרבית (טון)": "100", "אורך זרוע מרבי (מ')": "60",
                  'משקל עצמי (ק"ג)': "48,000"}},
    "LIEBHERR|LTM 1200-5.1": {
        "url": "https://www.liebherr.com/en/gbr/products/cranes/mobile-cranes/ltm-mobile-cranes/",
        "specs": {"קיבולת הרמה מרבית (טון)": "200", "אורך זרוע מרבי (מ')": "80",
                  'משקל עצמי (ק"ג)': "60,000"}},
    "GROVE|GMK4100": {
        "url": "https://www.manitowoccranes.com/en/cranes/grove",
        "specs": {"קיבולת הרמה מרבית (טון)": "100", "אורך זרוע מרבי (מ')": "60",
                  'משקל עצמי (ק"ג)': "48,000"}},
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().upper())


def _lookup_static(manufacturer: str, model: str) -> dict | None:
    mfr = _norm(manufacturer)
    mdl = _norm(model)
    exact = f"{mfr}|{mdl}"
    if exact in _S:
        return _S[exact]
    # Prefix / suffix partial match on same manufacturer
    for key, val in _S.items():
        db_mfr, db_mdl = key.split("|", 1)
        if db_mfr != mfr:
            continue
        if db_mdl.startswith(mdl) or mdl.startswith(db_mdl):
            return val
    return None


def _try_volvo_fetch(model: str, category_en: str) -> dict | None:
    """Fetch specs from Volvo CE's static product pages (confirmed reachable)."""
    cat = category_en.strip().upper()
    if "EXCAVAT" in cat:
        slug_cat = "excavators"
    elif "LOADER" in cat and "WHEEL" in cat:
        slug_cat = "wheel-loaders"
    elif "HAULER" in cat or "ARTICULATED" in cat:
        slug_cat = "articulated-haulers"
    elif "COMPACTOR" in cat or "ROLLER" in cat:
        slug_cat = "soil-compactors"
    elif "PAVER" in cat:
        slug_cat = "asphalt-pavers"
    else:
        return None

    slug_model = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    url = f"https://www.volvoce.com/europe/en/products/{slug_cat}/{slug_model}/"

    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

    # Parse key stats from the page text
    specs: dict[str, str] = {}
    patterns = [
        (r"(\d[\d,\.]+)\s*(?:–|-)\s*(\d[\d,\.]+)\s*kg", "משקל עצמי (ק\"ג)"),
        (r"(\d[\d,\.]+)\s*kW\s*Gross\s*power", "הספק מנוע (kW)"),
        (r"(\d[\d,\.]+)\s*–\s*(\d[\d,\.]+)\s*m³", "נפח דלי (מ\"ק)"),
        (r"Max\.\s*digging\s*reach[^\d]*(\d[\d,\.]+)\s*mm", "טווח מרבי (מ\"מ)"),
    ]
    # Simple weight/power extraction
    weight = re.search(r'"([\d,]+)\s*(?:–|-)?\s*(?:[\d,]+)?\s*kg"', html)
    power  = re.search(r'"(\d+(?:\.\d+)?)\s*kW"', html)
    reach  = re.search(r'"([\d,]+)\s*mm".*?digging reach|digging reach.*?"([\d,]+)\s*mm"',
                       html, re.IGNORECASE)

    if weight:
        specs['משקל עצמי (ק"ג)'] = weight.group(1)
    if power:
        specs['הספק מנוע (kW)'] = power.group(1)
    if reach:
        val = reach.group(1) or reach.group(2)
        if val:
            specs['טווח מרבי (מ"מ)'] = val

    if specs:
        specs["_url"] = url
    return specs or None


# ── Public API ────────────────────────────────────────────────────────────────
def get_manufacturer_url(manufacturer: str) -> str | None:
    key = _norm(manufacturer)
    if key in MANUFACTURER_SITES:
        return MANUFACTURER_SITES[key]
    for k, v in MANUFACTURER_SITES.items():
        if k in key or key in k:
            return v
    return None


def build_search_links(manufacturer: str, model: str) -> dict[str, str]:
    """External spec-search links for any model."""
    q = f"{manufacturer}+{model}".replace(" ", "+")
    return {
        "🔍 RitchieSpecs": (
            f"https://www.ritchiespecs.com/specification?type="
            f"{manufacturer.replace(' ', '+')}&q={model.replace(' ', '+')}"
        ),
        "🌐 Google": (
            f"https://www.google.com/search?q={q}+specifications+technical+specs"
        ),
        "🏗️ MachineryZone": (
            f"https://www.machineryzone.eu/search?q={manufacturer.replace(' ', '+')}+{model.replace(' ', '+')}"
        ),
    }


def get_web_specs(manufacturer: str, model: str, category_en: str) -> dict | None:
    """
    Return specs dict (Hebrew keys + '_url') for a machine, or None.
    Priority: static DB → Volvo CE live fetch → None.
    Results cached 30 days.
    """
    cache_key = f"web2|{_norm(manufacturer)}|{_norm(model)}|{category_en}"
    now = time.time()

    # Cache hit
    if cache_key in _cache:
        entry = _cache[cache_key]
        if now - entry.get("fetched", 0) < _TTL:
            data = entry.get("specs", {})
            return data if data else None

    # 1. Static DB
    row = _lookup_static(manufacturer, model)
    if row:
        result = dict(row["specs"])
        result["_url"] = row.get("url", get_manufacturer_url(manufacturer) or "")
        _cache[cache_key] = {"specs": result, "fetched": now}
        _save_cache()
        return result

    # 2. Volvo CE live fetch
    if _norm(manufacturer) in ("VOLVO", "VOLVO CE"):
        volvo = _try_volvo_fetch(model, category_en)
        if volvo:
            _cache[cache_key] = {"specs": volvo, "fetched": now}
            _save_cache()
            return volvo

    # Cache negative result (short TTL: 1 day, don't want to miss new DB entries)
    _cache[cache_key] = {"specs": {}, "fetched": now - _TTL + 86_400}
    _save_cache()
    return None
