import streamlit as st

st.set_page_config(
    page_title="שוק צמ\"ה — ישראל",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation([
    st.Page("_pages/_market.py",     title="שוק הצמ\"ה",    icon="🏗️"),
    st.Page("_pages/_cross_ref.py",  title="קרוס רפרנס",    icon="🔄"),
    st.Page("_pages/_overview.py",   title="סקירה כללית",   icon="🗺️"),
    st.Page("_pages/_specs_page.py", title="מפרטים טכניים", icon="📐"),
])
pg.run()
