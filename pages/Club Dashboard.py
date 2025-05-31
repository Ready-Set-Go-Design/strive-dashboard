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


# ─── 2) Age‐Group Distribution ─────────────────────────────────────────────────────────
st.subheader("Age-Group Distribution")

# We compute age via (current year - yearofbirth) and bucket into categories.
# Because PostgreSQL won’t let us ORDER BY an alias at the same select level,
# we wrap the CASE aggregation in a subquery and then order in the outer SELECT.

sql_age = """
SELECT
  age_group,
  count_users
FROM (
  SELECT
    CASE
      WHEN u.yearofbirth IS NULL THEN 'Unknown'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) < 18 THEN '<18'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 18 AND 25 THEN '18-25'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 26 AND 35 THEN '26-35'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 36 AND 50 THEN '36-50'
      ELSE '50+'
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
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) < 18 THEN '<18'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 18 AND 25 THEN '18-25'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 26 AND 35 THEN '26-35'
      WHEN (EXTRACT(YEAR FROM CURRENT_DATE) - u.yearofbirth) BETWEEN 36 AND 50 THEN '36-50'
      ELSE '50+'
    END
) sub
ORDER BY
  CASE sub.age_group
    WHEN '<18' THEN 1
    WHEN '18-25' THEN 2
    WHEN '26-35' THEN 3
    WHEN '36-50' THEN 4
    WHEN '50+'  THEN 5
    ELSE 6
  END;
"""

df_age = pd.read_sql(sql_age, engine, params={"club_name": club_choice})

if df_age.empty:
    st.info("No age data for this club.")
else:
    bar_age = (
        Bar(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add_xaxis(df_age["age_group"].tolist())
        .add_yaxis("Number of Skiers", df_age["count_users"].tolist(), category_gap="25%")
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="Age Groups",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            xaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}}),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#ffffff"))
        )
        .set_series_opts(label_opts=opts.LabelOpts(color="#ffffff"))
    )
    html(bar_age.render_embed(), height=400, scrolling=False)


# ─── 3) Device‐Platform Breakdown ───────────────────────────────────────────────────────
st.subheader("Device Platform Breakdown")

sql_device = """
SELECT
  COALESCE(u.device_platform, 'Unknown') AS platform,
  COUNT(*) AS count_users
FROM users u
WHERE u.club_id = (
    SELECT id FROM clubs WHERE name = %(club_name)s
  )
  AND u.active IS TRUE
  AND u.role = 'skier'
GROUP BY platform
ORDER BY count_users DESC;
"""
df_device = pd.read_sql(sql_device, engine, params={"club_name": club_choice})

if df_device.empty:
    st.info("No device‐platform data for this club.")
else:
    pie_device = (
        Pie(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add(
            "",
            df_device[["platform", "count_users"]].values.tolist(),
            radius=["30%", "65%"],
            center=["50%", "50%"],
            rosetype="none"
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Devices Used by Skiers", pos_left="center", title_textstyle_opts=opts.TextStyleOpts(color="#ffffff")),
            legend_opts=opts.LegendOpts(
                orient="vertical", pos_left="left",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}})
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
    )
    html(pie_device.render_embed(), height=400, scrolling=False)


# ─── 4) Verification Rate (Verified vs. Unverified) ─────────────────────────────────────
st.subheader("Verification Rate (%)")

sql_verify = """
SELECT
  SUM(CASE WHEN u.verified_at IS NOT NULL THEN 1 ELSE 0 END) AS verified,
  SUM(CASE WHEN u.verified_at IS NULL THEN 1 ELSE 0 END)   AS unverified
FROM users u
WHERE u.club_id = (
    SELECT id FROM clubs WHERE name = %(club_name)s
  )
  AND u.active IS TRUE
  AND u.role = 'skier';
"""
df_verify = pd.read_sql(sql_verify, engine, params={"club_name": club_choice})

if df_verify.empty:
    st.info("No verification data for this club.")
else:
    verified_count   = int(df_verify.at[0, "verified"])
    unverified_count = int(df_verify.at[0, "unverified"])
    total_users      = verified_count + unverified_count

    # Prepare pie slices
    data_verify = [
        ("Verified", verified_count),
        ("Unverified", unverified_count)
    ]

    pie_verify = (
        Pie(init_opts=opts.InitOpts(width="100%", height="300px", bg_color="#111111"))
        .add(
            "Verification",
            data_verify,
            radius=["40%", "65%"],
            center=["50%", "50%"]
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=f"Verified: {verified_count / max(total_users,1) * 100:.1f}%",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            legend_opts=opts.LegendOpts(
                orient="vertical", pos_left="left",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}})
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
    )
    html(pie_verify.render_embed(), height=300, scrolling=False)


# ─── 5) Task Pass/Fail Rate ──────────────────────────────────────────────────────────────
st.subheader("Task Pass/Fail Rate")

