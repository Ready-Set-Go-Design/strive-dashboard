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

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="PTSO Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── GLOBAL CSS ─────────────────────────────────────────────
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
st.markdown(
    """
    <style>
      /* right-align any direct child chart container */
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

st.markdown(
    """
    <style>
      /* 1) Let the sidebar container overflow so nothing inside it clips children */
      [data-testid="stSidebar"] {
        overflow: visible !important;
      }

      /* 2) Pull every BaseWeb popover out of the sidebar's stacking context
            and force it to the right edge of the viewport */
      .baseui-popover__popper {
        position: fixed !important;
        left: auto     !important;
        right: 16px    !important;  /* tweak as needed */
        top: auto      !important;
        z-index: 9999  !important;
        transform-origin: top right !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

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

# ─── SIDEBAR LOGO & FILTERS ────────────────────────────
st.sidebar.image(logo_path, width=200)

# Pre-fetch options
target_season = "2024/2025"

# PTSO options
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

# Club Name options
nsql = """
SELECT DISTINCT club_name
FROM public.vw_club_summary_by_season
WHERE season = %(season)s
ORDER BY club_name;
"""
names_df = pd.read_sql(nsql, engine, params={"season": target_season})
name_options = names_df["club_name"].tolist()

# Sidebar filters
season = st.sidebar.selectbox("Season", [target_season])
ptso_choice = st.sidebar.multiselect("PTSO", ["All"] + ptso_options, default=["All"])
status_choice = st.sidebar.multiselect("Status", ["All"] + status_choices, default=["All"])
name_choice = st.sidebar.multiselect("Club", ["All"] + name_options, default=["All"])
search_name = st.sidebar.text_input("🔍 Search Club Name", "")

# Resolve "All" selections
ptso_sel = ptso_options   if "All" in ptso_choice   else ptso_choice
status_sel = status_choices if "All" in status_choice else status_choice
club_sel = name_options   if "All" in name_choice   else name_choice

st.markdown(
    """
    <style>
    /* lay out the radio buttons in a row */
    div[role="radiogroup"] {
      display: flex !important;
      gap: 1rem !important;
    }
    /* make each label look like a pill */
    div[role="radiogroup"] label {
      background-color: #2E3B4E !important;
      color: #ffffff !important;
      padding: 0.4rem 0.8rem !important;
      border-radius: 20px !important;
      cursor: pointer !important;
      font-weight: 500 !important;
      transition: background-color 0.2s ease !important;
    }
    /* hide the default dot */
    div[role="radiogroup"] input[type="radio"] {
      display: none !important;
    }
    /* style the checked pill */
    div[role="radiogroup"] input[type="radio"]:checked + label {
      background-color: #009688 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ─── Province selector ──────────────────────────────────
provinces = ["All"] + ptso_options
selected_province = st.radio(
    "Filter by Province", provinces,
    index=0,
    horizontal=True
)
if selected_province == "All":
    ptso_sel = ptso_options
else:
    ptso_sel = [selected_province]

# ─── 1) Provincial summary metrics ──────────────────────────
sql_base = """
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
  AND club_name = ANY(%(names)s);
"""
df_base = pd.read_sql(
    sql_base,
    engine,
    params={
        "season": season,
        "ptso":   ptso_sel,
        "status": status_sel,
        "names":  club_sel
    }
)
if df_base.empty:
    st.warning(f"No data found for season {season} with the selected filters.")
    st.stop()

#  ── aggregate totals ───────────────────────────────────────
active_clubs = df_base["club_id"].nunique()
total_skiers = df_base["skiers"].sum()

#  ── coaches: min / max / mode ─────────────────────────────
min_coaches  = int(df_base["coaches"].min())
max_coaches  = int(df_base["coaches"].max())
mode_coaches = int(df_base["coaches"].mode().iloc[0]) if not df_base["coaches"].mode().empty else 0

#  ── new coach-related metrics ─────────────────────────────
total_evals           = df_base["evaluations_completed"].sum()
avg_evals_per_coach   = total_evals / (df_base["coaches"].sum() or 1)
total_drills          = df_base["drills_shared"].sum()
avg_drills_per_skier  = total_drills / (total_skiers or 1)

#  ── render updated KPI cards ───────────────────────────────
st.markdown(f"""
<div class="stats-row">
  <div class="stat-card"><p>Active Clubs</p><h2>{active_clubs:,}</h2></div>
  <div class="stat-card"><p>Total Skiers</p><h2>{total_skiers:,}</h2></div>
  <div class="stat-card"><p>Coaches (min/max/mode)</p><h2>{min_coaches}/{max_coaches}/{mode_coaches}</h2></div>
  <div class="stat-card"><p>Avg Evals per Coach</p><h2>{avg_evals_per_coach:.1f}</h2></div>
  <div class="stat-card"><p>Avg Drills per Skier</p><h2>{avg_drills_per_skier:.2f}</h2></div>
</div>
""", unsafe_allow_html=True)

from pyecharts.options import DataZoomOpts

# ─── Dynamic Skier‐Count Bar Chart (all items) ───────────────────
if len(ptso_sel) == 1:
    # single province → list every club in that province
    province = ptso_sel[0]
    sql_chart = """
    SELECT
      club_name      AS label,
      SUM(skiers)    AS value
    FROM public.vw_club_summary_by_season
    WHERE season = %(season)s
      AND ptso   = %(province)s
      AND status = ANY(%(status)s)
    GROUP BY club_name
    ORDER BY value DESC;
    """
    params = {"season": season, "province": province, "status": status_sel}
    title  = f"All Clubs in {province} by Skier Count"
else:
    # multiple/all provinces → list every province
    sql_chart = """
    SELECT
      ptso            AS label,
      SUM(skiers)     AS value
    FROM public.vw_club_summary_by_season
    WHERE season    = %(season)s
      AND ptso      = ANY(%(ptso)s)
      AND status    = ANY(%(status)s)
      AND club_name = ANY(%(names)s)
    GROUP BY ptso
    ORDER BY value DESC;
    """
    params = {"season": season, "ptso": ptso_sel, "status": status_sel, "names": club_sel}
    title  = "All Provinces by Skier Count"

df_chart = pd.read_sql(sql_chart, engine, params=params)

st.subheader(title)
if not df_chart.empty:
    bar = (
        Bar(init_opts=opts.InitOpts(width="100%", height="600px", bg_color="#111111"))
        .add_xaxis(df_chart["label"].tolist())
        .add_yaxis("Skiers",    df_chart["value"].tolist(), category_gap="30%")
        .reversal_axis()
        .set_series_opts(label_opts=opts.LabelOpts(position="right", color="#ffffff"))
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {"title": "Save"},
                "restore":     {"title": "Reset"}
            })
        )
    )
    html(bar.render_embed(), height=600, scrolling=False)
else:
    st.info("No data to display for the current selection.")


# ─── Total Evaluations by Province/Club ───────────────────────────
if len(ptso_sel) == 1:
    # single province -> show total evaluations per club
    province = ptso_sel[0]
    sql_eval_chart = """
    SELECT
      club_name AS label,
      SUM(evaluations_completed) AS value
    FROM public.vw_national_summary_by_season
    WHERE season = %(season)s
      AND ptso   = %(province)s
      AND status = ANY(%(status)s)
    GROUP BY club_name
    ORDER BY value DESC;
    """
    params = {"season": season, "province": province, "status": status_sel}
    title = f"Total Evaluations by Club in {province}"
else:
    # multiple/all provinces -> show total evaluations per province
    sql_eval_chart = """
    SELECT
      ptso          AS label,
      SUM(evaluations_completed) AS value
    FROM public.vw_national_summary_by_season
    WHERE season    = %(season)s
      AND ptso      = ANY(%(ptso)s)
      AND status    = ANY(%(status)s)
      AND club_name = ANY(%(names)s)
    GROUP BY ptso
    ORDER BY value DESC;
    """
    params = {"season": season, "ptso": ptso_sel, "status": status_sel, "names": club_sel}
    title = "Total Evaluations by Province"

_df_eval_chart = pd.read_sql(sql_eval_chart, engine, params=params)

st.subheader(title)
if not _df_eval_chart.empty:
    bar_eval = (
        Bar(init_opts=opts.InitOpts(width="80%", height="600px", theme=ThemeType.LIGHT))
        .add_xaxis(_df_eval_chart["label"].tolist())
        .add_yaxis("Evaluations", _df_eval_chart["value"].tolist(), category_gap="30%")
        .reversal_axis()
        .set_series_opts(label_opts=opts.LabelOpts(position="insideRight", formatter="{c}"))
        .set_global_opts(
      
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            yaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(color="#ffffff")),
            toolbox_opts=opts.ToolboxOpts(feature={
                "saveAsImage": {"title": "Save"},
                "restore":     {"title": "Reset"}
            })
        )
    )
    html(bar_eval.render_embed(), height=600, scrolling=False)
else:
    st.info("No evaluation data to display for the current selection.")

# ─── Pass-Rate % by Level ─────────────────────────────────────
st.subheader("Pass-Rate % by Level")
sql_pass_rate = """
SELECT
  level_id,
  level_name,
  ROUND(SUM(eval_passed)::numeric / NULLIF(SUM(eval_total),0) * 100, 1) AS pass_pct
FROM public.vw_evaluations_by_level_by_season
WHERE season = %(season)s
  AND ptso   = ANY(%(ptso)s)
  AND club_name = ANY(%(names)s)
GROUP BY level_id, level_name;
"""
_df_pass = pd.read_sql(sql_pass_rate, engine, params={"season": season, "ptso": ptso_sel, "names": club_sel})

raw_ids     = [1, 34, 35, 36, 37, 38, 67, 68]
order_map   = {rid: idx for idx, rid in enumerate(raw_ids, start=1)}
label_map   = {rid: f"Level {i}" for i, rid in enumerate(raw_ids, start=1)}
_df_pass["sort_ord"]      = _df_pass["level_id"].map(order_map)
_df_pass["display_level"] = _df_pass["level_id"].map(label_map)
_df_pass = _df_pass[_df_pass["sort_ord"].notna()].sort_values("sort_ord")

if _df_pass.empty:
    st.info("No pass-rate data for the selected filters.")
else:
    data_pairs = list(zip(_df_pass["display_level"].tolist(), _df_pass["pass_pct"].tolist()))
pie_pass = (
    Pie(init_opts=opts.InitOpts(width="100%", height="600px"))
    .add(
        "Pass %",
        data_pairs,
        radius=["15%", "65%"],
        center=["55%", "50%"],
        rosetype="radius",
        label_opts=opts.LabelOpts(
            formatter="{b}\n{c} %",
            position="outside",
            font_size=14,        # ↑ increase font size
            font_weight="bold",  # ↑ make text bold
            color="#ffffff"      # ↑ set label color
        ),
    )
    .set_global_opts(
        legend_opts=opts.LegendOpts(
            orient="vertical",
            pos_left="left",
            textstyle_opts=opts.TextStyleOpts(
                color="#ffffff",
                font_size=14      # ↑ increase legend font size too
            )
        ),
        toolbox_opts=opts.ToolboxOpts(
            feature={
                "saveAsImage": {"title": "Save"},
                "restore": {"title": "Reset"},
            }
        )
    )
)

html(pie_pass.render_embed(), height=600, scrolling=False)

# ─── User Activity & Retention by Province ─────────────────────
st.subheader("User Activity & Retention by Province")
sql_activity = """
WITH
  signups AS (
    SELECT date_trunc('month', u.created_at)::date AS month, c.ptso AS province, COUNT(u.id) AS signups
    FROM users u JOIN clubs c ON c.id = u.club_id
    WHERE u.created_at >= date_trunc('year', CURRENT_DATE) AND c.ptso = ANY(%(ptso)s) AND c.name = ANY(%(names)s)
    GROUP BY 1,2
  ),
  actives AS (
    SELECT date_trunc('month', u.last_login)::date AS month, c.ptso AS province, COUNT(DISTINCT u.id) AS active_users
    FROM users u JOIN clubs c ON c.id = u.club_id
    WHERE u.last_login >= date_trunc('year', CURRENT_DATE) AND c.ptso = ANY(%(ptso)s) AND c.name = ANY(%(names)s)
    GROUP BY 1,2
  )
SELECT s.month, s.province, s.signups, COALESCE(a.active_users,0) AS active_users
FROM signups s LEFT JOIN actives a ON s.month=a.month AND s.province=a.province ORDER BY s.month;
"""
_df_activity = pd.read_sql(sql_activity, engine, params={"ptso": ptso_sel, "names": club_sel})
_df_activity["month"] = pd.to_datetime(_df_activity["month"])

if _df_activity.empty:
    st.info("No activity data for the current filters.")
else:
    df_tot = _df_activity.groupby("month", as_index=False)[["signups","active_users"]].sum().sort_values("month")
    months = df_tot["month"].dt.strftime("%Y-%m").tolist()
    signups = df_tot["signups"].tolist()
    active  = df_tot["active_users"].tolist()
    line = (
        Line(init_opts=opts.InitOpts(width="100%", height="500px"))
        .add_xaxis(months)
        .add_yaxis("Sign-ups", signups, yaxis_index=0, label_opts=opts.LabelOpts(is_show=False))
        .extend_axis(yaxis=opts.AxisOpts(name="Active Users", position="right", axislabel_opts=opts.LabelOpts(color="#ffffff"), axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color="#ffffff"))))
        .add_yaxis("Active Users", active, yaxis_index=1, label_opts=opts.LabelOpts(is_show=False))
        .set_series_opts(linestyle_opts=opts.LineStyleOpts(width=3), label_opts=opts.LabelOpts(color="#ffffff"))
        .set_global_opts(xaxis_opts=opts.AxisOpts(type_="category", axislabel_opts=opts.LabelOpts(color="#ffffff")), yaxis_opts=opts.AxisOpts(name="Sign-ups", axislabel_opts=opts.LabelOpts(color="#ffffff"), axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color="#ffffff"))), legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color="#ffffff")), tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"), toolbox_opts=opts.ToolboxOpts(feature={"saveAsImage": {"title": "Save"}, "restore": {"title": "Reset"}}))
        )
    html(line.render_embed(), height=500, scrolling=False)

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

    gb = GridOptionsBuilder.from_dataframe(df_display)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, flex=1)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    grid_options = gb.build()

    st.markdown('<div style="position: relative; left:50%; transform: translateX(-50%); width:100vw; overflow-x:auto;">', unsafe_allow_html=True)
    AgGrid(
        df_display,
        gridOptions=grid_options,
        theme="streamlit",
        height=1000,
        fit_columns_on_grid_load=True
    )
    st.markdown("</div>", unsafe_allow_html=True)
