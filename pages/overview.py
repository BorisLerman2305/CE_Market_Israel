"""
עמוד 3 — סקירה כללית של כל סגמנטי שוק הצמ"ה
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.loader import load_annual

ALL_YEARS = list(range(2018, 2027))

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
  div[data-testid="metric-container"] {
    background: white; border: 1px solid #DDE3EC;
    border-radius: 10px; padding: 12px 16px;
  }
  div[data-testid="metric-container"] label { font-size: 13px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="טוען נתונים...")
def load_data() -> pd.DataFrame:
    return load_annual()


df_all = load_data()

# ── One-time year-state init ──────────────────────────────────────────────────
for _y in ALL_YEARS:
    if f"ov_yr_{_y}" not in st.session_state:
        st.session_state[f"ov_yr_{_y}"] = (_y < 2026)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### 📅 בחירת שנים")
    _bc1, _bc2 = st.columns(2)
    if _bc1.button("בחר הכל", key="ov_sel_all", use_container_width=True):
        for _y in ALL_YEARS:
            st.session_state[f"ov_yr_{_y}"] = True
        st.rerun()
    if _bc2.button("נקה הכל", key="ov_clr", use_container_width=True):
        for _y in ALL_YEARS:
            st.session_state[f"ov_yr_{_y}"] = False
        st.rerun()

    selected_years = []
    _cols3 = st.columns(3)
    for i, y in enumerate(ALL_YEARS):
        label = "2026◑" if y == 2026 else str(y)
        if _cols3[i % 3].checkbox(label, key=f"ov_yr_{y}"):
            selected_years.append(y)

    if not selected_years:
        st.warning("בחר לפחות שנה אחת")
        st.stop()

    st.markdown("---")
    st.caption("מקור: מרשם רכב ישראלי | כלים חדשים בלבד")

# ── Filter ────────────────────────────────────────────────────────────────────
df = df_all[
    (df_all["condition"] == "new") &
    (df_all["year"].isin(selected_years)) &
    (~df_all["is_aggregate"])
].copy()

yr_str = f"{min(selected_years)}–{max(selected_years)}"
st.title("🗺️  סקירה כללית — שוק הצמ\"ה")
st.caption(f"כלים חדשים בלבד | {yr_str}")

# ── Pre-compute fixed YoY comparison years ────────────────────────────────────
# Always compare the last two selected years that are ≤ 2025 (avoids comparing
# non-adjacent years or accidentally skipping a year with zero sales).
_yrs_le2025 = sorted(y for y in selected_years if y <= 2025)
_yoy_prev   = _yrs_le2025[-2] if len(_yrs_le2025) >= 2 else None
_yoy_curr   = _yrs_le2025[-1] if len(_yrs_le2025) >= 2 else None
_yoy_col    = f"שינוי {_yoy_prev}→{_yoy_curr}" if _yoy_curr else "שינוי שנתי"

# ── Helpers ───────────────────────────────────────────────────────────────────
def hhi_info(shares: pd.Series) -> tuple[int, str, str]:
    val = int((shares ** 2).sum())
    if val < 1_500:
        return val, "שוק תחרותי", "#27AE60"
    if val < 2_500:
        return val, "ריכוז מתון",  "#F39C12"
    return val,     "שוק מרוכז",  "#E74C3C"


# ── Market-level KPIs ─────────────────────────────────────────────────────────
total_units = int(df["units"].sum())
n_segs      = df["category_en"].nunique()
n_mfrs      = df["manufacturer_en"].nunique()

ann_all = df.groupby("year")["units"].sum()
yoy_lbl, yoy_val = _yoy_col, "—"
if _yoy_curr and _yoy_prev:
    v_c = int(ann_all.get(_yoy_curr, 0))
    v_p = int(ann_all.get(_yoy_prev, 0))
    d   = v_c - v_p
    p   = d / v_p * 100 if v_p else 0
    yoy_val = f"{d:+,} ({p:+.1f}%)"

k1, k2, k3, k4 = st.columns(4)
k1.metric("סה\"כ יחידות בשוק",  f"{total_units:,}")
k2.metric("סגמנטים פעילים",     str(n_segs))
k3.metric("יצרנים פעילים",      str(n_mfrs))
k4.metric(yoy_lbl,              yoy_val)

st.markdown("---")

# ── Per-segment stats ─────────────────────────────────────────────────────────
# Build a consistent category_en → category_he label mapping
_cat_he = {en: (grp["category_he"].iloc[0] or en) for en, grp in df.groupby("category_en")}

records = []
for cat_en, grp in df.groupby("category_en"):
    cat_he  = _cat_he[cat_en]
    total   = int(grp["units"].sum())
    mfr_grp = grp.groupby("manufacturer_en")["units"].sum().sort_values(ascending=False)
    shares  = (mfr_grp / total * 100).round(1)

    leader     = mfr_grp.index[0] if len(mfr_grp) >= 1 else "—"
    lead_share = shares.iloc[0]   if len(shares)  >= 1 else 0
    second     = mfr_grp.index[1] if len(mfr_grp) >= 2 else "—"
    sec_share  = shares.iloc[1]   if len(shares)  >= 2 else 0

    h, h_lbl, h_color = hhi_info(shares)

    # YoY: always compare the same two fixed years for every segment
    # (use 0 if a segment had no registrations in one of those years)
    ann_seg = grp.groupby("year")["units"].sum()
    yoy_pct = None
    if _yoy_curr and _yoy_prev:
        v_c2 = int(ann_seg.get(_yoy_curr, 0))
        v_p2 = int(ann_seg.get(_yoy_prev, 0))
        if v_p2 > 0:
            yoy_pct = round((v_c2 - v_p2) / v_p2 * 100, 1)

    records.append({
        "סגמנט":      cat_he,
        "category_en": cat_en,
        "יחידות":     total,
        "מוביל":      f"{leader} ({lead_share}%)",
        "שני":        f"{second} ({sec_share}%)",
        "HHI":        h,
        "ריכוזיות":   h_lbl,
        "hhi_color":  h_color,
        _yoy_col:     f"{yoy_pct:+.1f}%" if yoy_pct is not None else "—",
        "yoy_pct":    yoy_pct,
    })

stats = pd.DataFrame(records).sort_values("יחידות", ascending=False).reset_index(drop=True)

# ── Row 1: Segment bar chart ──────────────────────────────────────────────────
st.markdown("#### 📊 גודל סגמנטים")

fig_bar = px.bar(
    stats.sort_values("יחידות"), x="יחידות", y="סגמנט",
    orientation="h", text="יחידות",
    color="יחידות", color_continuous_scale=["#AED6F1", "#1B4F91"],
    labels={"יחידות": "יחידות", "סגמנט": ""},
)
fig_bar.update_traces(textposition="outside", textfont_size=10)
fig_bar.update_layout(
    height=max(320, len(stats) * 30),
    showlegend=False, coloraxis_showscale=False,
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=10, l=10, r=70),
    xaxis=dict(showgrid=True, gridcolor="#EEE"),
    yaxis=dict(showgrid=False),
)
st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# ── Row 2: Heatmap (segment × year) ──────────────────────────────────────────
st.markdown("#### 🌡️ מפת חום — יחידות לפי סגמנט ושנה")

# Group by category_en (authoritative key) then rename index to Hebrew labels
# so the heatmap rows always match the bar chart segments 1-for-1.
_sort_yr = max((y for y in df["year"].unique() if y <= 2025), default=max(selected_years))
pivot = (
    df.groupby(["category_en", "year"])["units"].sum()
    .unstack(fill_value=0)
    .sort_values(by=_sort_yr, ascending=False)
)
pivot.index = [_cat_he.get(e, e) for e in pivot.index]

fig_heat = px.imshow(
    pivot,
    labels=dict(x="שנה", y="סגמנט", color="יחידות"),
    color_continuous_scale="Blues",
    aspect="auto",
    text_auto=True,
)
fig_heat.update_traces(textfont_size=10)
fig_heat.update_layout(
    height=max(300, len(pivot) * 30),
    xaxis=dict(dtick=1, tickformat="d"),
    margin=dict(t=20, b=20, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)",
    coloraxis_showscale=False,
)
st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

# ── Row 3: Scatter — size vs growth ──────────────────────────────────────────
scatter_data = stats[stats["yoy_pct"].notna()].copy()
if not scatter_data.empty and _yoy_curr:
    st.markdown(f"#### 🎯 גודל שוק מול {_yoy_col}")
    fig_sc = px.scatter(
        scatter_data,
        x="יחידות", y="yoy_pct",
        size="יחידות", color="ריכוזיות",
        hover_name="סגמנט",
        text="סגמנט",
        labels={"יחידות": "סה\"כ יחידות", "yoy_pct": f"{_yoy_col} (%)"},
        color_discrete_map={
            "שוק תחרותי": "#27AE60",
            "ריכוז מתון":  "#F39C12",
            "שוק מרוכז":  "#E74C3C",
        },
    )
    fig_sc.add_hline(y=0, line_dash="dot", line_color="#AAA", opacity=0.7)
    fig_sc.update_traces(textposition="top center", textfont_size=9)
    fig_sc.update_layout(
        height=460,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#EEE", title="סה\"כ יחידות"),
        yaxis=dict(showgrid=True, gridcolor="#EEE", title=f"{_yoy_col} (%)"),
        legend=dict(title="ריכוזיות", orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
        margin=dict(t=40, b=30, l=0, r=0),
    )
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

# ── Summary table ─────────────────────────────────────────────────────────────
st.markdown("#### 📋 טבלת סגמנטים")
display = stats[["סגמנט", "יחידות", "מוביל", "שני", "HHI", "ריכוזיות", _yoy_col]].copy()
st.dataframe(display, hide_index=True, use_container_width=True)
