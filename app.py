import streamlit as st

st.set_page_config(
    page_title="שוק צמ\"ה — ישראל",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("pages/market.py",     title="שוק הצמ\"ה",     icon="🏗️", url_path="market"),
    st.Page("pages/cross_ref.py",  title="קרוס רפרנס",     icon="🔄", url_path="cross-ref"),
    st.Page("pages/overview.py",   title="סקירה כללית",    icon="🗺️", url_path="overview"),
    st.Page("pages/specs_page.py", title="מפרטים טכניים",  icon="📐", url_path="specs"),
])
pg.run()
