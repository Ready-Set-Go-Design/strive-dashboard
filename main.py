import streamlit as st

# ─── Global page config ──────────────────────────────────
st.set_page_config(
    page_title="Strive Dashboard",
    page_icon="🏔️",
    layout="wide"
)

# ─── Constrain max width ─────────────────────────────────
st.markdown(
    """
    <style>
      .reportview-container .main .block-container {
        max-width: 1440px;
        margin: auto;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Sidebar Branding ────────────────────────────────────
st.sidebar.image(
    r"C:\Users\Owner\Desktop\strive\strive-dashboard\rsg_logo.jpg",
    use_container_width=True
)
st.sidebar.markdown("## Welcome to Strive Dashboard")

# ─── Manual page links ───────────────────────────────────
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

# ─── Main content ────────────────────────────────────────
st.title("🏔️ Strive Dashboard")
st.write(
    """
    Use the **Navigate** links in the sidebar to switch between dashboards.
    """
)