import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------
# STREAMLIT CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide"
)

# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------
@st.cache_data
def load_data():
    # Correct filenames from your GitHub repo
    matches = pd.read_csv("matches (2).csv")
    deliveries = pd.read_csv("deliveries.csv")

    # Clean column names
    matches.columns = matches.columns.str.strip().str.lower().str.replace(" ", "_")
    deliveries.columns = deliveries.columns.str.strip().str.lower().str.replace(" ", "_")

    # Fix common inconsistencies
    rename_map = {
        "match_winner": "winner",
        "team_1": "team1",
        "team_2": "team2"
    }
    matches.rename(columns={k: v for k, v in rename_map.items() if k in matches.columns}, inplace=True)

    # Ensure date column is properly parsed
    if "date" in matches.columns:
        matches["date"] = pd.to_datetime(matches["date"], errors="ignore")

    return matches, deliveries


matches, deliveries = load_data()

# ----------------------------------------------------
# VALIDATION
# ----------------------------------------------------
required_match_cols = {"team1", "team2", "winner", "season", "id"}
if not required_match_cols.issubset(matches.columns):
    st.error("❌ Required columns missing in matches CSV")
    st.write("Columns available:", matches.columns.tolist())
    st.stop()

if "match_id" not in deliveries.columns:
    st.error("❌ Column 'match_id' missing in deliveries.csv")
    st.write("Available columns:", deliveries.columns.tolist())
    st.stop()

# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.title("🏏 IPL Analytics Dashboard")
st.markdown("""
Explore IPL matches, teams, players, and venue statistics using interactive visual analytics.
""")

# ----------------------------------------------------
# SIDEBAR FILTERS
# ----------------------------------------------------
st.sidebar.header("Filters")

# Seasons
seasons = sorted(matches["season"].dropna().unique())
selected_seasons = st.sidebar.multiselect("Select Seasons", seasons, default=seasons)

# Filter matches season-wise
matches_f = matches[matches["season"].isin(selected_seasons)]

# Teams
teams = sorted(pd.unique(pd.concat([matches["team1"], matches["team2"], matches["winner"]]).dropna()))
selected_team = st.sidebar.selectbox("Select Team (optional)", ["All"] + teams)

# Filter deliveries based on filtered matches
deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

# ----------------------------------------------------
# TABS
# ----------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Team Analysis", "Batting", "Bowling"])

# ----------------------------------------------------
# TAB 1 — OVERVIEW
# ----------------------------------------------------
with tab1:
    st.subheader("📊 Tournament Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Matches", len(matches_f))
    col2.metric("Total Seasons", matches_f["season"].nunique())
    col3.metric("Venues Used", matches_f["venue"].nunique() if "venue" in matches.columns else "--")
    col4.metric("Total Teams", len(teams))

    # Matches per season chart
    mps = matches_f.groupby("season")["id"].count().reset_index()

    fig = px.bar(
        mps,
        x="season",
        y="id",
        title="Matches Played Each Season",
        color="id",
        labels={"id": "Matches"},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# TAB 2 — TEAM ANALYSIS
# ----------------------------------------------------
with tab2:
    st.subheader("🏏 Team Analysis")

    if selected_team != "All":
        team_matches = matches_f[(matches_f["team1"] == selected_team) | (matches_f["team2"] == selected_team)]

        wins = (team_matches["winner"] == selected_team).sum()
        total = len(team_matches)

        st.metric(f"{selected_team} — Win Percentage", f"{(wins/total)*100:.2f}%" if total > 0 else "N/A")

        win_df = team_matches.groupby("season").apply(lambda x: (x["winner"] == selected_team).sum()).reset_index(name="wins")

        fig = px.line(
            win_df,
            x="season",
            y="wins",
            markers=True,
            title=f"{selected_team} — Wins Per Season",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a team from the sidebar to view detailed team analysis.")

# ----------------------------------------------------
# TAB 3 — BATTING ANALYSIS
# ----------------------------------------------------
with tab3:
    st.subheader("🏏 Batting Performance")

    if "batsman" in deliveries.columns:
        batsman_runs = deliveries_f.groupby("batsman")["batsman_runs"].sum().sort_values(ascending=False).head(20)

        fig = px.bar(
            batsman_runs,
            x=batsman_runs.values,
            y=batsman_runs.index,
            orientation="h",
            title="Top 20 Run Scorers",
            labels={"x": "Runs", "y": "Batsman"},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Batsman column missing from deliveries data.")

# ----------------------------------------------------
# TAB 4 — BOWLING ANALYSIS
# ----------------------------------------------------
with tab4:
    st.subheader("🔥 Bowling Impact Analysis")

    if {"bowler", "is_wicket"} <= set(deliveries.columns):
        wickets = deliveries_f[deliveries_f["is_wicket"] == 1]

        bowler_wkts = wickets.groupby("bowler")["is_wicket"].count().sort_values(ascending=False).head(20)

        fig = px.bar(
            bowler_wkts,
            x=bowler_wkts.values,
            y=bowler_wkts.index,
            orientation="h",
            title="Top 20 Wicket Takers",
            labels={"x": "Wickets", "y": "Bowler"},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Required bowling columns missing in deliveries data.")
