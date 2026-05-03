"""
עמוד 4 — מפרטים טכניים
"""

import streamlit as st
import pandas as pd
from src.loader import load_annual
from src.specs import get_specs

st.markdown("""
<style>
  .block-container { padding-top: 1.2rem; }
  .spec-card {
    background: white; border: 1px solid #DDE3EC;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
  }
  .spec-title {
    font-size: 22px; font-weight: 800; color: #1B4F91;
    border-bottom: 2px solid #1B4F91; padding-bottom: 8px; margin-bottom: 16px;
  }
  .spec-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid #F0F4F8; font-size: 15px;
  }
  .spec-row:last-child { border-bottom: none; }
  .spec-label { color: #444; font-weight: 500; }
  .spec-value { font-weight: 700; color: #1B4F91; font-size: 16px; }
  .url-box {
    background: #EBF5FB; border: 1px solid #AED6F1;
    border-radius: 8px; padding: 12px 16px; margin-top: 16px;
  }
  .compare-header {
    font-size: 17px; font-weight: 700; color: #1B4F91;
    border-bottom: 2px solid #1B4F91; padding-bottom: 6px; margin-bottom: 14px;
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
st.caption("מפרטי דגמים לפי קטגוריה, יצרן ומודל | מקור: AI — יש לאמת מול מפרט רשמי")

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

# ── Mode toggle ───────────────────────────────────────────────────────────────
mode = st.radio(
    "מצב",
    ["דגם יחיד", "השוואה בין שני דגמים"],
    horizontal=True,
    label_visibility="collapsed",
)
st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────
def model_selector(prefix: str, label_color: str, label_text: str):
    """Returns (mfr, model) for one panel."""
    st.markdown(
        f"<div class='compare-header'>{label_color} {label_text}</div>",
        unsafe_allow_html=True,
    )
    mfrs = sorted(seg_df["manufacturer_en"].unique())
    mfr = st.selectbox("יצרן", mfrs, key=f"{prefix}_mfr")
    models = sorted(
        seg_df[seg_df["manufacturer_en"] == mfr]["model_name"].dropna().unique()
    )
    model = st.selectbox("דגם", models or ["—"], key=f"{prefix}_model")
    return mfr, model, models


def render_spec_card(mfr: str, model: str, specs: dict | None):
    """Render a styled card for one machine's specs."""
    if specs is None:
        st.warning(f"מפרטים לא זמינים עבור {mfr} {model}")
        return

    url = specs.pop("_url", None)
    display_specs = {k: v for k, v in specs.items() if v not in (None, "—", "")}

    rows_html = "".join(
        f"<div class='spec-row'>"
        f"<span class='spec-label'>{k}</span>"
        f"<span class='spec-value'>{v}</span>"
        f"</div>"
        for k, v in display_specs.items()
    )
    url_html = (
        f"<div class='url-box'>🔗 <strong>אתר היצרן:</strong> "
        f"<a href='{url}' target='_blank'>{url}</a></div>"
        if url else ""
    )

    st.markdown(
        f"<div class='spec-card'>"
        f"<div class='spec-title'>{mfr} — {model}</div>"
        f"{rows_html}"
        f"{url_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Single model mode ─────────────────────────────────────────────────────────
if mode == "דגם יחיד":
    mfr, model, models = model_selector("sp1", "🔵", "בחר דגם")

    if models and model != "—":
        with st.spinner("שולח שאילתה למסד הנתונים..."):
            specs = get_specs(sel_cat_en, mfr, model)

        if specs is None:
            st.error("מפרטים טכניים לא זמינים.")
            st.info(
                "כדי להפעיל את המפרטים הטכניים, הוסף מפתח **ANTHROPIC_API_KEY** ב:\n\n"
                "- **Railway:** Settings → Variables\n"
                "- **מקומי:** `.streamlit/secrets.toml`"
            )
        else:
            render_spec_card(mfr, model, specs)
            st.caption("מקור: נתוני יצרן | נאסף ע\"י Claude AI — יש לאמת מול מפרט רשמי")

# ── Comparison mode ───────────────────────────────────────────────────────────
else:
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        mfr_a, model_a, models_a = model_selector("sp_a", "🔵", "דגם א׳")

    with col_vs:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='text-align:center;font-size:22px;font-weight:900;"
            "color:#1B4F91;padding-top:20px;'>VS</div>",
            unsafe_allow_html=True,
        )

    with col_b:
        other_mfrs_df = seg_df[seg_df["manufacturer_en"] != mfr_a]
        if other_mfrs_df.empty:
            st.warning("אין יצרנים נוספים בסגמנט זה")
            st.stop()
        mfr_b, model_b, models_b = model_selector("sp_b", "🔴", "דגם ב׳")

    if (models_a and model_a != "—") and (models_b and model_b != "—"):
        st.markdown("---")
        with st.spinner("שולח שאילתות..."):
            specs_a = get_specs(sel_cat_en, mfr_a, model_a)
            specs_b = get_specs(sel_cat_en, mfr_b, model_b)

        if specs_a is None and specs_b is None:
            st.error("מפרטים טכניים לא זמינים.")
            st.info(
                "כדי להפעיל את המפרטים הטכניים, הוסף מפתח **ANTHROPIC_API_KEY** ב:\n\n"
                "- **Railway:** Settings → Variables\n"
                "- **מקומי:** `.streamlit/secrets.toml`"
            )
        else:
            col_card_a, col_card_b = st.columns(2)
            with col_card_a:
                render_spec_card(mfr_a, model_a, specs_a)
            with col_card_b:
                render_spec_card(mfr_b, model_b, specs_b)

            # ── Side-by-side comparison table ─────────────────────────────────
            if specs_a is not None and specs_b is not None:
                st.markdown("#### 📊 השוואת מפרטים")
                # specs_a and specs_b already had _url popped in render_spec_card
                all_keys = list(dict.fromkeys(
                    list(specs_a.keys()) + list(specs_b.keys())
                ))
                cmp_df = pd.DataFrame({
                    "מפרט": all_keys,
                    f"🔵 {mfr_a} — {model_a}": [specs_a.get(k, "—") for k in all_keys],
                    f"🔴 {mfr_b} — {model_b}": [specs_b.get(k, "—") for k in all_keys],
                })
                st.dataframe(cmp_df, hide_index=True, use_container_width=True)

            st.caption("מקור: נתוני יצרן | נאסף ע\"י Claude AI — יש לאמת מול מפרט רשמי")
