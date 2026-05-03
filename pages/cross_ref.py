"""
עמוד 2 — קרוס-רפרנס: השוואת דגמים
"""

import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.loader import load_annual
from src.matcher import ai_match

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; }
  .panel-header {
    font-size: 17px; font-weight: 700; color: #1B4F91;
    border-bottom: 2px solid #1B4F91; padding-bottom: 6px; margin-bottom: 14px;
  }
  .auto-badge {
    background: #EBF5FB; border: 1px solid #AED6F1;
    border-radius: 8px; padding: 10px 14px; margin-top: 8px;
  }
  .auto-model { font-size: 22px; font-weight: 800; color: #E74C3C; }
  .phase-note { font-size: 11px; color: #888; font-style: italic; margin-top: 6px; }
  div[data-testid="metric-container"] {
    background: white; border: 1px solid #DDE3EC;
    border-radius: 10px; padding: 12px 16px;
  }
</style>
""", unsafe_allow_html=True)

ALL_YEARS = list(range(2018, 2027))

# One-time initialization — prevents years from resetting when other params change
for _y in ALL_YEARS:
    _yk = f"xr_yr_{_y}"
    if _yk not in st.session_state:
        st.session_state[_yk] = (_y < 2026)


@st.cache_data(show_spinner="טוען נתונים...")
def load_data() -> pd.DataFrame:
    return load_annual()


df_all = load_data()

# ── Sidebar — year checkboxes ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("#### 📅 בחירת שנים")
    _btn_col1, _btn_col2 = st.columns(2)
    if _btn_col1.button("בחר הכל", key="xr_sel_all", use_container_width=True):
        for _y in ALL_YEARS:
            st.session_state[f"xr_yr_{_y}"] = True
        st.rerun()
    if _btn_col2.button("נקה הכל", key="xr_clr", use_container_width=True):
        for _y in ALL_YEARS:
            st.session_state[f"xr_yr_{_y}"] = False
        st.rerun()

    selected_years = []
    cols3 = st.columns(3)
    for i, y in enumerate(ALL_YEARS):
        label = "2026◑" if y == 2026 else str(y)
        if cols3[i % 3].checkbox(label, key=f"xr_yr_{y}"):
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

# ── Page header ───────────────────────────────────────────────────────────────
yr_str = f"{min(selected_years)}–{max(selected_years)}"
st.title("🔄  קרוס-רפרנס — השוואת דגמים")
st.caption(f"השוואת דגם בסיס מול הדגם המתחרה הקרוב ביותר | {yr_str}")

# ── Segment selector ──────────────────────────────────────────────────────────
seg_info = (
    df.groupby(["category_en", "category_he"])["units"]
    .sum().reset_index()
    .sort_values("units", ascending=False)
    .query("units > 0")
)
seg_labels  = [r.category_he or r.category_en for _, r in seg_info.iterrows()]
seg_en_list = seg_info["category_en"].tolist()

col_seg, _ = st.columns([2, 3])
with col_seg:
    prev = st.session_state.get("_xref_cat_en", "")
    dflt = seg_en_list.index(prev) if prev in seg_en_list else 0
    sel_idx = st.selectbox(
        "בחר סגמנט", range(len(seg_labels)),
        format_func=lambda i: seg_labels[i], index=dflt,
    )
    st.session_state["_xref_cat_en"] = seg_en_list[sel_idx]

sel_cat_en = seg_en_list[sel_idx]
sel_cat_he = seg_info.iloc[sel_idx]["category_he"] or sel_cat_en
seg_df = df[df["category_en"] == sel_cat_en].copy()
st.markdown("---")


# ── Auto-match engine ─────────────────────────────────────────────────────────
def _extract_num(name: str) -> float:
    nums = re.findall(r'\d+(?:\.\d+)?', str(name or ""))
    return float(max(nums, key=float)) if nums else -1.0


def auto_match(
    seg_df, base_mfr, base_model, comp_mfr, category_he: str = ""
) -> tuple[str, str]:
    """
    Phase 2 (AI): ask Claude for the best technical match → fast, cached 24 h.
    Phase 1 (fallback): rank-based + numeric-code proximity.
    """
    comp_series = (
        seg_df[seg_df["manufacturer_en"] == comp_mfr]
        .groupby("model_name")["units"].sum()
        .sort_values(ascending=False)
    )
    if comp_series.empty:
        return None, ""

    comp_models_tuple = tuple(comp_series.index)

    # ── Phase 2: AI matching ──────────────────────────────────────────────────
    ai_model = ai_match(category_he, base_mfr, base_model, comp_mfr, comp_models_tuple)
    if ai_model and ai_model in comp_series.index:
        vol = int(comp_series[ai_model])
        return ai_model, f"{vol:,} יחידות — נבחר ע\"פ מפרטים טכניים (AI) 🤖"

    # ── Phase 1: rank + numeric ───────────────────────────────────────────────
    base_series = (
        seg_df[seg_df["manufacturer_en"] == base_mfr]
        .groupby("model_name")["units"].sum()
        .sort_values(ascending=False)
    )
    base_rank_list = list(base_series.index)
    base_rank = base_rank_list.index(base_model) if base_model in base_rank_list else 0

    rank_idx  = min(base_rank, len(comp_series) - 1)
    candidate = comp_series.index[rank_idx]
    rank_vol  = int(comp_series[candidate])

    base_num = _extract_num(base_model)
    cand_num = _extract_num(candidate)
    if base_num > 0 and cand_num > 0:
        comp_nums = pd.Series({m: _extract_num(m) for m in comp_series.index})
        valid = comp_nums[comp_nums > 0]
        if not valid.empty:
            num_best = (valid - base_num).abs().idxmin()
            num_vol  = int(comp_series[num_best])
            if num_vol >= rank_vol * 0.25:
                return num_best, f"{num_vol:,} יחידות — נבחר לפי קרבת קוד דגם"

    return candidate, f"{rank_vol:,} יחידות — נבחר לפי דירוג מכירות תואם (#{base_rank + 1})"


# ── Two-panel selection ───────────────────────────────────────────────────────
mfrs_in_seg = sorted(seg_df["manufacturer_en"].unique())
col_base, col_vs, col_comp = st.columns([5, 1, 5])

with col_base:
    st.markdown("<div class='panel-header'>🔵 דגם בסיס</div>", unsafe_allow_html=True)
    base_mfr = st.selectbox("יצרן", mfrs_in_seg, key="base_mfr")
    base_models = sorted(
        seg_df[seg_df["manufacturer_en"] == base_mfr]["model_name"].dropna().unique()
    )
    base_model = st.selectbox("דגם", base_models or ["—"], key="base_model")
    if base_models:
        bv = int(seg_df[
            (seg_df["manufacturer_en"] == base_mfr) &
            (seg_df["model_name"] == base_model)
        ]["units"].sum())
        st.caption(f"סה\"כ {bv:,} יחידות בתקופה הנבחרת")

with col_vs:
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;font-size:26px;font-weight:900;"
        "color:#1B4F91;padding-top:30px;'>VS</div>",
        unsafe_allow_html=True,
    )

with col_comp:
    st.markdown("<div class='panel-header'>🔴 דגם מתחרה</div>", unsafe_allow_html=True)
    other_mfrs = sorted(m for m in mfrs_in_seg if m != base_mfr)
    if not other_mfrs:
        st.warning("אין יצרנים נוספים בסגמנט זה")
        st.stop()

    comp_mfr   = st.selectbox("יצרן מתחרה", other_mfrs, key="comp_mfr")
    comp_model, reason = auto_match(seg_df, base_mfr, base_model, comp_mfr, category_he=sel_cat_he)

    if comp_model:
        _ai_active = "AI" in reason
        _phase_note = (
            "🤖 שלב ב׳ פעיל: התאמה על בסיס מפרטים טכניים (Claude AI)"
            if _ai_active else
            "⚙️ שלב ב׳ (בפיתוח): התאמה על בסיס מפרטים טכניים"
        )
        st.markdown(
            f"""<div class='auto-badge'>
              <div style='font-size:12px;color:#555;'>דגם שנבחר אוטומטית</div>
              <div class='auto-model'>{comp_model}</div>
              <div style='font-size:12px;color:#1A5276;margin-top:4px;'>{reason}</div>
              <div class='phase-note'>{_phase_note}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        comp_all = sorted(
            seg_df[seg_df["manufacturer_en"] == comp_mfr]["model_name"].dropna().unique()
        )
        with st.expander("🔧 שינוי ידני"):
            ov_idx    = comp_all.index(comp_model) if comp_model in comp_all else 0
            comp_model = st.selectbox(
                "בחר דגם שונה", comp_all, index=ov_idx,
                key="comp_override", label_visibility="collapsed",
            )
    else:
        st.warning("לא נמצאו דגמים ליצרן זה בסגמנט")
        st.stop()

st.markdown("---")

# ── Yearly series ─────────────────────────────────────────────────────────────
def yearly(mfr, model):
    mask = (seg_df["manufacturer_en"] == mfr) & (seg_df["model_name"] == model)
    return seg_df[mask].groupby("year")["units"].sum().reindex(selected_years, fill_value=0)

s_base = yearly(base_mfr, base_model)
s_comp = yearly(comp_mfr, comp_model)

# ── Comparison bar chart ──────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Bar(
    name=f"{base_mfr}  –  {base_model}",
    x=selected_years, y=s_base.values,
    marker_color="#1B4F91",
    text=s_base.values, textposition="outside",
))
fig.add_trace(go.Bar(
    name=f"{comp_mfr}  –  {comp_model}",
    x=selected_years, y=s_comp.values,
    marker_color="#E74C3C",
    text=s_comp.values, textposition="outside",
))
fig.update_layout(
    barmode="group",
    title=f"השוואה שנתית — {base_model}  vs  {comp_model}",
    xaxis=dict(title="שנה", tickmode="linear", dtick=1, tickformat="d"),
    yaxis=dict(title="יחידות"),
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=60, b=40),
)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#EEE")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Summary stats ─────────────────────────────────────────────────────────────
st.markdown("#### 📊 סיכום נתונים")

