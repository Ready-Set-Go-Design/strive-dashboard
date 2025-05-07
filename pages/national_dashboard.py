# pages/national_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
from utils.db import engine
import pyecharts.options as opts
from pyecharts.charts import Pie, Bar

from streamlit.components.v1 import html   # built‑in

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="National Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS for banner & metric cards ─────────────────────────
st.markdown("""
<style>
/* Top banner */
.header-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: #d32f2f;
  color: white;
  padding: 1rem 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}
/* Metric cards */
.stats-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}
.stat-card {
  flex: 1;
  background-color: #393939;
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
}
.stat-card p {
  margin: 0;
  font-size: 1.1rem;
  color: #bbbbbb;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stat-card h2 {
  margin: 0.5rem 0 0;
  font-size: 2.5rem;
  font-weight: bold;
  color: #fafafa;
}
</style>
""", unsafe_allow_html=True)

# ─── Banner with logo + title ──────────────────────────────
logo_path = "Alpine_Canada_logo.svg.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(f"""
<div class="header-banner">
  <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
  <h1 style="margin:0;font-size:3rem;">National Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar filters ───────────────────────────────────────
st.sidebar.markdown("## Filters")
seasons = ["2022/2023", "2023/2024", "2024/2025"]
season = st.sidebar.selectbox("Select Season", seasons)

# ─── 1) Summary metrics ────────────────────────────────────
sql_sum = """
SELECT
  total_coaches,
  total_parents,
  total_skiers,
  evaluations_completed,
  drills_shared
FROM public.vw_national_summary_by_season
WHERE season = %(season)s;
"""
df_sum = pd.read_sql(sql_sum, engine, params={"season": season})
if df_sum.empty:
    st.warning(f"No data found for season {season}.")
    st.stop()

row = df_sum.iloc[0]
coaches     = int(row.total_coaches or 0)
parents     = int(row.total_parents or 0)
skiers      = int(row.total_skiers  or 0)
evaluations = int(row.evaluations_completed or 0)
drills      = int(row.drills_shared or 0)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Coaches</p><h2>{coaches:,}</h2></div>
  <div class="stat-card"><p>Parents</p><h2>{parents:,}</h2></div>
  <div class="stat-card"><p>Skiers</p><h2>{skiers:,}</h2></div>
  <div class="stat-card"><p>Evaluations Completed</p><h2>{evaluations:,}</h2></div>
  <div class="stat-card"><p>Drills Shared</p><h2>{drills:,}</h2></div>
</div>
""", unsafe_allow_html=True)

# First, query both data sets
sql_dist = """
SELECT level_name, skier_count
FROM public.vw_skier_level_distribution_by_season
WHERE season = %(season)s
ORDER BY level_id;
"""
df_dist = pd.read_sql(sql_dist, engine, params={"season": season})

sql_eval = """
SELECT level_name, eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season = %(season)s
ORDER BY level_id;
"""
df_eval = pd.read_sql(sql_eval, engine, params={"season": season})

# Create two columns
col_pie, col_bar = st.columns(2, gap="large")

# ─── Pie in left column ───────────────────────────────────
with col_pie:
    st.subheader("Skier Level Distribution")
    if df_dist.empty:
        st.info("No level-distribution data for this season.")
    else:
        data_pairs = df_dist.values.tolist()
        pie = (
            Pie(init_opts=opts.InitOpts(bg_color="#111111"))
            .add("", data_pairs, radius=["40%", "70%"])
            .set_global_opts(
                legend_opts=opts.LegendOpts(
                    orient="vertical",
                    pos_left="left",
                    textstyle_opts=opts.TextStyleOpts(color="#ffffff")
                ),
                title_opts=opts.TitleOpts(title="")
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff")
            )
        )
        html(pie.render_embed(), height=450, width=None, scrolling=False)

# ─── Bar in right column ──────────────────────────────────
with col_bar:
    st.subheader("Evaluations by Levels")
    if df_eval.empty:
        st.info("No evaluations data for this season.")
    else:
        bar = (
            Bar(init_opts=opts.InitOpts(bg_color="#111111"))
            .add_xaxis(df_eval["level_name"].tolist())
            .add_yaxis(
                series_name="Evaluations",
                y_axis=df_eval["eval_count"].tolist(),
                category_gap="35%",
                color="#CD5C5C"
            )
            .set_global_opts(
                yaxis_opts=opts.AxisOpts(
                    name="Count",
                    axislabel_opts=opts.LabelOpts(color="#ffffff")
                ),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(color="#ffffff")
                ),
                legend_opts=opts.LegendOpts(
                    textstyle_opts=opts.TextStyleOpts(color="#ffffff")
                ),
                toolbox_opts=opts.ToolboxOpts(
                    orient="horizontal",
                    item_size=18,
                    item_gap=8,
                    feature={
                        "saveAsImage": {"title": "save as image"},
                        "restore":     {"title": "restore"},
                        "dataZoom":    {"title": {"zoom": "zoom", "back": "reset zoom"}},
                        "dataView":    {"title": "data view", "lang": ["data view", "turn off", "refresh"]},
                        "magicType":   {"type": ["line", "bar"], "title": {"line": "line chart", "bar": "bar chart"}}
                    }
                ),
                title_opts=opts.TitleOpts(title="")
            )
        )
        html(bar.render_embed(), height=500, width=None, scrolling=False)