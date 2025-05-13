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
      /* Max-width for the main block container */
      .reportview-container .main .block-container {
        max-width: 1440px;
        margin: auto;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Sidebar Branding ───────────────────────────────────
st.sidebar.image("Alpine_Canada_logo.svg.png", use_container_width=True)
st.sidebar.markdown("## Welcome to Strive Dashboard")

# ─── Welcome Message ────────────────────────────────────
st.title("🏔️ Strive Dashboard")
st.write(
    """
    Use the **Pages** menu in the top-left corner to navigate:
    - National Dashboard  
    - PTSO Dashboard  
    - Club Dashboard  
    """
)
