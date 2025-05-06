# pages/national_dashboard.py

import streamlit as st
import pandas as pd
from utils.db import engine

# —— Page Configuration —————————————————————————————
st.set_page_config(
    page_title="National Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# —— Sidebar: Season Selector —————————————————————————
with st.sidebar:
    st.title("National Dashboard")
    seasons = ["2022/2023", "2023/2024", "2024/2025"]
    season = st.selectbox("Select Season", seasons)

# —— 1) High-level summary metrics —————————————————————
sql_summary = """
SELECT
  season,
  total_coaches,
  total_parents,
  total_skiers,
  evaluations_completed,
  drills_shared
FROM public.vw_national_summary_by_season
WHERE season = %(season)s;
"""
df_summary = pd.read_sql(sql_summary, engine, params={"season": season})

if df_summary.empty:
    st.warning(f"No summary data found for season {season}.")
    st.stop()

# pull the single row and replace any nulls with 0
row = df_summary.iloc[0].fillna(0)

# —— Display as Metrics —————————————————————————————
col1, col2, col3, col4, col5 = st.columns(5, gap="small")
col1.metric("Coaches",               f"{int(row.total_coaches):,}")
col2.metric("Parents",               f"{int(row.total_parents):,}")
col3.metric("Skiers",                f"{int(row.total_skiers):,}")
col4.metric("Evaluations Completed", f"{int(row.evaluations_completed):,}")
col5.metric("Drills Shared",         f"{int(row.drills_shared):,}")

# (Later: add your pie/bar charts and club table below)
