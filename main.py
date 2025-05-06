import streamlit as st
from utils.auth import get_current_user

PAGES = {
    "national": "pages.national_dashboard",
    "ptso":     "pages.ptso_dashboard",
    "club":     "pages.club_dashboard",   # ← make sure this line exists
}

def main():
    st.set_page_config(layout="wide")
    user = get_current_user()
    if not user:
        st.error("Please log in.")
        return

    role = user["role"]
    if role == "aca":
        module = PAGES["national"]
    elif role == "ptso":
        module = PAGES["ptso"]
    elif role == "club_admin":
        module = PAGES["club"]
    else:
        st.error("Unauthorized role.")
        return

    page = __import__(module, fromlist=["app"])
    page.app()

if __name__ == "__main__":
    main()
