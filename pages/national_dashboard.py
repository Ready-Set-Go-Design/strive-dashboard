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
        zoom: 0.85 !important;
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

# ─── Sidebar filters ───────────────────────────────────────
st.sidebar.markdown("## Filters")
# wrap filters so our CSS only affects them
st.sidebar.markdown('<div class="right-filters">', unsafe_allow_html=True)

# Season (single-select)
season = st.sidebar.selectbox("Select Season", ["2024/2025"])

# PTSO (single-select dropdown with “All”)
sql_ptso = """
SELECT DISTINCT ptso
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY ptso;
"""
ptso_df = pd.read_sql(sql_ptso, engine, params={"season": season})
ptso_options = ptso_df["ptso"].dropna().tolist()
ptso_choice = st.sidebar.selectbox("Filter by PTSO", ["All"] + ptso_options)
selected_ptso = ptso_options if ptso_choice == "All" else [ptso_choice]

# Status (single-select dropdown with “All”)
status_choices = ["Active", "Inactive"]
status_choice = st.sidebar.selectbox("Filter by Status", ["All"] + status_choices)
selected_status = status_choices if status_choice == "All" else [status_choice]

# Club Name (single-select dropdown with “All”)
sql_names = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(sql_names, engine, params={"season": season})
name_options = names_df["club_name"].tolist()
name_choice = st.sidebar.selectbox("Filter by Club Name", ["All"] + name_options)
selected_name = name_options if name_choice == "All" else [name_choice]

st.sidebar.markdown('</div>', unsafe_allow_html=True)


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
    "ptso": selected_ptso,
    "names": selected_name
})

sql_eval = """
SELECT
  level_name,
  SUM(eval_count) AS eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_eval = pd.read_sql(sql_eval, engine, params={
    "season": season,
    "ptso": selected_ptso,
    "names": selected_name
})

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
                    item_size=18,
                    item_gap=8,
                    pos_left="10%",
                    feature={
                        "saveAsImage": {"title": "save as image"},
                        "restore":     {"title": "restore"},
                        "dataZoom":    {"title": {"zoom": "zoom", "back": "reset zoom"}},
                        "dataView":    {"title": "data view", "lang": ["data view", "turn off", "refresh"]},
                        "magicType":   {"type": ["pie", "funnel"], "title": {"pie": "pie", "funnel": "funnel"}}
                    }
                )
            )
            .set_series_opts(
                label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff")
            )
        )
        html(pie.render_embed(), height=450, scrolling=False)

with col_bar:
    st.subheader("Evaluations by Level")
    if df_eval.empty:
        st.info("No evaluations data for the selected filters.")
    else:
        bar = (
            Bar(init_opts=opts.InitOpts(bg_color="#111111"))
            .add_xaxis(df_eval["level_name"].tolist())
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
                    orient="horizontal",
                    item_size=18,
                    item_gap=8,
                    pos_left="10%",
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
    # prepare display DataFrame
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

    # CSV download button
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

    # inject full-bleed CSS & force grid width
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

    # build AG Grid options
    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    grid_options = gb.build()

    # wrap AG Grid in full-viewport container
    st.markdown(
        '<div style="position: relative; left:50%; transform: translateX(-50%); width:100vw; overflow-x:auto;">',
        unsafe_allow_html=True,
    )

    # render AG Grid full-width & taller
    AgGrid(
        df_display,
        gridOptions=grid_options,
        theme="streamlit",
        height=1000,       # increased height
        fit_columns_on_grid_load=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)
