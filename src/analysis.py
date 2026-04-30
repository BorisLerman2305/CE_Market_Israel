"""
Common market analysis queries built on top of load_annual().
All functions accept an optional pre-loaded DataFrame to avoid re-reading the files.
"""

from __future__ import annotations
import pandas as pd
from src.loader import load_annual


def _df(df: pd.DataFrame | None) -> pd.DataFrame:
    return load_annual() if df is None else df


# ── Market totals ──────────────────────────────────────────────────────────────

def total_by_year(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Total units sold per year, split by new/used."""
    return (
        _df(df)
        .groupby(["year", "condition"])["units"]
        .sum()
        .unstack("condition")
        .fillna(0)
        .astype(int)
        .assign(total=lambda x: x.sum(axis=1))
    )


def market_share_by_manufacturer(
    df: pd.DataFrame | None = None,
    condition: str = "new",
    years: list[int] | None = None,
) -> pd.DataFrame:
    """
    Units and market share per manufacturer for the given condition and year range.
    condition: 'new' | 'used' | 'all'
    """
    d = _df(df)
    if condition != "all":
        d = d[d["condition"] == condition]
    if years:
        d = d[d["year"].isin(years)]
    result = (
        d.groupby("manufacturer_en")["units"]
        .sum()
        .reset_index()
        .sort_values("units", ascending=False)
    )
    result["market_share_%"] = (result["units"] / result["units"].sum() * 100).round(1)
    return result.reset_index(drop=True)


def market_share_by_category(
    df: pd.DataFrame | None = None,
    condition: str = "new",
    years: list[int] | None = None,
) -> pd.DataFrame:
    """Units and market share per equipment category."""
    d = _df(df)
    if condition != "all":
        d = d[d["condition"] == condition]
    if years:
        d = d[d["year"].isin(years)]
    result = (
        d.groupby(["category_code", "category_en"])["units"]
        .sum()
        .reset_index()
        .sort_values("units", ascending=False)
    )
    result["market_share_%"] = (result["units"] / result["units"].sum() * 100).round(1)
    return result.reset_index(drop=True)


# ── Trend analysis ─────────────────────────────────────────────────────────────

def trend_by_category(
    df: pd.DataFrame | None = None,
    condition: str = "new",
) -> pd.DataFrame:
    """Annual unit totals for each equipment category (pivot: rows=year, cols=category)."""
    d = _df(df)
    if condition != "all":
        d = d[d["condition"] == condition]
    return (
        d.groupby(["year", "category_en"])["units"]
        .sum()
        .unstack("category_en")
        .fillna(0)
        .astype(int)
    )


def trend_by_manufacturer(
    df: pd.DataFrame | None = None,
    category_en: str | None = None,
    condition: str = "new",
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Annual unit totals per manufacturer, optionally filtered by category.
    Returns only the top_n manufacturers by total volume.
    """
    d = _df(df)
    if condition != "all":
        d = d[d["condition"] == condition]
    if category_en:
        d = d[d["category_en"] == category_en]
    pivot = (
        d.groupby(["year", "manufacturer_en"])["units"]
        .sum()
        .unstack("manufacturer_en")
        .fillna(0)
        .astype(int)
    )
    top = pivot.sum().nlargest(top_n).index
    return pivot[top]


# ── Model-level queries ────────────────────────────────────────────────────────

def top_models(
    df: pd.DataFrame | None = None,
    category_en: str | None = None,
    manufacturer_en: str | None = None,
    condition: str = "new",
    years: list[int] | None = None,
    top_n: int = 20,
) -> pd.DataFrame:
    """Top-selling individual models, optionally scoped by category / manufacturer / year."""
    d = _df(df)
    if condition != "all":
        d = d[d["condition"] == condition]
    if category_en:
        d = d[d["category_en"] == category_en]
    if manufacturer_en:
        d = d[d["manufacturer_en"] == manufacturer_en]
    if years:
        d = d[d["year"].isin(years)]
    result = (
        d.groupby(["manufacturer_en", "model_name"])["units"]
        .sum()
        .reset_index()
        .sort_values("units", ascending=False)
        .head(top_n)
    )
    return result.reset_index(drop=True)


# ── Import-type breakdown ──────────────────────────────────────────────────────

def import_type_split(
    df: pd.DataFrame | None = None,
    years: list[int] | None = None,
) -> pd.DataFrame:
    """Commercial vs personal import split per year."""
    d = _df(df)
    if years:
        d = d[d["year"].isin(years)]
    return (
        d.groupby(["year", "import_type"])["units"]
        .sum()
        .unstack("import_type")
        .fillna(0)
        .astype(int)
    )


# ── Year-over-year growth ──────────────────────────────────────────────────────

def yoy_growth(
    df: pd.DataFrame | None = None,
    condition: str = "new",
) -> pd.DataFrame:
    """Year-over-year unit growth (absolute and %) for the total market."""
    totals = total_by_year(df)
    col = condition if condition != "all" else "total"
    s = totals[col] if col in totals.columns else totals["total"]
    growth = pd.DataFrame({
        "units": s,
        "yoy_change": s.diff(),
        "yoy_pct": s.pct_change() * 100,
    })
    return growth.round({"yoy_pct": 1})