def peak_info(s):
    if s.sum() == 0:
        return "—", "—"
    return str(int(s.idxmax())), f"{int(s.max()):,}"

py_b, pv_b = peak_info(s_base)
py_c, pv_c = peak_info(s_comp)

m1, m2, m3, m4 = st.columns(4)
m1.metric("סה\"כ — בסיס",          f"{int(s_base.sum()):,}")
m2.metric("סה\"כ — מתחרה",         f"{int(s_comp.sum()):,}")
m3.metric(f"שנת שיא — {base_model}", f"{py_b} ({pv_b})")
m4.metric(f"שנת שיא — {comp_model}", f"{py_c} ({pv_c})")

st.dataframe(
    pd.DataFrame({
        "מדד": ["סה\"כ יחידות", "שנת שיא", "יחידות בשיא", "שנים פעילות"],
        f"🔵 {base_mfr} — {base_model}": [
            f"{int(s_base.sum()):,}", py_b, pv_b, str(int((s_base > 0).sum())),
        ],
        f"🔴 {comp_mfr} — {comp_model}": [
            f"{int(s_comp.sum()):,}", py_c, pv_c, str(int((s_comp > 0).sum())),
        ],
    }),
    hide_index=True, use_container_width=True,
)

st.caption("💡 למפרטים טכניים מפורטים עבור כל דגם — עברו לעמוד **📐 מפרטים טכניים**")
