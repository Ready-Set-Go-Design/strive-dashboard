import streamlit as st
import pandas as pd
import base64
from utils.db import engine
from st_aggrid import AgGrid, GridOptionsBuilder  # for the interactive table
import pyecharts.options as opts
from pyecharts.charts import Pie, Bar, Line
from streamlit.components.v1 import html  # built-in
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="PTSO Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Widen canvas & apply scale to block-container only ───────────────────
st.markdown(
    """
    <style>
      /* Scale just the main content area */
      .reportview-container .main .block-container {
        transform: scale(0.80);
        transform-origin: top left;
        max-width: 100% !important;
        padding: 1rem 2rem;
      }
      /* Remove any zoom on html/body so dropdowns calculate correctly */
      /* html, body, .reportview-container .main .block-container {
           zoom: 0.85 !important;
      } */
    </style>
    """,
    unsafe_allow_html=True,
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
  <h1 style="margin:0;font-size:3rem;">PTSO Dashboard</h1>
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


# ─── 1) Provincial summary metrics ──────────────────────────
sql_ptso_sum = """
WITH base AS (
  SELECT
    club_id,
    skiers,
    coaches,
    evaluations_completed,
    drills_shared
  FROM public.vw_national_summary_by_season
  WHERE season    = %(season)s
    AND ptso      = ANY(%(ptso)s)
    AND status    = ANY(%(status)s)
    AND club_name = ANY(%(names)s)
)
SELECT
  COUNT(DISTINCT club_id)      AS active_clubs,
  SUM(skiers)                  AS total_skiers,
  SUM(coaches)                 AS total_coaches,
  SUM(evaluations_completed)   AS evals_done,
  SUM(drills_shared)           AS drills_shared
FROM base;
"""

df_sum = pd.read_sql(
    sql_ptso_sum,
    engine,
    params={
        "season": season,
        "ptso":   selected_ptso,
        "status": selected_status,
        "names":  selected_name
    }
)

if df_sum.empty:
    st.warning(f"No data found for season {season} with the selected filters.")
    st.stop()

row = df_sum.iloc[0]

# ─── derive the ratio‑style KPIs safely ─────────────────────
active_clubs      = int(row.active_clubs or 0)
total_skiers      = int(row.total_skiers or 0)
total_coaches     = int(row.total_coaches or 0)
coach_skier_ratio = (total_coaches / total_skiers) if total_skiers else 0
eval_completion   = (row.evals_done / total_skiers) if total_skiers else 0
drills_per_coach  = (row.drills_shared / total_coaches) if total_coaches else 0

# ─── metric cards (reuse existing CSS) ─────────────────────
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Active Clubs</p><h2>{active_clubs:,}</h2></div>
  <div class="stat-card"><p>Total Skiers</p><h2>{total_skiers:,}</h2></div>
  <div class="stat-card"><p>Coach / Skier Ratio</p><h2>{coach_skier_ratio:.2f}</h2></div>
  <div class="stat-card"><p>Eval Completion %</p><h2>{eval_completion:.0%}</h2></div>
  <div class="stat-card"><p>Drills per Coach</p><h2>{drills_per_coach:.2f}</h2></div>
</div>
""", unsafe_allow_html=True)


from pyecharts.options import DataZoomOpts

# ─── 2 & 3) Top-10 Clubs by Skiers with Eval Completion stacked below ─────────

# 2a) TOP-10 CLUBS BY SKIER COUNT (unchanged)
sql_top_clubs = """
SELECT
  club_name,
  SUM(skiers) AS skier_total
FROM public.vw_club_summary_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND status    = ANY(%(status)s)
  AND club_name = ANY(%(names)s)
GROUP BY club_name
ORDER BY skier_total DESC
LIMIT 10;
"""
df_top = pd.read_sql(sql_top_clubs, engine, params={
    "season": season,
    "ptso":   selected_ptso,
    "status": selected_status,
    "names":  selected_name
})

# 3) EVALUATION COMPLETION RATE (all clubs, zoom/pan)
sql_eval_rate = """
SELECT
  club_name,
  SUM(evaluations_completed) AS evals_done,
  SUM(skiers)                AS skiers
FROM public.vw_national_summary_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND status    = ANY(%(status)s)
  AND club_name = ANY(%(names)s)
GROUP BY club_name
HAVING SUM(skiers) > 0
ORDER BY SUM(evaluations_completed)::numeric
       / NULLIF(SUM(skiers),0) DESC;
"""
df_rate = pd.read_sql(sql_eval_rate, engine, params={
    "season": season,
    "ptso":   selected_ptso,
    "status": selected_status,
    "names":  selected_name
})

col = st.columns([1])[0]
with col:
    # ─── Top 10 Clubs by Skiers (bigger) ───────────────────────────
    st.subheader("Top 10 Clubs by Skier Count")
    if not df_top.empty:
        bar = (
            Bar(init_opts=opts.InitOpts(
                    width="100%",   # full container width
                    height="800px", # taller chart
                    bg_color="#111111"
                ))
            .add_xaxis(df_top["club_name"].tolist())
            .add_yaxis("Skiers", df_top["skier_total"].tolist(), category_gap="35%")
            .reversal_axis()
            .set_series_opts(label_opts=opts.LabelOpts(position="right", color="#ffffff"))
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
                yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
                toolbox_opts=opts.ToolboxOpts(feature={
                    "saveAsImage": {"title": "save as image"},
                    "restore":     {"title": "restore"}
                })
            )
        )
        html(bar.render_embed(), height=800, scrolling=False)


    # ─── Evaluation Completion Rate by Club (bigger + zoom/pan) ─────────────────────
    st.subheader("Evaluation Completion Rate by Club")
    if not df_rate.empty:
        perc_done = [
            round(row.evals_done / row.skiers * 100, 1)
            for _, row in df_rate.iterrows()
        ]
        perc_rem = [round(100 - d, 1) for d in perc_done]

        bar_percent = (
            Bar(init_opts=opts.InitOpts(
                    width="100%",
                    height="800px",
                    theme=ThemeType.LIGHT
                ))
            .add_xaxis(df_rate["club_name"].tolist())
            .add_yaxis("Completed %", perc_done, stack="stack1")
            .add_yaxis("Remaining %", perc_rem,  stack="stack1")
            .reversal_axis()
            .set_series_opts(
                label_opts=opts.LabelOpts(position="insideRight", formatter="{c} %")
            )
            .set_global_opts(
                datazoom_opts=[DataZoomOpts(type_="slider", orient="vertical")],
                xaxis_opts=opts.AxisOpts(
                    type_="value",
                    min_=0, max_=100,
                    axislabel_opts=opts.LabelOpts(color="#333333"),
                    splitline_opts=opts.SplitLineOpts(is_show=True)
                ),
                yaxis_opts=opts.AxisOpts(
                    type_="category",
                    axislabel_opts=opts.LabelOpts(color="#333333")
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="shadow",
                    formatter="{b0}: {c0} %"
                ),
                toolbox_opts=opts.ToolboxOpts(feature={
                    "saveAsImage": {"title": "Save"},
                    "restore":     {"title": "Reset"}
                })
            )
        )
        html(bar_percent.render_embed(), height=800, scrolling=False)


# ─── Pass‑Rate % by Level (from the new view) ──────────────
st.subheader("Pass‑Rate % by Level")

sql_pass_rate = """
SELECT
  level_name,
  ROUND(
    SUM(eval_passed)::numeric / NULLIF(SUM(eval_total),0) * 100,
    1
  ) AS pass_pct
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND ptso      = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_name
ORDER BY MIN(level_id);          -- keeps logical order
"""

df_pass = pd.read_sql(
    sql_pass_rate,
    engine,
    params={
        "season": season,
        "ptso":   selected_ptso,
        "names":  selected_name
    }
)

if df_pass.empty:
    st.info("No pass‑rate data for the selected filters.")
else:
    # ── Nightingale‑Rose (polar pie) instead of bar ─────────
    # ── Light‑theme Nightingale‑Rose chart ─────────────────────
    data_pairs = list(
    zip(df_pass["level_name"].tolist(), df_pass["pass_pct"].round(1).tolist())
)

# pastel palette by pass‑rate band
rose_colors = [
    "#ff9e9e" if pct < 50      # soft red
    else "#ffdd8d" if pct < 75 # soft orange/yellow
    else "#7ed6c8"             # soft teal
    for _, pct in data_pairs
]

pie_rose = (
    Pie(init_opts=opts.InitOpts(bg_color="#f5f5f5"))  # ← lighter canvas
    .add(
        series_name="Pass %",
        data_pair=data_pairs,
        radius=["15%", "65%"],
        center=["55%", "50%"],
        rosetype="radius",
        label_opts=opts.LabelOpts(
            formatter="{b}\n{c} %",
            position="outside",
            color="#333333"      # dark text on light bg
        ),
        itemstyle_opts=opts.ItemStyleOpts(color=rose_colors)
    )
    .set_global_opts(
        legend_opts=opts.LegendOpts(
            orient="vertical",
            pos_left="left",
            textstyle_opts=opts.TextStyleOpts(color="#333333")
        ),
        toolbox_opts=opts.ToolboxOpts(
            orient="horizontal",
            pos_left="10%",
            feature={
                "saveAsImage": {"title": "Save"},
                "restore":     {"title": "Reset"}
            }
        )
    )
)

html(pie_rose.render_embed(), height=500, scrolling=False)






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
