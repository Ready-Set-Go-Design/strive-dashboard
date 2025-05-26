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

# ─── Sidebar Branding & Page Links ───────────────────────
# Logo at very top of sidebar
st.sidebar.image(
    r"C:\Users\Owner\Desktop\strive\strive-dashboard\rsg_logo.jpg",
    use_container_width=True
)
# Optional welcome text
st.sidebar.markdown("## Welcome to Strive Dashboard")

# Move the “Pages” list into the sidebar below the logo
st.sidebar.markdown(
    """
    **Navigate:**  
    - National Dashboard  
    - PTSO Dashboard  
    - Club Dashboard  
    """
)

# ─── Welcome Message ────────────────────────────────────
st.title("🏔️ Strive Dashboard")
st.write(
    """
    Use the **Pages** menu in the top-left corner to switch between dashboards,
    or click the links in the sidebar above.
    """
)
