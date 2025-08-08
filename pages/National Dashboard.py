import streamlit as st
import pandas as pd
import base64
from utils.db import engine
from st_aggrid import AgGrid, GridOptionsBuilder
import pyecharts.options as opts
from pyecharts.charts import Pie, Bar
from streamlit.components.v1 import html

from utils.sidebar import render_nav

st.set_page_config(
    page_title="National Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_nav()

# ─── GLOBAL CSS ─────────────────────────────────────────────
st.markdown(
    """
    <style>
      /* give the page enough width so fixed-width charts fit on Cloud */
      .block-container {
        max-width: 1400px;
        padding-left: 0 !important;
        padding-right: 0 !important;
      }
      /* header banner */
      .header-banner {
        display: flex; align-items: center; gap: 1rem;
        background-color: #d32f2f; color: white;
        padding: 1rem 2rem; border-radius: 8px; margin-bottom: 2rem;
      }
      /* stat cards */
      .stats-row { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
      .stat-card {
        flex: 1; background-color: #393939;
        padding: 1rem !important; border-radius: 6px; text-align: center;
      }
      .stat-card p {
        margin: 0; font-size: 0.9rem !important; color: #bbbbbb;
        text-transform: uppercase; letter-spacing: 0.04em;
      }
      .stat-card h2 {
        margin: 0.3rem 0 0; font-size: 1.8rem !important;
        color: #fafafa; font-weight: bold;
      }
      /* shrink Streamlit metrics if used */
      div[data-testid="stMetricValue"] { font-size: 1rem !important; }
      div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
      /* tighter AgGrid */
      .ag-theme-streamlit .ag-cell,
      .ag-theme-streamlit .ag-header-cell-label {
        font-size: 12px !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── SIDEBAR FILTERS ────────────────────────────────────────
target_season = "2024/2025"

# Fetch PTSO & Club options
tsql_ptso = """
SELECT DISTINCT ptso
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY ptso;
"""
ptso_df = pd.read_sql(tsql_ptso, engine, params={"season": target_season})
ptso_options = ptso_df["ptso"].dropna().tolist()

status_choices = ["Active", "Inactive"]

nsql_clubs = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(nsql_clubs, engine, params={"season": target_season})
name_options = names_df["club_name"].tolist()

# Basic filters
season        = st.sidebar.selectbox("Season", [target_season])
ptso_choice   = st.sidebar.multiselect("PTSO",   ["All"] + ptso_options, default=["All"])
status_choice = st.sidebar.multiselect("Status", ["All"] + status_choices, default=["All"])
club_choice   = st.sidebar.multiselect("Club",   ["All"] + name_options,   default=["All"])

# Resolve "All"
ptso_sel   = ptso_options   if "All" in ptso_choice   else ptso_choice
status_sel = status_choices if "All" in status_choice else status_choice
club_sel   = name_options   if "All" in club_choice   else club_choice

# Fetch full distribution for chart + level options
sql_dist_full = """
SELECT level_id, level_name, SUM(skier_count) AS skier_count
FROM public.vw_skier_level_distribution_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_dist_full = pd.read_sql(
    sql_dist_full,
    engine,
    params={"season": season, "ptso": ptso_sel, "names": club_sel}
)

# Levels multiselect for charts
level_list      = df_dist_full["level_name"].unique().tolist()
selected_levels = st.sidebar.multiselect("Levels (chart)", level_list, default=level_list)

# Text‐search filter for table
search_name = st.sidebar.text_input("🔍 Search Club Name", "")

# Load full clubs for table filtering
sql_clubs_full = """
SELECT club_id, club_name, sr_id, primary_contact, primary_contact_email,
       skiers, coaches, ptso, status
FROM public.vw_club_summary_by_season
WHERE season = %(season)s;
"""
df_clubs_full = pd.read_sql(sql_clubs_full, engine, params={"season": season})

# ─── BANNER ─────────────────────────────────────────────────
logo_path = "Alpine_Canada_logo.svg.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(f"""
<div class="header-banner">
  <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
  <h1 style="margin:0;font-size:3rem;">National Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ─── 1) Summary metrics ────────────────────────────────────
sql_sum = """
SELECT
  SUM(coaches)               AS total_coaches,
  SUM(parents)               AS total_parents,
  SUM(skiers)                AS total_skiers,
  SUM(evaluations_completed) AS total_evaluations,
  SUM(drills_shared)         AS total_drills
FROM public.vw_national_summary_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND status    = ANY(%(status)s)
  AND club_name = ANY(%(names)s);
"""
df_sum = pd.read_sql(
    sql_sum,
    engine,
    params={
        "season": season,
        "ptso":   ptso_sel,
        "status": status_sel,
        "names":  club_sel
    }
)
if df_sum.empty:
    st.warning(f"No data for season {season} with those filters.")
    st.stop()

row = df_sum.iloc[0]
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Coaches</p><h2>{int(row.total_coaches):,}</h2></div>
  <div class="stat-card"><p>Parents</p><h2>{int(row.total_parents):,}</h2></div>
  <div class="stat-card"><p>Skiers</p><h2>{int(row.total_skiers):,}</h2></div>
  <div class="stat-card"><p>Evaluations</p><h2>{int(row.total_evaluations):,}</h2></div>
  <div class="stat-card"><p>Drills Shared</p><h2>{int(row.total_drills):,}</h2></div>
</div>
""", unsafe_allow_html=True)

# ─── 2) Distribution & eval data ───────────────────────────
df_dist = df_dist_full[df_dist_full["level_name"].isin(selected_levels)]

sql_eval_full = """
SELECT level_id, level_name, SUM(eval_passed) AS eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name;
"""
df_eval_full = pd.read_sql(
    sql_eval_full,
    engine,
    params={"season": season, "ptso": ptso_sel, "names": club_sel}
)

raw_ids   = [1,34,35,36,37,38,67,68]
order_map = {rid: i for i, rid in enumerate(raw_ids)}
label_map = {rid: f"Level {idx+1}" for idx, rid in enumerate(raw_ids)}

df_eval = df_eval_full.copy()
df_eval["sort_ord"]      = df_eval["level_id"].map(order_map)
df_eval["display_level"] = df_eval["level_id"].map(label_map)
df_eval = (
    df_eval[df_eval["sort_ord"].notna() & df_eval["display_level"].isin(selected_levels)]
    .sort_values("sort_ord")
)

# ─── 3) Charts (fixed pixel width so Cloud won’t squish) ───
st.subheader("Skier Level Distribution")
if df_dist.empty:
    st.info("No level distribution data.")
else:
    pie = (
        Pie(
            init_opts=opts.InitOpts(
                width="1200px",   # ← fixed pixel width
                height="420px",
                bg_color="#111111"
            )
        )
        .add(
            "",
            df_dist[["level_name", "skier_count"]].values.tolist(),
            radius=["40%", "70%"]
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                orient="horizontal", pos_top="2%",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {}, "restore": {}, "dataZoom": {},
                "dataView": {}, "magicType": {}
            })
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
    )
    html(pie.render_embed(), height=440, scrolling=False)

st.subheader("Evaluations by Level")
if df_eval.empty:
    st.info("No evaluations data.")
else:
    bar = (
        Bar(
            init_opts=opts.InitOpts(
                width="1200px",   # ← fixed pixel width
                height="420px",
                bg_color="#111111"
            )
        )
        .add_xaxis(df_eval["display_level"].tolist())
        .add_yaxis("Evaluations", df_eval["eval_count"].tolist(), category_gap="35%")
        .set_global_opts(
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {}, "restore": {}, "dataZoom": {},
                "dataView": {}, "magicType": {}
            })
        )
    )
    html(bar.render_embed(), height=440, scrolling=False)

# ─── Clubs list as interactive AG Grid + CSV download ───
sql_clubs = """
SELECT club_id, club_name, sr_id, primary_contact, primary_contact_email, skiers, coaches, ptso, status
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
_df_clubs = pd.read_sql(sql_clubs, engine, params={"season": season})

# apply sidebar filters + text search
mask = pd.Series(True, index=_df_clubs.index)
mask &= _df_clubs["ptso"].isin(ptso_sel)
mask &= _df_clubs["status"].isin(status_sel)
mask &= _df_clubs["club_name"].isin(club_sel)
if search_name:
    mask &= _df_clubs["club_name"].str.contains(search_name, case=False)
_df_clubs = _df_clubs[mask]

st.subheader("Clubs")
if _df_clubs.empty:
    st.info("No clubs data for this season.")
else:
    df_display = (_df_clubs.rename(columns={
        "club_id": "ID",
        "club_name": "Name",
        "sr_id": "SR ID",
        "primary_contact": "Contact",
        "primary_contact_email": "Email",
        "skiers": "Skiers",
        "coaches": "Coaches",
        "ptso": "PTSO",
        "status": "Status",
    }).set_index("ID"))

    btn_col, _ = st.columns([1,8])
    with btn_col:
        csv = df_display.reset_index().to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"clubs_{season.replace('/','-')}.csv",
            mime="text/csv",
            use_container_width=False
        )

    st.markdown("""
    <style>
      .ag-root-wrapper, .ag-theme-streamlit {
        width: 100% !important;
      }
    </style>
    """, unsafe_allow_html=True)

    # Move AgGrid config inside the block so it only runs when data exists
    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)
    gb.configure_grid_options(domLayout="autoHeight")
    grid_options = gb.build()

    AgGrid(
        df_display,
        gridOptions=grid_options,
        theme="streamlit",
        fit_columns_on_grid_load=True  # autoHeight will size it
    )
