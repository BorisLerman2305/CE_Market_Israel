"""
עמוד 4 — מפרטים טכניים
"""

import streamlit as st
import pandas as pd
from src.loader import load_annual
from src.specs_web import get_web_specs, get_manufacturer_url, build_search_links

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; }
  .spec-card {
    background: white; border: 1px solid #DDE3EC;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 18px;
  }
  .spec-title {
    font-size: 20px; font-weight: 800; color: #1B4F91;
    border-bottom: 2px solid #1B4F91; padding-bottom: 8px; margin-bottom: 14px;
  }
  .spec-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 7px 0; border-bottom: 1px solid #F0F4F8; font-size: 14px;
  }
  .spec-row:last-child { border-bottom: none; }
  .spec-label { color: #444; font-weight: 500; }
  .spec-value { font-weight: 700; color: #1B4F91; }
  .link-box {
    background: #EBF5FB; border: 1px solid #AED6F1;
    border-radius: 8px; padding: 12px 16px; margin-top: 14px;
  }
  .not-found-box {
    background: #FEF9E7; border: 1px solid #F9E79F;
    border-radius: 8px; padding: 14px 18px;
  }
  .panel-header {
    font-size: 16px; font-weight: 700; color: #1B4F91;
    border-bottom: 2px solid #1B4F91; padding-bottom: 5px; margin-bottom: 12px;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="טוען נתונים...")
def load_data() -> pd.DataFrame:
    return load_annual()


df_all = load_data()
df = df_all[
    (df_all["condition"] == "new") &
    (~df_all["is_aggregate"])
].copy()

st.title("📐  מפרטים טכניים")
st.caption("מפרטי דגמים לפי קטגוריה, יצרן ומודל | מבוסס על מסד נתונים מקומי + אתרי יצרנים")

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
    sel_idx = st.selectbox(
        "סגמנט", range(len(seg_labels)),
        format_func=lambda i: seg_labels[i],
    )
sel_cat_en = seg_en_list[sel_idx]
seg_df = df[df["category_en"] == sel_cat_en]

# ── Mode ──────────────────────────────────────────────────────────────────────
mode = st.radio(
    "מצב", ["דגם יחיד 🔵", "השוואה בין שני דגמים ⚔️"],
    horizontal=True, label_visibility="collapsed",
)
st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _model_panel(prefix: str, color: str, label: str,
                 exclude_mfr: str | None = None):
    """Return (mfr, model, models_list) for one selection panel."""
    st.markdown(
        f"<div class='panel-header'>{color} {label}</div>",
        unsafe_allow_html=True,
    )
    mfrs = sorted(seg_df["manufacturer_en"].unique())
    if exclude_mfr:
        mfrs = [m for m in mfrs if m != exclude_mfr]
    mfr = st.selectbox("יצרן", mfrs, key=f"{prefix}_mfr")
    models = sorted(
        seg_df[seg_df["manufacturer_en"] == mfr]["model_name"].dropna().unique()
    )
    model = st.selectbox("דגם", models or ["—"], key=f"{prefix}_model")
    return mfr, model, models


def _render_spec_card(mfr: str, model: str, specs: dict | None):
    """Render a spec card with URL link + external search links."""
    url = specs.pop("_url", None) if specs else None
    mfr_url = url or get_manufacturer_url(mfr)
    ext_links = build_search_links(mfr, model)

    # ── Spec rows HTML ────────────────────────────────────────────────────────
    if specs:
        rows_html = "".join(
            f"<div class='spec-row'>"
            f"<span class='spec-label'>{k}</span>"
            f"<span class='spec-value'>{v}</span>"
            f"</div>"
            for k, v in specs.items()
            if v not in (None, "—", "")
        )
        card_body = rows_html
    else:
        card_body = (
            "<div class='not-found-box'>"
            "⚠️ דגם זה אינו במסד הנתונים המקומי שלנו עדיין.<br>"
            "השתמש בקישורי החיפוש להלן למציאת המפרטים הרשמיים."
            "</div>"
        )

    # ── Manufacturer link ─────────────────────────────────────────────────────
    url_html = (
        f"<div class='link-box'>🌍 <strong>אתר היצרן:</strong> "
        f"<a href='{mfr_url}' target='_blank'>{mfr_url}</a></div>"
        if mfr_url else ""
    )

    st.markdown(
        f"<div class='spec-card'>"
        f"<div class='spec-title'>{mfr} — {model}</div>"
        f"{card_body}"
        f"{url_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── External search links ─────────────────────────────────────────────────
    st.markdown("**🔗 חיפוש מפרטים מורחב:**")
    ext_cols = st.columns(len(ext_links))
    for col, (lbl, href) in zip(ext_cols, ext_links.items()):
        col.link_button(lbl, href, use_container_width=True)


# ── Single model ──────────────────────────────────────────────────────────────
if "יחיד" in mode:
    mfr, model, models = _model_panel("sp1", "🔵", "בחר דגם")

    if models and model != "—":
        with st.spinner("מחפש מפרטים..."):
            specs = get_web_specs(mfr, model, sel_cat_en)
        _render_spec_card(mfr, model, specs)
        if specs:
            st.caption("מקור: מסד נתונים מקומי | יש לאמת מול מפרט יצרן רשמי")

# ── Comparison ────────────────────────────────────────────────────────────────
else:
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        mfr_a, model_a, models_a = _model_panel("sp_a", "🔵", "דגם א׳")
    with col_vs:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;font-size:22px;font-weight:900;"
            "color:#1B4F91;padding-top:20px;'>VS</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        if len(seg_df["manufacturer_en"].unique()) < 2:
            st.warning("אין יצרן שני בסגמנט זה")
            st.stop()
        mfr_b, model_b, models_b = _model_panel("sp_b", "🔴", "דגם ב׳",
                                                  exclude_mfr=mfr_a)

    if (models_a and model_a != "—") and (models_b and model_b != "—"):
        st.markdown("---")
        with st.spinner("מחפש מפרטים..."):
            specs_a = get_web_specs(mfr_a, model_a, sel_cat_en)
            specs_b = get_web_specs(mfr_b, model_b, sel_cat_en)

        col_ca, col_cb = st.columns(2)
        with col_ca:
            _render_spec_card(mfr_a, model_a, specs_a)
        with col_cb:
            _render_spec_card(mfr_b, model_b, specs_b)

        # ── Side-by-side table (only when both have specs) ────────────────────
        if specs_a and specs_b:
            st.markdown("#### 📊 השוואת מפרטים")
            all_keys = list(dict.fromkeys(
                [k for k in specs_a if not k.startswith("_")] +
                [k for k in specs_b if not k.startswith("_")]
            ))
            cmp_df = pd.DataFrame({
                "מפרט": all_keys,
                f"🔵 {mfr_a} — {model_a}": [specs_a.get(k, "—") for k in all_keys],
                f"🔴 {mfr_b} — {model_b}": [specs_b.get(k, "—") for k in all_keys],
            })
            st.dataframe(cmp_df, hide_index=True, use_container_width=True)
            st.caption("מקור: מסד נתונים מקומי | יש לאמת מול מפרט יצרן רשמי")
