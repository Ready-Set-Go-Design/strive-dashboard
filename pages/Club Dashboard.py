# club_dashboard.py

import streamlit as st
import pandas as pd
import base64
from utils.db import engine
from st_aggrid import AgGrid, GridOptionsBuilder
import pyecharts.options as opts
from pyecharts.charts import Pie, Bar, Line
from streamlit.components.v1 import html
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

from utils.sidebar import render_nav

st.set_page_config(
    page_title="Club Dashboard",
    page_icon="⛷️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

render_nav()

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
      /* edge-to-edge layout */
      .reportview-container .main .block-container {
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
      }
      /* header banner */
      .header-banner {
        display: flex; align-items: center; gap: 1rem;
        background-color: #d32f2f; color: white;
        padding: 1rem 2rem; border-radius: 8px; margin-bottom: 2rem;
      }
      /* stat cards */
      .stats-row { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
      .stat-card {
        flex: 1 1 200px; background-color: #393939;
        padding: 1rem !important; border-radius: 6px; text-align: center; margin-bottom: 0.5rem;
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
      /* right-align chart containers */
      .chart-container {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-bottom: 2rem;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── PRE‐FETCH NEEDED VALUES ────────────────────────────────────────────────────────────
target_season = "2024/2025"

# Fetch all club names (to populate the combobox)
nsql_clubs = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(nsql_clubs, engine, params={"season": target_season})
name_options = names_df["club_name"].tolist()

# Sidebar “Status” filter (remains, but we collapse sidebar by default)
status_choices = ["Active", "Inactive"]
status_choice = st.sidebar.multiselect("Status", ["All"] + status_choices, default=["All"])
status_sel = status_choices if "All" in status_choice else status_choice

# ─── HEADER BANNER ─────────────────────────────────────────────────────────────────
logo_path = "Alpine_Canada_logo.svg.png"
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(f"""
<div class="header-banner">
  <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
  <h1 style="margin:0;font-size:3rem;">Club Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ─── MAIN‐PAGE CLUB PICKER ───────────────────────────────────────────────────────────
club_choice = st.selectbox(
    "🔍 Search or pick a club to view its dashboard:",
    options=[""] + name_options,
    index=0,
    help="Start typing to filter clubs…"
)

if not club_choice:
    st.info("⛷️ Select a club above to load its dashboard data.")
    st.stop()

# Re‐render header now that club is chosen
st.markdown(f"""
<div class="header-banner">
  <img src="data:image/png;base64,{logo_b64}" style="height:60px;">
  <h1 style="margin:0;font-size:3rem;">Club Dashboard: {club_choice}</h1>
</div>
""", unsafe_allow_html=True)


# ─── 1) Club‐Level Summary Metrics (combining gender + eval/drill) ─────────────────────
sql_club_sum = """
SELECT
  cs.skiers,
  cs.male_skiers,
  cs.female_skiers,
  (cs.skiers - cs.male_skiers - cs.female_skiers) AS na_skiers,
  cs.coaches,
  cs.parents,
  COALESCE(ns.evaluations_completed, 0) AS evaluations_completed,
  COALESCE(ns.drills_shared, 0)         AS drills_shared
FROM public.vw_club_summary_by_season cs
LEFT JOIN public.vw_national_summary_by_season ns
  ON cs.club_id = ns.club_id
 AND cs.season  = ns.season
WHERE
  cs.season     = %(season)s
  AND cs.club_name = %(club_name)s
  AND cs.status  = ANY(%(status)s);
"""

df_club_sum = pd.read_sql(
    sql_club_sum,
    engine,
    params={"season": target_season, "club_name": club_choice, "status": status_sel}
)

if df_club_sum.empty:
    st.warning(f"No data found for '{club_choice}' in season {target_season}.")
    st.stop()

row = df_club_sum.iloc[0]

st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Total Skiers</p><h2>{int(row.skiers):,}</h2></div>
  <div class="stat-card"><p>Male Skiers</p><h2>{int(row.male_skiers):,}</h2></div>
  <div class="stat-card"><p>Female Skiers</p><h2>{int(row.female_skiers):,}</h2></div>
  <div class="stat-card"><p>Unspecified Gender</p><h2>{int(row.na_skiers):,}</h2></div>
  <div class="stat-card"><p>Coaches</p><h2>{int(row.coaches):,}</h2></div>
  <div class="stat-card"><p>Parents</p><h2>{int(row.parents):,}</h2></div>
  <div class="stat-card"><p>Evaluations</p><h2>{int(row.evaluations_completed):,}</h2></div>
  <div class="stat-card"><p>Drills Shared</p><h2>{int(row.drills_shared):,}</h2></div>
</div>
""", unsafe_allow_html=True)


# ─── 2) Age‐Group Distribution (Granular 4–18, plus <4, >18, Unknown) ───────────────────
st.subheader("Age-Group Distribution")

sql_age = """
SELECT
  age_group,
  count_users
FROM (
  SELECT
    CASE
      WHEN u.yearofbirth IS NULL THEN 'Unknown'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) < 4 THEN '<4'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 4 AND 18 
        THEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth)::INT::TEXT
      ELSE '>18'
    END AS age_group,
    COUNT(*) AS count_users
  FROM users u
  WHERE u.club_id = (
      SELECT id FROM clubs WHERE name = %(club_name)s
    )
    AND u.active IS TRUE
    AND u.role = 'skier'
  GROUP BY
    CASE
      WHEN u.yearofbirth IS NULL THEN 'Unknown'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) < 4 THEN '<4'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 4 AND 18 
        THEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth)::INT::TEXT
      ELSE '>18'
    END
) sub
ORDER BY
  CASE sub.age_group
    WHEN 'Unknown' THEN 0
    WHEN '<4'    THEN 1
    WHEN '4'     THEN 2
    WHEN '5'     THEN 3
    WHEN '6'     THEN 4
    WHEN '7'     THEN 5
    WHEN '8'     THEN 6
    WHEN '9'     THEN 7
    WHEN '10'    THEN 8
    WHEN '11'    THEN 9
    WHEN '12'    THEN 10
    WHEN '13'    THEN 11
    WHEN '14'    THEN 12
    WHEN '15'    THEN 13
    WHEN '16'    THEN 14
    WHEN '17'    THEN 15
    WHEN '18'    THEN 16
    WHEN '>18'   THEN 17
    ELSE 18
  END;
"""

df_age = pd.read_sql(sql_age, engine, params={"club_name": club_choice})

if df_age.empty:
    st.info("No age data for this club.")
else:
    labels = df_age["age_group"].tolist()
    values = df_age["count_users"].tolist()

    bar_age = (
        Bar(init_opts=opts.InitOpts(width="100%", height="500px", bg_color="#111111"))
        .add_xaxis(labels)
        .add_yaxis(
            "Number of Skiers",
            values,
            category_gap="25%",
            label_opts=opts.LabelOpts(
                color="#ffffff",
                formatter=JsCode(
                    """
                    function(params) {
                        return params.value > 5 ? params.value : '';
                    }
                    """
                )
            )
        )
        .set_global_opts(
         
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff", rotate=45)
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}}),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#ffffff"))
        )
    )
    html(bar_age.render_embed(), height=500, scrolling=False)





# ─── 5) Current Level Distribution (Horizontal Bar Chart) ─────────────────────────────────
st.subheader("Current Level Distribution")

sql_current_level = """
SELECT
  u.current_level    AS level_id,
  COALESCE(l.name, 'Level ' || u.current_level::TEXT) AS level_name,
  COUNT(*)           AS num_skiers
FROM users u
LEFT JOIN levels l
  ON u.current_level = l.id
WHERE
  u.club_id = (SELECT id FROM clubs WHERE name = %(club_name)s)
  AND u.role   = 'skier'
  AND u.active IS TRUE
GROUP BY
  u.current_level,
  level_name
ORDER BY
  u.current_level;
"""

df_current = pd.read_sql(
    sql_current_level,
    engine,
    params={"club_name": club_choice}
)

if df_current.empty:
    st.info("No current-level data for this club.")
else:
    levels = df_current["level_name"].tolist()
    counts = df_current["num_skiers"].tolist()

    bar_current = (
        Bar(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add_xaxis(levels)
        .add_yaxis(
            "Skiers",
            counts,
            category_gap="35%",
            label_opts=opts.LabelOpts(color="#ffffff", position="insideRight")
        )
        .reversal_axis()  # horizontal bars
        .set_global_opts(
         
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff", interval=0)
            ),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}}),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#ffffff"))
        )
    )
    # make sure long level names are fully visible
    bar_current.options["grid"] = {"left": "20%", "right": "10%", "containLabel": True}

    html(bar_current.render_embed(), height=400, scrolling=False)





