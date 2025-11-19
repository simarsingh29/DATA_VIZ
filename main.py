import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

@st.cache_data
def load_data():
    matches = pd.read_csv("matches (2).csv")  # FIXED
    matches.columns = matches.columns.str.strip().str.lower().str.replace(" ", "_")

    deliveries = pd.read_excel("deliveries_1.csv")
    deliveries.columns = deliveries.columns.str.strip().str.lower().str.replace(" ", "_")

    return matches, deliveries


matches, deliveries = load_data()

# Fix inconsistent column names
if "match_winner" in matches.columns:
    matches.rename(columns={"match_winner": "winner"}, inplace=True)

if "team_1" in matches.columns:
    matches.rename(columns={"team_1": "team1"}, inplace=True)

if "team_2" in matches.columns:
    matches.rename(columns={"team_2": "team2"}, inplace=True)

if "date" in matches.columns:
    matches["date"] = pd.to_datetime(matches["date"], errors="ignore")


st.title("🏏 IPL Analytics Dashboard")

st.markdown("""
Interactive dashboard using IPL match and ball-by-ball data.  
Use the sidebar filters & tabs to explore teams, players, venues, and seasons.
""")

# Sidebar -------------------------------------
st.sidebar.header("Filters")

# Seasons
seasons = sorted(matches["season"].dropna().unique()) if "season" in matches.columns else []
selected_seasons = st.sidebar.multiselect("Select Seasons", seasons, default=seasons)

# Validate team columns
required = {"team1", "team2", "winner"}
if not required.issubset(matches.columns):
    st.error("❌ Required team columns missing!")
    st.write("Columns found:", matches.columns.tolist())
    st.stop()

# Teams
teams = sorted(pd.unique(pd.concat([matches["team1"], matches["team2"], matches["winner"]]).dropna()))
selected_team = st.sidebar.selectbox("Select Team (optional)", ["All"] + teams)

# Filter by seasons
matches_f = matches[matches["season"].isin(selected_seasons)] if selected_seasons else matches

# Validate ID column
if "id" not in matches_f.columns:
    st.error("❌ Column 'id' missing in matches.csv")
    st.write("Available columns:", matches_f.columns.tolist())
    st.stop()

deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

# TABS -----------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Team Analysis", "Batting", "Bowling"])

# TAB 1 - Overview -----------------------------
with tab1:
    st.subheader("Overall Tournament Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Matches", len(matches_f))
    col2.metric("Seasons", matches_f["season"].nunique())
    col3.metric("Venues", matches_f["venue"].nunique() if "venue" in matches_f.columns else 0)
    col4.metric("Teams", len(teams))

    if "season" in matches_f.columns:
        mps = matches_f.groupby("season")["id"].count().reset_index()