# Use COALESCE in SQL so that passed_count/failed_count are never NULL.
sql_tasks = """
SELECT
  COALESCE(SUM(CASE WHEN ut.passed IS TRUE THEN 1 ELSE 0 END), 0)  AS passed_count,
  COALESCE(SUM(CASE WHEN ut.passed IS FALSE THEN 1 ELSE 0 END), 0) AS failed_count
FROM user_tasks ut
JOIN users u ON u.id = ut.user_id
WHERE u.club_id = (
    SELECT id FROM clubs WHERE name = %(club_name)s
  )
  AND u.role = 'skier';
"""
df_tasks = pd.read_sql(sql_tasks, engine, params={"club_name": club_choice})

# Now df_tasks.at[0, "passed_count"] and "failed_count" will always be an integer (never None).
passed_count = int(df_tasks.at[0, "passed_count"])
failed_count = int(df_tasks.at[0, "failed_count"])
total_tasks  = passed_count + failed_count

# If total_tasks is 0, adjust to avoid division by zero
data_tasks = [
    ("Passed" if total_tasks>0 else "Passed", passed_count),
    ("Failed" if total_tasks>0 else "Failed", failed_count)
]

pie_tasks = (
    Pie(init_opts=opts.InitOpts(width="100%", height="300px", bg_color="#111111"))
    .add(
        "Tasks",
        data_tasks,
        radius=["40%", "65%"],
        center=["50%", "50%"]
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(
            title=f"Pass Rate: { (passed_count / total_tasks * 100):.1f}%"
                  if total_tasks > 0 else "Pass Rate: N/A",
            pos_left="center",
            title_textstyle_opts=opts.TextStyleOpts(color="#ffffff")
        ),
        legend_opts=opts.LegendOpts(
            orient="vertical", pos_left="left",
            textstyle_opts=opts.TextStyleOpts(color="#ffffff")
        ),
        toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}})
    )
    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
)
html(pie_tasks.render_embed(), height=300, scrolling=False)


# ─── 6) Notification Volume Over Time (Last 6 Months) ─────────────────────────────────
st.subheader("Notification Volume (Last 6 Months)")

sql_notifications = """
SELECT
  date_trunc('month', created_at)::date AS month,
  COUNT(*) AS notif_count
FROM user_notifications un
WHERE un.recipient_id IN (
    SELECT id FROM users WHERE club_id = (
      SELECT id FROM clubs WHERE name = %(club_name)s
    )
  )
  AND created_at >= (CURRENT_DATE - INTERVAL '6 months')
GROUP BY 1
ORDER BY 1;
"""
df_notifs = pd.read_sql(sql_notifications, engine, params={"club_name": club_choice})

if df_notifs.empty:
    st.info("No notification data for this club in the last 6 months.")
else:
    # Ensure 'month' is a datetime type
    df_notifs["month"] = pd.to_datetime(df_notifs["month"])

    # Create a string column for formatting as YYYY-MM
    df_notifs["month_str"] = df_notifs["month"].dt.strftime("%Y-%m")

    line_notif = (
        Line(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add_xaxis(df_notifs["month_str"].tolist())
        .add_yaxis("Notifications", df_notifs["notif_count"].tolist(), label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="Notifications over Last 6 Months",
                pos_left="center",
                title_textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            yaxis_opts=opts.AxisOpts(
                axislabel_opts=opts.LabelOpts(color="#ffffff")
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {}, "restore": {}}),
            legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#ffffff"))
        )
        .set_series_opts(linestyle_opts=opts.LineStyleOpts(width=3), label_opts=opts.LabelOpts(color="#ffffff"))
    )
    html(line_notif.render_embed(), height=400, scrolling=False)


# ─── (Existing) Other Sections: Level Distribution / Eval by Level / Pass‐Rate / Club Details ──
# ──────────────────────────────────────────────────────────────────────────────────────────────────

