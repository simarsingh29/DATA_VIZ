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

    deliveries = pd.read_csv("deliveries.csv")
    deliveries.columns = deliveries.columns.str.strip().str.lower().str.replace(" ", "_")

    return matches, deliveries





matches, deliveries = load_data()

# --- Required Column Fixing ---

# Some datasets use "winner", others "match_winner"
if "winner" not in matches.columns and "match_winner" in matches.columns:
    matches.rename(columns={"match_winner": "winner"}, inplace=True)

# Some Excel files use "team1" / "team_1" or "team_1_name"
team_cols = [c for c in matches.columns if "team1" in c]
if team_cols:
    matches.rename(columns={team_cols[0]: "team1"}, inplace=True)

team_cols2 = [c for c in matches.columns if "team2" in c]
if team_cols2:
    matches.rename(columns={team_cols2[0]: "team2"}, inplace=True)

# Ensure date parsing if exists
if "date" in matches.columns:
    matches["date"] = pd.to_datetime(matches["date"], errors="ignore")

st.title("🏏 IPL Analytics Dashboard")

st.markdown("""
Interactive dashboard using IPL match and ball-by-ball data.  
Use the sidebar filters & tabs to explore teams, players, venues, and seasons.
""")

# -----------------------------------------------
# SIDEBAR
# -----------------------------------------------
st.sidebar.header("Filters")

# Seasons
seasons = sorted(matches["season"].dropna().unique()) if "season" in matches.columns else []
selected_seasons = st.sidebar.multiselect("Select Seasons", options=seasons, default=seasons)

# TEAMS FIX — Prevent KeyError
team_cols_required = {"team1", "team2", "winner"}
if not team_cols_required.issubset(matches.columns):
    st.error("❌ Team columns missing in matches dataset.")
    st.write("Available columns:", matches.columns.tolist())
    st.stop()

# Combine all teams
teams = sorted(pd.unique(pd.concat([matches["team1"], matches["team2"], matches["winner"]]).dropna()))

selected_team = st.sidebar.selectbox("Focus Team (optional)", ["All"] + teams)

# Filter matches by season
if selected_seasons:
    matches_f = matches[matches["season"].isin(selected_seasons)]
else:
    matches_f = matches.copy()

if "id" not in matches_f.columns:
    st.error("Column 'id' not found in matches dataset! Fix your Excel structure.")
    st.write("Available columns:", matches_f.columns.tolist())
    st.stop()

deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

# -----------------------------------------------
# TABS
# -----------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Team Analysis", "Batting", "Bowling"])

# ------------------------ TAB 1 ----------------------------
with tab1:
    st.subheader("Overall Tournament Overview")

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Matches", len(matches_f))
    col2.metric("Seasons", matches_f["season"].nunique())
    col3.metric("Venues", matches_f["venue"].nunique() if "venue" in matches_f.columns else 0)
    col4.metric("Teams", len(teams))

    # Matches per season
    if "season" in matches_f.columns:
        mps = matches_f.groupby("season")["id"].count().reset_index()
        fig = px.bar(mps, x="season", y="id", title="Matches per Season", text="id")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------ TAB 2 ----------------------------
with tab2:
    st.subheader("Team Performance Analysis")

    # Team matches home/away
    t1 = matches_f.groupby("team1")["id"].count().reset_index().rename(columns={"team1": "team", "id": "home"})
    t2 = matches_f.groupby("team2")["id"].count().reset_index().rename(columns={"team2": "team", "id": "away"})
    tw = matches_f.groupby("winner")["id"].count().reset_index().rename(columns={"winner": "team", "id": "wins"})

    team_stats = t1.merge(t2, on="team", how="outer").merge(tw, on="team", how="left").fillna(0)
    team_stats["played"] = team_stats["home"] + team_stats["away"]
    team_stats["win_pct"] = (team_stats["wins"] / team_stats["played"]) * 100

    fig1 = px.bar(team_stats.sort_values("wins", ascending=False), x="team", y="wins",
                  title="Wins by Team", text="wins")
    st.plotly_chart(fig1, use_container_width=True)

# ------------------------ TAB 3 ----------------------------
with tab3:
    st.subheader("Batting Analysis")

    if {"batter", "batsman_runs"}.issubset(deliveries_f.columns):
        bat = deliveries_f.groupby("batter")["batsman_runs"].sum().reset_index()
        bat = bat.sort_values("batsman_runs", ascending=False)
        fig = px.bar(bat.head(20), x="batter", y="batsman_runs", text="batsman_runs",
                      title="Top Batters")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Batting columns missing in deliveries!")

# ------------------------ TAB 4 ----------------------------
with tab4:
    st.subheader("Bowling Analysis")

    if {"bowler", "is_wicket", "dismissal_kind"}.issubset(deliveries_f.columns):
        wk = deliveries_f[
            (deliveries_f["is_wicket"] == 1) &
            (~deliveries_f["dismissal_kind"].isin(["run out", "retired hurt"]))
        ]
        bowl = wk.groupby("bowler")["is_wicket"].count().reset_index().sort_values("is_wicket", ascending=False)
        fig = px.bar(bowl.head(20), x="bowler", y="is_wicket", title="Top Bowlers", text="is_wicket")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Bowling columns missing in deliveries!")
