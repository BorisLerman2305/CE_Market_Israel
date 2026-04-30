"""
Official Israeli importers / dealers for each manufacturer in the dataset.
Keys match manufacturer_en column values exactly.
Sources searched April 2026.
"""

IMPORTERS: dict[str, dict] = {
    # ── Forklifts ──────────────────────────────────────────────────────────────
    "STILL": {
        "name_he": "איגל פורקליפטס ולוגיסטיקה",
        "name_en": "Eagle Forklifts & Logistics Ltd.",
        "website": "https://www.still.co.il",
        "phone": "+972-3-3728644",
    },
    "TOYOTA": {
        "name_he": "יוניון רכב תעשייתי",
        "name_en": "Union Industrial Vehicle Ltd.",
        "website": "https://toyota-forklift.co.il",
        "phone": "+972-77-3339799",
    },
    "LINDE": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.linde-mh.com/en/technical/Location-Finder.html",
        "phone": "",
        "note": "יש לאמת דרך אתר לינדה הרשמי",
    },
    "JUNGHEINRICH": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.jungheinrich.com",
        "phone": "",
        "note": "יש לאמת דרך אתר יונגהיינריך הרשמי",
    },
    "CLARK": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "HYSTER": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "MITSUBISHI": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "TOYOTA": {
        "name_he": "יוניון רכב תעשייתי",
        "name_en": "Union Industrial Vehicle Ltd.",
        "website": "https://toyota-forklift.co.il",
        "phone": "+972-77-3339799",
    },
    "B.T.": {
        "name_he": "יוניון רכב תעשייתי",
        "name_en": "Union Industrial Vehicle Ltd.",
        "website": "https://toyota-forklift.co.il",
        "phone": "+972-77-3339799",
        "note": "BT (Raymond) הם חלק מקבוצת Toyota Material Handling",
    },
    "RAYMOND": {
        "name_he": "יוניון רכב תעשייתי",
        "name_en": "Union Industrial Vehicle Ltd.",
        "website": "https://toyota-forklift.co.il",
        "phone": "+972-77-3339799",
    },
    "UNICARRIERS": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "ATLET": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "ATLET - NISSAN": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "CROWN": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "NARROW AISLE": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Construction Equipment – Caterpillar/ITE ───────────────────────────────
    "CATERPILLAR": {
        "name_he": "טרקטורים וציוד – ITE (זוקו)",
        "name_en": "Israel Tractors & Equipment – ITE (Zoko Enterprises)",
        "website": "https://www.ite-cat.co.il",
        "phone": "",
    },
    # ── Construction Equipment – Comasco ──────────────────────────────────────
    "J.C.B (BAMFORD)": {
        "name_he": "קומסקו",
        "name_en": "Comasco Construction Machinery & Systems Ltd.",
        "website": "https://comasco.co.il",
        "phone": "+972-974-99300",
        "note": "יבואן רשמי מאז 1966",
    },
    "POTAIN": {
        "name_he": "קומסקו",
        "name_en": "Comasco Construction Machinery & Systems Ltd.",
        "website": "https://comasco.co.il",
        "phone": "+972-974-99300",
        "note": "יבואן רשמי מאז 1963",
    },
    # ── Construction Equipment – Emcol ────────────────────────────────────────
    "BOBCAT": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
    },
    "DOOSAN": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
        "note": "דואסן שונה לדבלון (DEVELON) ב-2022",
    },
    "DOOSAN-BOBCAT": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
    },
    "DEVELON": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
    },
    "AMMANN": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
    },
    "HIDROMEK": {
        "name_he": "אמקול",
        "name_en": "Emcol",
        "website": "https://www.emcol.co.il",
        "phone": "3955*",
    },
    # ── Construction Equipment – Volvo CE ─────────────────────────────────────
    "VOLVO": {
        "name_he": "מאיר'ס רכב ומשאיות",
        "name_en": "Mayer's Cars and Trucks",
        "website": "https://www.volvoce.com/middle-east/en-sa/contact-us/dealer-locator/",
        "phone": "",
        "note": "יש לאמת מול Volvo CE dealer locator",
    },
    # ── Construction Equipment – Hyundai ──────────────────────────────────────
    "HYUNDAI": {
        "name_he": "אפקו ציוד בע\"מ",
        "name_en": "EFCO Equipment Ltd.",
        "website": "",
        "phone": "",
    },
    # ── Aerial Work Platforms ─────────────────────────────────────────────────
    "J.L.G": {
        "name_he": "רום ישראל",
        "name_en": "Rom Israel Access Platforms",
        "website": "https://www.rom.co.il",
        "phone": "",
    },
    "GENIE - BOOM": {
        "name_he": "רום ישראל",
        "name_en": "Rom Israel Access Platforms",
        "website": "https://www.rom.co.il",
        "phone": "",
        "note": "יש לאמת – ROM מייצגת פלטפורמות הרמה בישראל",
    },
    "SKYJACK": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "HAULOTTE": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "NIFTYLIFT": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Compactors / Road Construction ────────────────────────────────────────
    "BOMAG": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.bomag.com/ww-en/services/support-and-training/locations-dealers/dealer/",
        "phone": "",
        "note": "יש לאמת דרך אתר BOMAG הרשמי",
    },
    "HAMM (GEBRUEDER)": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.wirtgen-group.com",
        "phone": "",
        "note": "Wirtgen Group (John Deere) – יש לאמת יבואן ישראלי",
    },
    "VOGELE": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.wirtgen-group.com",
        "phone": "",
        "note": "Wirtgen Group (John Deere) – יש לאמת יבואן ישראלי",
    },
    "DYNAPAC": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "MIKASA": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "WACKER": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Road Sweepers ─────────────────────────────────────────────────────────
    "SCHMIDT": {
        "name_he": "גד-אל ציוד עירוני",
        "name_en": "Gad-El Municipal Equipment Ltd.",
        "website": "https://gad-el.co.il",
        "phone": "",
        "note": "גד-אל מייבאת ציוד עירוני – יש לאמת ל-Schmidt ספציפית",
    },
    "BUCHER": {
        "name_he": "גד-אל ציוד עירוני",
        "name_en": "Gad-El Municipal Equipment Ltd.",
        "website": "https://gad-el.co.il",
        "phone": "",
    },
    "HAKO": {
        "name_he": "גד-אל ציוד עירוני",
        "name_en": "Gad-El Municipal Equipment Ltd.",
        "website": "https://gad-el.co.il",
        "phone": "",
    },
    "RAVO": {
        "name_he": "גד-אל ציוד עירוני",
        "name_en": "Gad-El Municipal Equipment Ltd.",
        "website": "https://gad-el.co.il",
        "phone": "",
    },
    # ── Cranes ────────────────────────────────────────────────────────────────
    "YONGMAO": {
        "name_he": "סקיילין עגורנים וטכנולוגיות",
        "name_en": "Skyline Cranes and Technologies",
        "website": "https://sky-line.co.il",
        "phone": "+972-3-9033901",
        "note": "נציגות בלעדית של Yongmao בישראל",
    },
    "GROVE": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "TADANO": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "DEMAG": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "LIEBHERR": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.liebherr.com",
        "phone": "",
        "note": "ליבהר פועלת בישראל ישירות ו/או דרך שלוחה",
    },
    "COMANSA": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Telehandlers ──────────────────────────────────────────────────────────
    "MERLO": {
        "name_he": "שי-מגן ציוד הרמה",
        "name_en": "Shai-Magen Lifting Equipment",
        "website": "https://www.shaimagen.com",
        "phone": "",
    },
    "MANITOU": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "DIECI": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "MAGNI": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Air Compressors ───────────────────────────────────────────────────────
    "ATLAS COPCO": {
        "name_he": "אוטומציה ירוחם ושות'",
        "name_en": "Automation Yeruham & Co.",
        "website": "https://ayeruham.com",
        "phone": "",
        "note": "גם Epiroc (שהתפרד מ-Atlas Copco) פועל בישראל",
    },
    "KAESER": {
        "name_he": "קיזר קומפרסורים ישראל",
        "name_en": "Kaeser Compressors Israel Ltd.",
        "website": "https://www.kaeser.com/int-en/company/about-us/kaeser-worldwide/israel",
        "phone": "+972-9-7885888",
        "note": "משרד ישיר של Kaeser",
    },
    "EPIROC": {
        "name_he": "אוטומציה ירוחם ושות'",
        "name_en": "Automation Yeruham & Co.",
        "website": "https://ayeruham.com",
        "phone": "",
    },
    "INGERSOLL RAND": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "DENAIR": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Stone Crushing & Screening ────────────────────────────────────────────
    "KLEEMANN REINER": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.wirtgen-group.com",
        "phone": "",
        "note": "Wirtgen Group (John Deere) – יש לאמת יבואן ישראלי",
    },
    "METSO": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "TEREX": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "MCCLOSKEY": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "RUBBLE MASTER": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "KEESTRACK": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Skid Steers ───────────────────────────────────────────────────────────
    "GEHL": {
        "name_he": "",
        "name_en": "",
        "website": "https://www.gehl.com/en-US/store-locator",
        "phone": "",
        "note": "יש לאמת דרך Gehl dealer locator",
    },
    "CASE": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Pavers & Finishers ────────────────────────────────────────────────────
    "LEE BOY": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    # ── Drills ────────────────────────────────────────────────────────────────
    "COMACCHIO": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "CHARLES MACHINE WORKS DITCHWIT": {
        "name_he": "",
        "name_en": "Ditch Witch",
        "website": "https://www.ditchwitch.com",
        "phone": "",
    },
    # ── Chinese brands (growing presence) ────────────────────────────────────
    "XCMG": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "SANY": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "YANMAR": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "KUBOTA": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "TAKEUCHI": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "KOMATSU": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "HITACHI": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "SUNWARD": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
    "NINGBO": {
        "name_he": "",
        "name_en": "",
        "website": "",
        "phone": "",
    },
}


def get_importer(manufacturer_en: str) -> dict:
    """Return importer info dict for a brand, or empty dict if unknown."""
    return IMPORTERS.get(manufacturer_en, {})


def importer_display(manufacturer_en: str) -> str:
    """Short one-line display string for use in tables/cards."""
    info = get_importer(manufacturer_en)
    if not info or not info.get("name_en"):
        return "—"
    name = info.get("name_he") or info.get("name_en", "")
    website = info.get("website", "")
    if website:
        return f"[{name}]({website})"
    return name