# Level distribution + evaluation by level:
sql_level_dist = """
SELECT level_id, level_name, SUM(skier_count) AS skier_count
FROM public.vw_skier_level_distribution_by_season
WHERE season    = %(season)s
  AND club_name = %(club_name)s
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_level_dist = pd.read_sql(sql_level_dist, engine, params={"season": target_season, "club_name": club_choice})

sql_eval_dist = """
SELECT level_id, level_name, SUM(eval_passed) AS eval_count
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND club_name = %(club_name)s
GROUP BY level_id, level_name
ORDER BY level_id;
"""
df_eval_dist = pd.read_sql(sql_eval_dist, engine, params={"season": target_season, "club_name": club_choice})

raw_ids   = [1,34,35,36,37,38,67,68]
order_map = {rid: idx for idx, rid in enumerate(raw_ids, start=1)}
label_map = {rid: f"Level {idx}" for idx, rid in enumerate(raw_ids, start=1)}

df_level_dist["display_level"] = df_level_dist["level_id"].map(label_map)
df_level_dist = df_level_dist[df_level_dist["display_level"].notna()]

st.subheader("Skier Level Distribution (Club)")
if df_level_dist.empty:
    st.info("No level distribution data for this club.")
else:
    pie = (
        Pie(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add(
            "",
            df_level_dist[["display_level", "skier_count"]].values.tolist(),
            radius=["40%", "70%"]
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_left="left",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff")
            ),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {}, "restore": {}, "dataZoom": {},
                "dataView": {}, "magicType": {}
            })
        )
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}", color="#ffffff"))
    )
    html(pie.render_embed(), height=400, scrolling=False)

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
        .add_yaxis("Passed", df_eval_dist["eval_count"].tolist(), category_gap="35%")
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

# Pass-Rate % by Level
st.subheader("Pass-Rate % by Level (Club)")
sql_pass_rate = """
SELECT
  level_id,
  level_name,
  ROUND(SUM(eval_passed)::numeric / NULLIF(SUM(eval_total), 0) * 100, 1) AS pass_pct
FROM public.vw_evaluations_by_level_by_season
WHERE season    = %(season)s
  AND club_name = %(club_name)s
GROUP BY level_id, level_name;
"""
df_pass = pd.read_sql(
    sql_pass_rate,
    engine,
    params={"season": target_season, "club_name": club_choice}
)

df_pass["display_level"] = df_pass["level_id"].map(label_map)
df_pass["sort_ord"]      = df_pass["level_id"].map(order_map)
df_pass = df_pass[df_pass["sort_ord"].notna()].sort_values("sort_ord")

if df_pass.empty:
    st.info("No pass-rate data for this club.")
else:
    data_pairs = list(zip(df_pass["display_level"].tolist(), df_pass["pass_pct"].tolist()))
    pie_pass = (
        Pie(init_opts=opts.InitOpts(width="100%", height="400px", bg_color="#111111"))
        .add(
            "Pass %",
            data_pairs,
            radius=["15%", "65%"],
            center=["55%", "50%"],
            rosetype="radius",
            label_opts=opts.LabelOpts(
                formatter="{b}\n{c} %",
                position="outside",
                font_size=12,
                font_weight="bold",
                color="#ffffff"
            ),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_left="left",
                textstyle_opts=opts.TextStyleOpts(color="#ffffff", font_size=12)
            ),
            toolbox_opts=opts.ToolboxOpts(
                feature={
                    "saveAsImage": {"title": "Save"},
                    "restore": {"title": "Reset"},
                }
            )
        )
    )
    html(pie_pass.render_embed(), height=400, scrolling=False)

# Club Details Table
sql_clubs = """
SELECT 
  cs.club_id        AS club_id, 
  cs.club_name      AS club_name,
  cs.coaches        AS coaches,
  cs.parents        AS parents,
  cs.skiers         AS skiers,
  cs.male_skiers    AS male_skiers,
  cs.female_skiers  AS female_skiers,
  (cs.skiers - cs.male_skiers - cs.female_skiers) AS na_skiers,
  ns.evaluations_completed AS evaluations_completed,
  ns.drills_shared         AS drills_shared,
  cs.ptso           AS ptso, 
  'Active'          AS status
FROM public.vw_club_summary_by_season cs
LEFT JOIN public.vw_national_summary_by_season ns
  ON cs.club_id = ns.club_id 
 AND cs.season  = ns.season
WHERE 
  cs.season    = %(season)s 
  AND cs.club_name = %(club_name)s
ORDER BY cs.club_name;
"""
_df_clubs = pd.read_sql(
    sql_clubs,
    engine,
    params={"season": target_season, "club_name": club_choice}
)

st.subheader("Club Details")
if _df_clubs.empty:
    st.info("No club details found.")
else:
    df_display = (
        _df_clubs.rename(columns={
            "club_id": "ID",
            "club_name": "Name",
            "coaches": "Coaches",
            "parents": "Parents",
            "skiers": "Total Skiers",
            "male_skiers": "Male Skiers",
            "female_skiers": "Female Skiers",
            "na_skiers": "Unspecified Gender",
            "evaluations_completed": "Evaluations",
            "drills_shared": "Drills Shared",
            "ptso": "PTSO",
            "status": "Status"
        })
        .set_index("ID")
    )

    btn_col, _ = st.columns([1, 8])
    with btn_col:
        csv = df_display.reset_index().to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"club_{club_choice.replace(' ', '_')}_{target_season.replace('/', '-')}.csv",
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

    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_grid_options(domLayout="autoHeight")
    grid_options = gb.build()

    AgGrid(
        df_display,
        gridOptions=grid_options,
        theme="streamlit",
        fit_columns_on_grid_load=True
    )
