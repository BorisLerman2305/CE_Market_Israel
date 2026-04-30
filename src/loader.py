"""
Load and merge the two Israeli construction equipment sales Excel files into a
single tidy long-format DataFrame.

Raw file layout (one sheet per file, data starts at row 4):
  Col 0  – קוד סוג צמה  (category code)
  Col 1  – סוג צמה      (category, Hebrew)
  Col 2  – סוג צמה-אנגלית (category, English)
  Col 3  – תוצר שלדה    (manufacturer, Hebrew)
  Col 4  – תוצר שלדה-אנגלית (manufacturer, English)
  Col 5  – קוד כלי      (model code)
  Col 6  – דגם          (model name)
  Col 7  – סוג יבוא     (import type: מסחרי=commercial / אישי=personal)
  Col 8  – סה"כ כלים    (grand total across all years in this file)
  Col 9  – new units, most-recent year
  Col 10 – used units, most-recent year
  Col 11 – new units, second year
  Col 12 – used units, second year
  ...repeating pairs for each year...
  Col 19 – new units, oldest/aggregate column ("עד YYYY")
  Col 20 – used units, oldest/aggregate column

Subtotal rows are identified by col 0 being 'סה"כ לתוצר' or 'סה"כ לסוג'.
These are dropped; only individual-machine rows are kept.

Output schema (long format):
  category_code   int
  category_he     str   Hebrew equipment type
  category_en     str   English equipment type
  manufacturer_he str
  manufacturer_en str
  model_code      str
  model_name      str
  import_type     str   'commercial' | 'personal'
  year            int
  condition       str   'new' | 'used'
  units           int
"""

from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# File 1: annual columns 2026, 2025, 2024, 2023, 2022, then "up to 2021" aggregate
FILE1 = RAW_DIR / "sales_2022_2026.xlsx"
# File 2: annual columns 2022, 2021, 2020, 2019, 2018, then "up to 2017" aggregate
FILE2 = RAW_DIR / "sales_2017_2022.xlsx"

SUBTOTAL_MARKERS = {"סה\"כ לתוצר", "סה\"כ לסוג", "סה\"כ ללקוח"}

IMPORT_TYPE_MAP = {"מסחרי": "commercial", "אישי": "personal", "לא ידוע": "unknown"}


def _parse_file(path: Path, years: list[int], aggregate_year: int) -> pd.DataFrame:
    """
    Parse one raw Excel file into long-format rows.

    years          – the 5 individual calendar years in column order (newest first)
    aggregate_year – the label to use for the "עד YYYY" aggregate pair
    """
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype={0: object})

    # Drop the two header rows and the empty first row
    data = raw.iloc[3:].reset_index(drop=True)

    # Drop subtotal rows
    data = data[~data[0].isin(SUBTOTAL_MARKERS)].copy()

    # Drop rows where col 0 is NaN or non-numeric (stray headers)
    data = data[pd.to_numeric(data[0], errors="coerce").notna()].copy()
    data[0] = data[0].astype(int)

    # Build year-column mapping: each year occupies 2 consecutive cols starting at col 9
    # Col 9,10 → years[0]; 11,12 → years[1]; ... 19,20 → aggregate_year
    all_years = years + [aggregate_year]
    year_col_pairs = [(9 + i * 2, 10 + i * 2) for i in range(6)]

    records = []
    for _, row in data.iterrows():
        base = {
            "category_code": int(row[0]),
            "category_he": row[1],
            "category_en": row[2],
            "manufacturer_he": row[3],
            "manufacturer_en": row[4],
            "model_code": str(row[5]) if pd.notna(row[5]) else None,
            "model_name": str(row[6]) if pd.notna(row[6]) else None,
            "import_type": IMPORT_TYPE_MAP.get(str(row[7]).strip(), str(row[7]).strip()),
        }
        for year, (col_new, col_used) in zip(all_years, year_col_pairs):
            new_units = row[col_new]
            used_units = row[col_used]
            if pd.notna(new_units) and new_units > 0:
                records.append({**base, "year": year, "condition": "new", "units": int(new_units)})
            if pd.notna(used_units) and used_units > 0:
                records.append({**base, "year": year, "condition": "used", "units": int(used_units)})

    return pd.DataFrame(records)


def load_raw() -> pd.DataFrame:
    """
    Return merged long-format DataFrame covering 2017–2026.

    Strategy:
    - File 2 provides individual yearly data for 2018–2022.
    - File 1 provides individual yearly data for 2022–2026.
    - 2022 appears in both files; File 1's 2022 takes precedence (more recent export).
    - The "עד 2021" aggregate from File 1 and "עד 2017" aggregate from File 2 are
      included with synthetic year values 2021 and 2017 respectively, labelled
      as aggregate rows via the 'is_aggregate' flag.
    - For granular year-over-year analysis use is_aggregate == False only.
    """
    # File 1: years newest→oldest: 2026, 2025, 2024, 2023, 2022 | agg=עד2021
    df1 = _parse_file(FILE1, years=[2026, 2025, 2024, 2023, 2022], aggregate_year=2021)

    # File 2: years newest→oldest: 2022, 2021, 2020, 2019, 2018 | agg=עד2017
    df2 = _parse_file(FILE2, years=[2022, 2021, 2020, 2019, 2018], aggregate_year=2017)

    # Mark aggregate rows before we set the flag on both
    df1["is_aggregate"] = df1["year"] == 2021
    df2["is_aggregate"] = df2["year"] == 2017

    # Drop file-2 data for 2022 (file-1 is the authoritative source)
    df2 = df2[df2["year"] != 2022]

    merged = pd.concat([df2, df1], ignore_index=True)
    merged = merged.sort_values(["category_code", "manufacturer_en", "model_name", "year", "condition"])
    merged = merged.reset_index(drop=True)

    return merged


def load_annual() -> pd.DataFrame:
    """Convenience wrapper: returns only individual-year rows (no aggregates)."""
    return load_raw()[lambda df: ~df["is_aggregate"]].reset_index(drop=True)
