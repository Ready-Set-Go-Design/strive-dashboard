import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

# —— Page Configuration ——
st.set_page_config(
    page_title="Dashboard Title",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable("dark")

# —— CSS Styling ——
st.markdown(
    """
    <style>
    [data-testid="block-container"] { padding:2rem 2rem 0 2rem; }
    [data-testid="stVerticalBlock"] { padding:0; }
    [data-testid="stMetric"] { background:#393939; text-align:center; padding:15px 0; }
    [data-testid="stMetricLabel"]{ display:flex; justify-content:center; align-items:center; }
    [data-testid="stMetricDeltaIcon-Up"], [data-testid="stMetricDeltaIcon-Down"] {
      position: relative; left: 38%; transform: translateX(-50%);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# —— Data Placeholders ——
# df_main = pd.DataFrame()  # Replace with actual data loading

# —— Sidebar Filters ——
with st.sidebar:
    st.title("Dashboard Filters")
    # Example filters:
    # date_range = st.date_input("Select Date Range")
    # category = st.selectbox("Select Category", ["A", "B", "C"])

# —— Helper Chart Functions ——
def make_bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    """Return a Plotly bar chart."""
    # fig = px.bar(df, x=x, y=y, title=title)
    # return fig
    pass


def make_pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    """Return an Altair pie chart."""
    # fig = alt.Chart(df).mark_arc().encode(theta=f"{values}:Q", color=f"{names}:N").properties(title=title)
    # return fig
    pass


def make_heatmap(df: pd.DataFrame, x: str, y: str, color: str):
    """Return an Altair heatmap."""
    # heatmap = alt.Chart(df).mark_rect().encode(x=f"{x}:O", y=f"{y}:O", color=f"{color}:Q")
    # return heatmap
    pass

# —— Main Layout ——
col1, col2, col3 = st.columns((1.5, 4.5, 2), gap="medium")

with col1:
    st.subheader("Section 1")
    # st.metric(label="Metric A", value="Value A", delta="Delta A")

with col2:
    st.subheader("Section 2")
    # fig = make_bar_chart(df_main, x="x_col", y="y_col", title="Bar Chart")
    # st.plotly_chart(fig, use_container_width=True)

with col3:
    st.subheader("Section 3")
    # fig = make_pie_chart(df_main, names="category", values="value", title="Pie Chart")
    # st.altair_chart(fig, use_container_width=True)

# —— Footer or Raw Data ——
# if st.checkbox("Show raw data"):
#     st.dataframe(df_main)