# ─── (Updated) Evaluation Passed by Level (Club) ─────────────────────────────────────────

# Only run the “evaluations by level” query and chart; remove the “skier level distribution” section.

sql_eval_dist = """
SELECT level_id, level_name, SUM(eval_passed) AS eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND club_name = %(club_name)s
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_eval_dist = pd.read_sql(
    sql_eval_dist,
    engine,
    params={"season": target_season, "club_name": club_choice}
)

# Map raw level IDs to display labels and sort order
raw_ids   = [1, 34, 35, 36, 37, 38, 67, 68]
order_map = {rid: idx for idx, rid in enumerate(raw_ids, start=1)}
label_map = {rid: f"Level {idx}" for idx, rid in enumerate(raw_ids, start=1)}

df_eval_dist["display_level"] = df_eval_dist["level_id"].map(label_map)
df_eval_dist["sort_ord"]      = df_eval_dist["level_id"].map(order_map)
df_eval_dist = (
    df_eval_dist[df_eval_dist["sort_ord"].notna() & df_eval_dist["display_level"].notna()]
    .sort_values("sort_ord")
)

st.subheader("Evaluations Passed by Level (Club)")
if df_eval_dist.empty:
    st.info("No evaluation data for this club.")
else:
    bar = (
        Bar(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add_xaxis(df_eval_dist["display_level"].tolist())
        .add_yaxis(
            "Passed",
            df_eval_dist["eval_count"].tolist(),
            category_gap="35%",
            label_opts=opts.LabelOpts(color="#ffffff")
        )
        .set_global_opts(
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {}, "restore": {}, "dataZoom": {},
                "dataView": {}, "magicType": {}
            })
        )
    )
    html(bar.render_embed(), height=400, scrolling=False)


# ─── Pass-Rate % by Level (Club) ─────────────────────────────────────
st.subheader("Pass-Rate % by Level (Club)")

sql_pass_rate_club = """
SELECT
  level_id,
  level_name,
  ROUND(SUM(eval_passed)::numeric / NULLIF(SUM(eval_total), 0) * 100, 1) AS pass_pct
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND club_name = %(club_name)s
GROUP BY level_id, level_name;
"""
df_pass_club = pd.read_sql(
    sql_pass_rate_club,
    engine,
    params={"season": target_season, "club_name": club_choice}
)

# Use the exact same raw_ids → display_level mapping as in the PTSo dashboard
raw_ids   = [1, 34, 35, 36, 37, 38, 67, 68]
order_map = {rid: idx for idx, rid in enumerate(raw_ids, start=1)}
label_map = {rid: f"Level {i}" for i, rid in enumerate(raw_ids, start=1)}

# Attach sort_ord and display_level exactly as before
df_pass_club["sort_ord"]      = df_pass_club["level_id"].map(order_map)
df_pass_club["display_level"] = df_pass_club["level_id"].map(label_map)
df_pass_club = df_pass_club[df_pass_club["sort_ord"].notna()].sort_values("sort_ord")

if df_pass_club.empty:
    st.info("No pass-rate data for this club.")
else:
    data_pairs = list(zip(df_pass_club["display_level"].tolist(), df_pass_club["pass_pct"].tolist()))

    pie_pass_club = (
        Pie(init_opts=opts.InitOpts(width="100%", height="600px", bg_color="#111111"))
        .add(
            "Pass %",
            data_pairs,
            radius=["15%", "65%"],
            center=["55%", "50%"],
            rosetype="radius",
            label_opts=opts.LabelOpts(
                formatter="{b}\n{c} %",
                position="outside",
                font_size=14,
                font_weight="bold",
                color="#ffffff"
            ),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_left="left",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff", font_size=14)
            ),
            toolbox_opts=opts.ToolboxOpts(
                feature={
                    "saveAsImage": {"title": "Save"},
                    "restore": {"title": "Reset"},
                }
            )
        )
    )

    html(pie_pass_club.render_embed(), height=600, scrolling=False)


# ─── Skiers list for the selected club ─────────────────────────────────────────────────
st.subheader("Skiers in This Club")

sql_skiers = """
SELECT
  u.id                         AS skier_id,
  u.firstname                  AS first_name,
  u.lastname                   AS last_name,
  u.email                      AS email,
  u.yearofbirth                AS year_of_birth,
  COALESCE(u.gender, 'Unknown')        AS gender,
  COALESCE(u.device_platform, 'Unknown') AS device_platform,
  COALESCE(u.locale, 'Unknown')          AS locale,
  CASE WHEN u.verified_at IS NOT NULL THEN 'Yes' ELSE 'No' END AS verified,
  u.created_at                 AS joined_at,
  u.last_login                 AS last_login,
  CASE WHEN u.active IS TRUE THEN 'Active' ELSE 'Inactive' END AS active_status,
  COALESCE(l.name, 'Level ' || u.current_level::text) AS current_level
