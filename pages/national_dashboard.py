import streamlit as st
import pandas as pd
import base64
from utils.db import engine
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

# ─── CSS for banner & metric cards ─────────────────────────
st.markdown("""<style>
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

# Season (single-select)
seasons = ["2022/2023", "2023/2024", "2024/2025"]
season = st.sidebar.selectbox("Select Season", seasons)

# PTSO (multi-select)
sql_ptso = """
SELECT DISTINCT ptso
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY ptso;
"""
ptso_df = pd.read_sql(sql_ptso, engine, params={"season": season})
ptso_options = ptso_df["ptso"].dropna().tolist()
selected_ptso = st.sidebar.multiselect(
    "Filter by PTSO",
    options=ptso_options,
    default=ptso_options,
    help="Show only clubs in these PTSOs"
)

# Status (multi-select)
status_choices = ["Active", "Inactive"]
selected_status = st.sidebar.multiselect(
    "Filter by Status",
    options=status_choices,
    default=status_choices,
    help="Show only clubs with this status"
)

# Club Name (multi-select)
sql_names = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(sql_names, engine, params={"season": season})
name_options = names_df["club_name"].tolist()
selected_name = st.sidebar.multiselect(
    "Filter by Club Name",
    options=name_options,
    default=name_options,
    help="Show only selected clubs"
)

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
  b.level_name,
  SUM(b.skier_count) AS skier_count
FROM public.vw_skier_level_distribution_by_season b
WHERE b.season    = %(season)s
  AND b.ptso      = ANY(%(ptso)s)
  AND b.club_name = ANY(%(names)s)
GROUP BY b.level_id, b.level_name
ORDER BY b.level_id;
"""
df_dist = pd.read_sql(
    sql_dist,
    engine,
    params={
        "season": season,
        "ptso": selected_ptso,
        "names": selected_name
    }
)

sql_eval = """
SELECT
  b.level_name,
  SUM(b.eval_count) AS eval_count
FROM public.vw_evaluations_by_level_by_season b
WHERE b.season    = %(season)s
  AND b.ptso      = ANY(%(ptso)s)
  AND b.club_name = ANY(%(names)s)
GROUP BY b.level_id, b.level_name
ORDER BY b.level_id;
"""
df_eval = pd.read_sql(
    sql_eval,
    engine,
    params={
        "season": season,
        "ptso": selected_ptso,
        "names": selected_name
    }
)

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
                    pos_left="10%",  # ← shift toolbox over
                    feature={
                        "saveAsImage": {"title": "save as image"},
                        "restore":     {"title": "restore"},
                        "dataZoom":    {"title": {"zoom": "zoom", "back": "reset zoom"}},
                        "dataView":    {"title": "data view", "lang": ["data view", "turn off", "refresh"]},
                        "magicType":   {"type": ["pie", "funnel"], "title": {"pie": "pie", "funnel": "funnel"}}
                    }
                ),
                title_opts=opts.TitleOpts(title="")
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
                legend_opts=opts.LegendOpts(
                    textstyle_opts=opts.TextStyleOpts(color="#ffffff")
                ),
                toolbox_opts=opts.ToolboxOpts(
                    orient="horizontal",
                    item_size=18,
                    item_gap=8,
                    pos_left="10%",  # ← same shift here
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
        html(bar.render_embed(), height=500, scrolling=False)


# ─── 4) Clubs list as editable grid + CSV download ─────────
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

# ─── Apply sidebar filters correctly ────────────────────────
mask = pd.Series(True, index=df_clubs.index)
if selected_ptso:
    mask &= df_clubs["ptso"].isin(selected_ptso)
if selected_status:
    mask &= df_clubs["status"].isin(selected_status)
if selected_name:
    mask &= df_clubs["club_name"].isin(selected_name)
df_clubs = df_clubs[mask]

# ─── Clubs header + search + small CSV button ─────────────
st.subheader("Clubs")
search_term = st.text_input("Search Name", "")
if search_term:
    df_clubs = df_clubs[df_clubs["club_name"].str.contains(search_term, case=False)]

if df_clubs.empty:
    st.info("No clubs data for this season.")
else:
    df_display = (
        df_clubs
        .rename(columns={
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
    df_display["Status"] = df_display["Status"].astype("category")

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

    st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=False,
        column_config={
            "Name": st.column_config.TextColumn("Name"),
            "SR ID": st.column_config.NumberColumn("SR ID"),
            "Contact": st.column_config.TextColumn("Contact"),
            "Email": st.column_config.TextColumn("Email"),
            "Skiers": st.column_config.NumberColumn("Skiers"),
            "Coaches": st.column_config.NumberColumn("Coaches"),
            "PTSO": st.column_config.TextColumn("PTSO"),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Active", "Inactive"]
            ),
        }
    )
