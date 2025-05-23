import streamlit as st
import pandas as pd
import base64
from utils.db import engine
from st_aggrid import AgGrid, GridOptionsBuilder  # for the interactive table
import pyecharts.options as opts
from pyecharts.charts import Pie, Bar
from streamlit.components.v1 import html  # built-in

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="National Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Widen canvas & remove zoom ────────────────────────────
st.markdown(
    """
    <style>
      /* allow full-width canvas */
      .reportview-container .main .block-container {
        max-width: 100% !important;
        padding: 1rem 2rem;
      }
      /* reset zoom */
      html, body, .reportview-container .main .block-container {
        zoom: 0.80 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── CSS for banner & metric cards ─────────────────────────
st.markdown("""<style>
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
</style>""", unsafe_allow_html=True)

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

# ─── Filter popover (replaces sidebar filters) ───────────────────────────
target_season = "2024/2025"

# Fetch PTSO options
tsql_ptso = """
SELECT DISTINCT ptso
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY ptso;
"""
ptso_df = pd.read_sql(tsql_ptso, engine, params={"season": target_season})
ptso_options = ptso_df["ptso"].dropna().tolist()

# Status options
status_choices = ["Active", "Inactive"]

# Fetch Club Name options
nsql = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(nsql, engine, params={"season": target_season})
name_options = names_df["club_name"].tolist()

with st.popover("Filters", icon=":material/filter_list:"):
    season = st.selectbox("Select Season", [target_season])
    ptso_choice = st.selectbox("Filter by PTSO", ["All"] + ptso_options)
    status_choice = st.selectbox("Filter by Status", ["All"] + status_choices)
    name_choice = st.selectbox("Filter by Club Name", ["All"] + name_options)

# Derive selections for SQL parameters
selected_ptso = ptso_options if ptso_choice == "All" else [ptso_choice]
selected_status = status_choices if status_choice == "All" else [status_choice]
selected_name = name_options if name_choice == "All" else [name_choice]

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
        "ptso": selected_ptso,
        "status": selected_status,
        "names": selected_name
    }
)
if df_sum.empty:
    st.warning(f"No data found for season {season} with the selected filters.")
    st.stop()

row = df_sum.iloc[0]
coaches     = int(row.total_coaches     or 0)
parents     = int(row.total_parents     or 0)
skiers      = int(row.total_skiers      or 0)
evaluations = int(row.total_evaluations or 0)
drills      = int(row.total_drills      or 0)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Coaches</p><h2>{coaches:,}</h2></div>
  <div class="stat-card"><p>Parents</p><h2>{parents:,}</h2></div>
  <div class="stat-card"><p>Skiers</p><h2>{skiers:,}</h2></div>
  <div class="stat-card"><p>Evaluations Completed</p><h2>{evaluations:,}</h2></div>
  <div class="stat-card"><p>Drills Shared</p><h2>{drills:,}</h2></div>
</div>
""", unsafe_allow_html=True)

# ─── 2 & 3) Charts side by side ────────────────────────────
sql_dist = """
SELECT
  level_name,
  SUM(skier_count) AS skier_count
FROM public.vw_skier_level_distribution_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_dist = pd.read_sql(sql_dist, engine, params={
    "season": season,
    "ptso":   selected_ptso,
    "names":  selected_name
})

sql_eval = """
SELECT
  level_id,
  level_name,
  SUM(eval_passed) AS eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name;
