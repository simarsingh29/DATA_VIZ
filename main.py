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

# =======================================================
# LOAD DATA SAFELY
# =======================================================
@st.cache_data
def load_data():

    # --- Load Matches File ---
    try:
        matches = pd.read_csv("matches (2).csv")
    except:
        matches = pd.read_csv("matches (2).csv", header=None)

    # If only 1 column → CSV is corrupted → split manually
    if matches.shape[1] == 1:
        matches = matches.iloc[:, 0].str.split(",", expand=True)

    # Assign correct IPL columns
    matches.columns = [
        "id","season","city","date","match_type","player_of_match","venue","team1","team2",
        "toss_winner","toss_decision","winner","result","result_margin","target_runs",
        "target_overs","super_over","method","umpire1","umpire2"
    ]

    # Clean column names
    matches.columns = matches.columns.str.strip().str.lower()

    # Convert date to datetime
    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")

    # ---------------- DELIVERIES ----------------
    deliveries = pd.read_csv("deliveries.csv")
    deliveries.columns = deliveries.columns.str.strip().str.lower()

    return matches, deliveries


# LOAD CLEANED DATA
matches, deliveries = load_data()

# =======================================================
# MAIN UI
# =======================================================
st.title("🏏 IPL Analytics Dashboard")

st.markdown("""
Interactive dashboard using IPL match and ball-by-ball data.  
Use the sidebar filters & tabs to explore teams, players, venues, and seasons.
""")

# Sidebar -------------------------------
st.sidebar.header("Filters")

seasons = sorted(matches["season"].dropna().unique())
selected_seasons = st.sidebar.multiselect("Select Seasons", seasons, default=seasons)

teams = sorted(
    pd.unique(
        pd.concat([matches["team1"], matches["team2"], matches["winner"]]).dropna()
    )
)

selected_team = st.sidebar.selectbox("Focus Team (optional)", ["All"] + teams)

# Season filter
matches_f = matches[matches["season"].isin(selected_seasons)]
deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Team Analysis", "Batting Analysis", "Bowling Analysis"]
)

# =======================================================
# TAB 1: OVERVIEW
# =======================================================
with tab1:
    st.subheader("Overall Tournament Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Matches", len(matches_f))
    col2.metric("Seasons", matches_f["season"].nunique())
    col3.metric("Venues", matches_f["venue"].nunique())
    col4.metric("Teams", len(teams))

    # Matches per season
    mps = matches_f.groupby("season")["id"].count().reset_index()
    fig_mps = px.bar(
        mps, x="season", y="id", title="Matches per Season", text="id"
    )
    fig_mps.update_traces(textposition="outside")
    st.plotly_chart(fig_mps, use_container_width=True)

    # Toss decision
    toss_counts = matches_f["toss_decision"].value_counts().reset_index()
    toss_counts.columns = ["decision", "count"]
    fig_toss = px.pie(
        toss_counts, names="decision", values="count",
        title="Toss Decision (Bat vs Field)", hole=0.4
    )
    st.plotly_chart(fig_toss, use_container_width=True)

    # Result type
    res_counts = matches_f["result"].value_counts().reset_index()
    res_counts.columns = ["result", "count"]
    fig_res = px.bar(
        res_counts, x="result", y="count",
        text="count", title="Types of Match Results"
    )
    fig_res.update_traces(textposition="outside")
    st.plotly_chart(fig_res, use_container_width=True)

# =======================================================
# TAB 2: TEAM ANALYSIS
# =======================================================
with tab2:
    st.subheader("Team Performance Analysis")

    # Matches played by each team
    t1 = matches_f.groupby("team1")["id"].count().reset_index()
    t1.columns = ["team", "matches_home"]

    t2 = matches_f.groupby("team2")["id"].count().reset_index()
    t2.columns = ["team", "matches_away"]

    team_matches = pd.merge(t1, t2, on="team", how="outer").fillna(0)
    team_matches["matches_played"] = team_matches["matches_home"] + team_matches["matches_away"]

    # Wins
    wins = matches_f.groupby("winner")["id"].count().reset_index()
    wins.columns = ["team", "wins"]

    team_stats = pd.merge(team_matches, wins, on="team", how="left").fillna(0)
    team_stats["win_pct"] = (team_stats["wins"] / team_stats["matches_played"] * 100).round(2)
    team_stats = team_stats.sort_values("wins", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_tw = px.bar(team_stats, x="team", y="wins", text="wins", title="Total Wins by Team")
        fig_tw.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_tw, use_container_width=True)

    with col2:
        fig_wp = px.bar(team_stats, x="team", y="win_pct", text="win_pct",
                        title="Win Percentage by Team")
        fig_wp.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_wp, use_container_width=True)

# =======================================================
# TAB 3: BATTING ANALYSIS
# =======================================================
with tab3:
    st.subheader("Batting Analysis")

    if {"batter", "batsman_runs"}.issubset(deliveries_f.columns):

        bat = deliveries_f.groupby("batter")["batsman_runs"].sum().reset_index()
        bat = bat.sort_values("batsman_runs", ascending=False)

        top_n = st.slider("Top N batters", 5, 30, 10)
        top_bat = bat.head(top_n)

        fig_bat = px.bar(
            top_bat, x="batter", y="batsman_runs",
            text="batsman_runs", title=f"Top {top_n} Run Scorers"
        )
        fig_bat.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bat, use_container_width=True)

# =======================================================
# TAB 4: BOWLING ANALYSIS
# =======================================================
with tab4:
    st.subheader("Bowling Analysis")

    needed = {"bowler", "is_wicket", "dismissal_kind", "total_runs"}
    if needed.issubset(deliveries_f.columns):

        wk = deliveries_f[
            (deliveries_f["is_wicket"] == 1) &
            (~deliveries_f["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"]))
        ]

        bow = wk.groupby("bowler")["is_wicket"].count().reset_index()
        bow.columns = ["bowler", "wickets"]
        bow = bow.sort_values("wickets", ascending=False)

        top_n = st.slider("Top N bowlers", 5, 30, 10)
        top_bowl = bow.head(top_n)

        fig_bowl = px.bar(top_bowl, x="bowler", y="wickets",
                          text="wickets", title=f"Top {top_n} Wicket Takers")
        fig_bowl.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bowl, use_container_width=True)
