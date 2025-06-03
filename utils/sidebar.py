# utils/sidebar.py
import streamlit as st

def render_nav():
    st.sidebar.image(
        "Alpine_Canada_logo.svg.png",   # ← updated to your SVG file
        use_container_width=True
    )
    st.sidebar.markdown("## Welcome to Strive Dashboard")
    st.sidebar.markdown("**Navigate:**")

    st.sidebar.page_link(
        "pages/National Dashboard.py",
        label="National Dashboard",
        icon="🏠"
    )
    st.sidebar.page_link(
        "pages/PTSO Dashboard.py",
        label="PTSO Dashboard",
        icon="📊"
    )
    st.sidebar.page_link(
        "pages/Club Dashboard.py",
        label="Club Dashboard",
        icon="⛷️"
    )