FROM users u
JOIN clubs c
  ON u.club_id = c.id
LEFT JOIN levels l
  ON l.id = u.current_level
WHERE
  c.name   = %(club_name)s
  AND u.role   = 'skier'
ORDER BY
  u.lastname, u.firstname;
"""

df_skiers = pd.read_sql(
    sql_skiers,
    engine,
    params={"club_name": club_choice}
)

if df_skiers.empty:
    st.info("No skiers found for this club.")
else:
    df_skiers_display = (
        df_skiers.rename(columns={
            "skier_id": "ID",
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email",
            "year_of_birth": "Year of Birth",
            "gender": "Gender",
            "device_platform": "Device",
            "locale": "Locale",
            "verified": "Verified?",
            "joined_at": "Joined At",
            "last_login": "Last Login",
            "active_status": "Active Status",
            "current_level": "Current Level"
        })
        .set_index("ID")
    )

    btn_col, _ = st.columns([1, 8])
    with btn_col:
        csv = df_skiers_display.reset_index().to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Skiers CSV",
            data=csv,
            file_name=f"skiers_{club_choice.replace(' ', '_')}.csv",
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

    gb = GridOptionsBuilder.from_dataframe(df_skiers_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    gb.configure_grid_options(domLayout="autoHeight")
    grid_options = gb.build()

    AgGrid(
        df_skiers_display,
        gridOptions=grid_options,
        theme="streamlit",
        fit_columns_on_grid_load=True
    )
