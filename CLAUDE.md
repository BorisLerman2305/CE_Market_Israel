# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Analysis of the Israeli construction equipment (צמה – ציוד מכני הנדסי) market using official machine registration data covering **2017 through April 2026**. Delivered as an interactive Hebrew-language Streamlit dashboard.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard (opens at http://localhost:8501)
streamlit run app.py

# Quick data sanity-check
python -c "from src.loader import load_annual; df = load_annual(); print(df.shape, df.year.unique())"
```

## Project structure

```
app.py                          # Page 1 – Market Share (Streamlit entry point)
pages/
  1_Cross_Reference.py          # Page 2 – Cross-Reference / model comparison
src/
  loader.py                     # Parse both Excel files → single tidy long-format DataFrame
  analysis.py                   # Market analysis helpers (totals, shares, trends, top models)
  importers.py                  # Importer data per brand — NOT used in UI (data accuracy TBD)
data/raw/
  sales_2022_2026.xlsx          # Individual years 2022–2026 (April), + "up to 2021" aggregate
  sales_2017_2022.xlsx          # Individual years 2018–2022, + "up to 2017" aggregate
.streamlit/config.toml          # Theme: primaryColor="#1B4F91", clean blue/white
notebooks/
  market_analysis.ipynb         # Starter Jupyter notebook
outputs/
  charts/                       # Saved PNG plots
  reports/                      # Excel / summary reports
```

## Data schema

`load_annual()` returns one row per (machine model × import type × year × condition):

| Column | Type | Description |
|---|---|---|
| `category_code` | int | Numeric equipment type code |
| `category_he` | str | Equipment type (Hebrew) |
| `category_en` | str | Equipment type (English) e.g. `EXCAVATORS` |
| `manufacturer_he` | str | Brand (Hebrew) |
| `manufacturer_en` | str | Brand (English) e.g. `CATERPILLAR` |
| `model_code` | str | Numeric model code |
| `model_name` | str | Model designation e.g. `D9T` |
| `import_type` | str | `commercial` / `personal` / `unknown` |
| `year` | int | Registration year |
| `condition` | str | `new` or `used` |
| `units` | int | Number of machines registered |
| `is_aggregate` | bool | `True` for the rolled-up "up to YYYY" rows |

`load_raw()` includes aggregate rows (`is_aggregate=True`). Dashboard always uses `load_annual()`.

## Key data facts

- **2026 is partial** (January–April only). Exclude or annualise for YoY comparisons.
- **2022 appears in both source files.** `loader.py` uses File 1 as authoritative for 2022; File 2's 2022 rows are dropped.
- **New machines only** — all dashboard pages filter `condition == "new"` and `~is_aggregate`.
- Raw files contain subtotal rows (`סה"כ לתוצר`, `סה"כ לסוג`) — `loader.py` drops them automatically.

## Dashboard pages

### Page 1 – Market Share (`app.py`)

Fully Hebrew UI. Sidebar controls: year range slider (default 2018–2025), top-N slider (3–10 manufacturers), and **Excel file upload** (Phase 1 manual upload).

File upload flow:
- User picks period radio ("2022–2026" → `FILE1`, "2017–2022" → `FILE2`)
- `st.file_uploader` saves to `data/raw/`
- `load_data.clear()` + `st.rerun()` refreshes all charts

Main view (segment-centric, single page, no scrolling):
- Segment selectbox (Hebrew category + unit count, sorted by volume)
- 4 KPI metrics: total units, #1 brand (+ share%), #2 brand (+ share%), YoY change
- Donut chart (market share by manufacturer, top-N + "אחרים")
- Line chart (yearly trend for top-N manufacturers)
- Horizontal bar chart (top 15 models, "manufacturer – model" labels)

### Page 2 – Cross-Reference (`pages/1_Cross_Reference.py`)

User selects: Segment → Base manufacturer → Base model → Competitor manufacturer.
System **auto-selects** the competitor model (Phase 1: closest sales volume; Phase 2: technical spec matching via web — deferred).

Layout:
- Shared segment selector with year slider in sidebar
- `col_base` (🔵): manufacturer + model dropdowns
- `col_vs`: "VS" divider
- `col_comp` (🔴): competitor manufacturer dropdown; auto-matched model shown in styled badge with phase note
- Grouped bar chart (yearly units, base vs competitor)
- 4 KPI metrics + summary dataframe

## Planned phases (not yet implemented)

- **Phase 2 – Auto-match competitor model:** Technical spec matching via web search (replacing sales-volume proximity)
- **Phase 2 – Chamber of Commerce integration:** Monthly auto-pull of the latest Excel from the Chamber of Commerce website (replacing manual upload)
- **Importers:** `src/importers.py` exists but is excluded from UI — many entries were found to be incorrect and need validation before reintroduction

## Extending the analysis

- Add analysis functions in `src/analysis.py`; accept optional `df` argument to avoid re-reading files.
- Both Streamlit pages use `@st.cache_data` — changes to `loader.py` require a browser refresh or cache clear.
- Save charts to `outputs/charts/` and Excel exports to `outputs/reports/`.
