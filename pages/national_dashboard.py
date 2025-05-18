import streamlit as st
import pandas as pd
import base64
import plotly.express as px
from utils.db import engine

# ─── Page config ───────────────────────────────────────────
st.set_page_config(
    page_title="National Dashboard",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Constrain max width & zoom ────────────────────────────
st.markdown(
    """
    <style>
      /* cap dashboard at 1440px and center */
      .reportview-container .main .block-container {
        max-width: 1440px;
        margin: auto;
      }
      /* force 75% zoom to fit deployed view */
      html, body, .reportview-container .main .block-container {
        zoom: 0.75 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── CSS for banner & metric cards ─────────────────────────
st.markdown("""<style>
.header-banner { display: flex; align-items: center; gap: 1rem;
  background-color: #d32f2f; color: white; padding: 1rem 2rem;
  border-radius: 8px; margin-bottom: 2rem; }
.stats-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.stat-card { flex: 1; background-color: #393939;
  padding: 1.5rem; border-radius: 8px; text-align: center; }
.stat-card p { margin: 0; font-size: 1.1rem; color: #bbbbbb;
  text-transform: uppercase; letter-spacing: 0.05em; }
.stat-card h2 { margin: 0.5rem 0 0; font-size: 2.5rem;
  font-weight: bold; color: #fafafa; }
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
season = st.sidebar.selectbox("Select Season", ["2024/2025"])

ptso_df = pd.read_sql(
    "SELECT DISTINCT ptso FROM public.vw_club_summary_by_season WHERE season=%(s)s ORDER BY ptso",
    engine, params={"s": season}
)
selected_ptso = st.sidebar.multiselect(
    "Filter by PTSO",
    options=ptso_df["ptso"].dropna().tolist(),
    default=ptso_df["ptso"].dropna().tolist()
)

selected_status = st.sidebar.multiselect(
    "Filter by Status",
    options=["Active", "Inactive"],
    default=["Active", "Inactive"]
)

names_df = pd.read_sql(
    "SELECT DISTINCT club_name FROM public.vw_club_summary_by_season WHERE season=%(s)s ORDER BY club_name",
    engine, params={"s": season}
)
selected_name = st.sidebar.multiselect(
    "Filter by Club Name",
    options=names_df["club_name"].tolist(),
    default=names_df["club_name"].tolist()
)

# ─── 1) Summary metrics ────────────────────────────────────
df_sum = pd.read_sql(
    """
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
    """,
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
df_dist = pd.read_sql(
    """
    SELECT level_name, SUM(skier_count) AS skier_count
    FROM public.vw_skier_level_distribution_by_season
    WHERE season=%(s)s AND ptso=ANY(%(ptso)s) AND club_name=ANY(%(names)s)
    GROUP BY level_id, level_name ORDER BY level_id;
    """,
    engine, params={"s": season, "ptso": selected_ptso, "names": selected_name}
)

df_eval = pd.read_sql(
    """
    SELECT level_name, SUM(eval_count) AS eval_count
    FROM public.vw_evaluations_by_level_by_season
    WHERE season=%(s)s AND ptso=ANY(%(ptso)s) AND club_name=ANY(%(names)s)
    GROUP BY level_id, level_name ORDER BY level_id;
    """,
    engine, params={"s": season, "ptso": selected_ptso, "names": selected_name}
)

# split evenly half/half
col_pie, col_bar = st.columns(2, gap="large")

with col_pie:
    st.subheader("Skier Level Distribution")
    if df_dist.empty:
        st.info("No level-distribution data for the selected filters.")
    else:
        pie_fig = px.pie(
            df_dist,
            names="level_name",
            values="skier_count",
            hole=0.4
        )
        pie_fig.update_layout(
            paper_bgcolor="#111111",
            plot_bgcolor="#111111",
            font_color="#ffffff",
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(pie_fig, use_container_width=True)

with col_bar:
    st.subheader("Evaluations by Level")
    if df_eval.empty:
        st.info("No evaluations data for the selected filters.")
    else:
        bar_fig = px.bar(
            df_eval,
            x="level_name",
            y="eval_count",
            labels={"eval_count": "Count", "level_name": ""}
        )
        bar_fig.update_layout(
            paper_bgcolor="#111111",
            plot_bgcolor="#111111",
            font_color="#ffffff",
            margin=dict(t=20, b=20, l=20, r=20),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(bar_fig, use_container_width=True)

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

# ─── Clubs header + search + CSV download + full-width table ─
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

    # Download CSV
    csv = df_display.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"clubs_{season.replace('/', '-')}.csv",
        mime="text/csv",
        key="download-clubs"
    )

    # Full-width, container-wide table
    st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=False,
        height=600,
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