"""
df_eval = pd.read_sql(sql_eval, engine, params={
    "season": season,
    "ptso":   selected_ptso,
    "names":  selected_name
})

# 1) Define the raw IDs in the exact order you want
raw_ids     = [1, 34, 35, 36, 37, 38, 67, 68]
display_lbl = [f"Level {i}" for i in range(1, 9)]

# 2) Build mapping dicts
order_map = {rid: idx for idx, rid in enumerate(raw_ids, start=1)}
name_map  = {rid: lbl for rid, lbl in zip(raw_ids, display_lbl)}

# 3) Apply to df_eval
df_eval["sort_ord"]      = df_eval["level_id"].map(order_map)
df_eval["display_level"] = df_eval["level_id"].map(name_map)

# 4) Drop any rows not in our map, then sort
df_eval = (
    df_eval[df_eval["sort_ord"].notna()]
    .sort_values("sort_ord")
)

# Now plot
col_pie, col_bar = st.columns([1, 1.2], gap="large")

with col_pie:
    st.subheader("Skier Level Distribution")
    if df_dist.empty:
        st.info("No level-distribution data for the selected filters.")
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
                toolbox_opts=opts.ToolboxOpts(
                    orient="horizontal",
                    item_size=18, item_gap=8, pos_left="10%",
                    feature={
                        "saveAsImage": {"title": "save as image"},
                        "restore":     {"title": "restore"},
                        "dataZoom":    {"title": {"zoom": "zoom", "back": "reset zoom"}},
                        "dataView":    {"title": "data view", "lang": ["data view", "turn off", "refresh"]},
                        "magicType":   {"type": ["pie", "funnel"], "title": {"pie": "pie", "funnel": "funnel"}}
                    }
                )
            )
            .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
        )
        html(pie.render_embed(), height=450, scrolling=False)

with col_bar:
    st.subheader("Evaluations by Level")
    if df_eval.empty:
        st.info("No evaluations data for the selected filters.")
    else:
        bar = (
            Bar(init_opts=opts.InitOpts(bg_color="#111111"))
            .add_xaxis(df_eval["display_level"].tolist())
            .add_yaxis(
                series_name="Evaluations",
                y_axis=df_eval["eval_count"].tolist(),
                category_gap="35%"
            )
            .set_global_opts(
                yaxis_opts=opts.AxisOpts(
                    name="Count",
                    axislabel_opts=opts.LabelOpts(color="#ffffff")
                ),
                xaxis_opts=opts.AxisOpts(
                    axislabel_opts=opts.LabelOpts(color="#ffffff")
                ),
                toolbox_opts=opts.ToolboxOpts(
                    orient="horizontal", item_size=18, item_gap=8, pos_left="10%",
                    feature={
                        "saveAsImage": {"title": "save as image"},
                        "restore":     {"title": "restore"},
                        "dataZoom":    {"title": {"zoom": "zoom", "back": "reset zoom"}},
                        "dataView":    {"title": "data view", "lang": ["data view", "turn off", "refresh"]},
                        "magicType":   {"type": ["line", "bar"], "title": {"line": "line chart", "bar": "bar chart"}}
                    }
                )
            )
        )
        html(bar.render_embed(), height=500, scrolling=False)



# ─── 4) Clubs list as interactive AG Grid + CSV download ───
sql_clubs = """
SELECT
  club_id,
  club_name,
  sr_id,
  primary_contact,
  primary_contact_email,
  skiers,
  coaches,
  ptso,
  status
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
df_clubs = pd.read_sql(sql_clubs, engine, params={"season": season})

# apply filters
mask = pd.Series(True, index=df_clubs.index)
if selected_ptso:
    mask &= df_clubs["ptso"].isin(selected_ptso)
if selected_status:
    mask &= df_clubs["status"].isin(selected_status)
if selected_name:
    mask &= df_clubs["club_name"].isin(selected_name)

df_clubs = df_clubs[mask]

st.subheader("Clubs")
search_term = st.text_input("Search Name", "")
if search_term:
    df_clubs = df_clubs[df_clubs["club_name"].str.contains(search_term, case=False)]

if df_clubs.empty:
    st.info("No clubs data for this season.")
else:
    df_display = (
        df_clubs.rename(columns={
            "club_id": "ID",
            "club_name": "Name",
            "sr_id": "SR ID",
            "primary_contact": "Contact",
            "primary_contact_email": "Email",
            "skiers": "Skiers",
            "coaches": "Coaches",
            "ptso": "PTSO",
            "status": "Status",
        })
        .set_index("ID")
    )

    btn_col, _ = st.columns([1, 8])
    with btn_col:
        csv = df_display.reset_index().to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"clubs_{season.replace('/', '-')}.csv",
            mime="text/csv",
            use_container_width=False
        )

    st.markdown(
        """
        <style>
          .ag-root-wrapper, .ag-theme-streamlit {
            width: 100% !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    grid_options = gb.build()

    st.markdown(
        '<div style="position: relative; left:50%; transform: translateX(-50%); width:100vw; overflow-x:auto;">',
        unsafe_allow_html=True,
    )

    AgGrid(
        df_display,
        gridOptions=grid_options,
        theme="streamlit",
        height=1000,
        fit_columns_on_grid_load=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
