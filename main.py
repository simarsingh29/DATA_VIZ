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

# @st.cache_data
# def load_data():
#     matches = pd.read_csv("matches (2).csv")
#     deliveries = pd.read_csv("deliveries.csv")
#     return matches, deliveries

# matches, deliveries = load_data()
@st.cache_data
def load_data():
    # --- Load Matches File ---
    try:
        matches = pd.read_csv("matches (2).csv")
    except:
        matches = pd.read_csv("matches (2).csv", header=None)

    # Fix: If only ONE column exists → it's a corrupted CSV, split it manually
    if matches.shape[1] == 1:
        matches = matches.iloc[:, 0].str.split(",", expand=True)

    # Now assign correct column names
    matches.columns = [
        "id","season","city","date","match_type","player_of_match","venue","team1","team2",
        "toss_winner","toss_decision","winner","result","result_margin","target_runs",
        "target_overs","super_over","method","umpire1","umpire2"
    ]

    # Ensure columns clean
    matches.columns = matches.columns.str.strip().str.lower()

    # --- Deliveries File ---
    deliveries = pd.read_csv("deliveries.csv")
    deliveries.columns = deliveries.columns.str.strip().str.lower()

    return matches, deliveries



if "date" in matches.columns:
    matches["date"] = pd.to_datetime(matches["date"])

st.title("🏏 IPL Analytics Dashboard")

st.markdown(
    """
Interactive dashboard using IPL match and ball-by-ball data.  
Use the sidebar filters and tabs to explore teams, players, venues and seasons.
"""
)

st.sidebar.header("Filters")

seasons = sorted(matches["season"].dropna().unique()) if "season" in matches.columns else []
selected_seasons = st.sidebar.multiselect(
    "Select Seasons",
    options=seasons,
    default=seasons
)

teams = sorted(
    pd.unique(
        pd.concat(
            [
                matches["team1"],
                matches["team2"],
                matches["winner"]
            ],
            axis=0
        ).dropna()
    )
)

selected_team = st.sidebar.selectbox(
    "Focus Team (optional)",
    options=["All"] + teams,
    index=0
)

if selected_seasons:
    matches_f = matches[matches["season"].isin(selected_seasons)]
else:
    matches_f = matches.copy()

deliveries_f = deliveries[deliveries["match_id"].isin(matches_f["id"])]

tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Team Analysis", "Batting Analysis", "Bowling Analysis"]
)

# =========================
# TAB 1: OVERVIEW
# =========================
with tab1:
    st.subheader("Overall Tournament Overview")

    col1, col2, col3, col4 = st.columns(4)
    total_matches = len(matches_f)
    total_seasons = matches_f["season"].nunique() if "season" in matches_f.columns else 0
    total_venues = matches_f["venue"].nunique() if "venue" in matches_f.columns else 0
    total_teams = len(teams)

    col1.metric("Total Matches", total_matches)
    col2.metric("Seasons", total_seasons)
    col3.metric("Venues", total_venues)
    col4.metric("Teams", total_teams)

    if "season" in matches_f.columns:
        matches_per_season = (
            matches_f.groupby("season")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "matches"})
        )
        fig_mps = px.bar(
            matches_per_season,
            x="season",
            y="matches",
            title="Matches per Season",
            text="matches"
        )
        fig_mps.update_traces(textposition="outside")
        st.plotly_chart(fig_mps, use_container_width=True)

    if "toss_decision" in matches_f.columns:
        toss_counts = matches_f["toss_decision"].value_counts().reset_index()
        toss_counts.columns = ["toss_decision", "toss_count"]
        toss_counts = toss_counts.rename(columns={"toss_decision": "decision"})

        fig_toss = px.pie(
            toss_counts,
            names="decision",
            values="toss_count",
            title="Toss Decision (Bat vs Field)",
            hole=0.4
        )
        st.plotly_chart(fig_toss, use_container_width=True)

    if "result" in matches_f.columns:
        result_counts = matches_f["result"].value_counts().reset_index()
        result_counts.columns = ["result_type", "result_count"]

        fig_res = px.bar(
            result_counts,
            x="result_type",
            y="result_count",
            title="Result Type Distribution",
            text="result_count",
            labels={"result_type": "Result", "result_count": "Count"}
        )
        fig_res.update_traces(textposition="outside")
        st.plotly_chart(fig_res, use_container_width=True)

    if "win_by_runs" in matches_f.columns and "win_by_wickets" in matches_f.columns:
        col_a, col_b = st.columns(2)

        with col_a:
            runs_wins = matches_f[matches_f["win_by_runs"] > 0].copy()
            fig_runs = px.histogram(
                runs_wins,
                x="win_by_runs",
                nbins=30,
                title="Distribution of Victory Margin (Runs)",
                labels={"win_by_runs": "Run Margin"}
            )
            st.plotly_chart(fig_runs, use_container_width=True)

        with col_b:
            wk_wins = matches_f[matches_f["win_by_wickets"] > 0].copy()
            fig_wk = px.histogram(
                wk_wins,
                x="win_by_wickets",
                nbins=10,
                title="Distribution of Victory Margin (Wickets)",
                labels={"win_by_wickets": "Wicket Margin"}
            )
            st.plotly_chart(fig_wk, use_container_width=True)

# =========================
# TAB 2: TEAM ANALYSIS
# =========================
with tab2:
    st.subheader("Team Performance Analysis")

    if selected_team == "All":
        st.markdown("Showing overall team comparison.")
    else:
        st.markdown(f"Showing statistics for {selected_team}.")

    team_matches1 = (
        matches_f.groupby("team1")["id"]
        .count()
        .reset_index()
        .rename(columns={"team1": "team", "id": "matches_home"})
    )
    team_matches2 = (
        matches_f.groupby("team2")["id"]
        .count()
        .reset_index()
        .rename(columns={"team2": "team", "id": "matches_away"})
    )
    team_matches = pd.merge(team_matches1, team_matches2, on="team", how="outer").fillna(0)
    team_matches["matches_played"] = team_matches["matches_home"] + team_matches["matches_away"]

    team_wins = (
        matches_f.groupby("winner")["id"]
        .count()
        .reset_index()
        .rename(columns={"winner": "team", "id": "wins"})
    )

    team_stats = pd.merge(team_matches, team_wins, on="team", how="left").fillna(0)
    team_stats["win_pct"] = np.where(
        team_stats["matches_played"] > 0,
        (team_stats["wins"] / team_stats["matches_played"]) * 100,
        0
    )
    team_stats = team_stats.sort_values("wins", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_team_wins = px.bar(
            team_stats,
            x="team",
            y="wins",
            title="Total Wins by Team",
            text="wins"
        )
        fig_team_wins.update_layout(xaxis_tickangle=-45)
        fig_team_wins.update_traces(textposition="outside")
        st.plotly_chart(fig_team_wins, use_container_width=True)

    with col2:
        fig_team_winpct = px.bar(
            team_stats,
            x="team",
            y="win_pct",
            title="Win Percentage by Team",
            labels={"win_pct": "Win %"},
            text="win_pct"
        )
        fig_team_winpct.update_layout(xaxis_tickangle=-45)
        fig_team_winpct.update_traces(textposition="outside")
        st.plotly_chart(fig_team_winpct, use_container_width=True)

    if selected_team != "All":
        tm_row = team_stats[team_stats["team"] == selected_team]
        if not tm_row.empty:
            total_played = int(tm_row["matches_played"].iloc[0])
            total_won = int(tm_row["wins"].iloc[0])
            win_pct_val = round(tm_row["win_pct"].iloc[0], 2)

            c1, c2, c3 = st.columns(3)
            c1.metric("Matches Played", total_played)
            c2.metric("Matches Won", total_won)
            c3.metric("Win %", win_pct_val)

    if "venue" in matches_f.columns:
        st.markdown("### Top Venues by Matches Played")

        venue_match_count = (
            matches_f.groupby("venue")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "matches"})
            .sort_values("matches", ascending=False)
        )
        top_venues = venue_match_count.head(15)

        fig_venue = px.bar(
            top_venues,
            x="venue",
            y="matches",
            title="Most Used Venues",
            text="matches"
        )
        fig_venue.update_layout(xaxis_tickangle=-60)
        fig_venue.update_traces(textposition="outside")
        st.plotly_chart(fig_venue, use_container_width=True)

        venue_sel = st.selectbox(
            "Select a Venue to see team performance there",
            options=sorted(matches_f["venue"].dropna().unique())
        )

        venue_df = matches_f[matches_f["venue"] == venue_sel]
        venue_team_wins = (
            venue_df.groupby("winner")["id"]
            .count()
            .reset_index()
            .rename(columns={"winner": "team", "id": "wins_at_venue"})
            .sort_values("wins_at_venue", ascending=False)
        )

        fig_venue_team = px.bar(
            venue_team_wins,
            x="team",
            y="wins_at_venue",
            title=f"Wins by Team at {venue_sel}",
            text="wins_at_venue"
        )
        fig_venue_team.update_layout(xaxis_tickangle=-45)
        fig_venue_team.update_traces(textposition="outside")
        st.plotly_chart(fig_venue_team, use_container_width=True)

# =========================
# TAB 3: BATTING ANALYSIS
# =========================
with tab3:
    st.subheader("Batting Analysis")

    if {"batter", "batsman_runs"}.issubset(deliveries_f.columns):
        batter_runs = (
            deliveries_f.groupby("batter")["batsman_runs"]
            .sum()
            .reset_index()
            .sort_values("batsman_runs", ascending=False)
        )

        top_n_bat = st.slider("Top N batters by runs", 5, 30, 10)
        top_batters = batter_runs.head(top_n_bat)

        top_batters = top_batters.rename(columns={"batsman_runs": "total_runs"})

        fig_top_bat = px.bar(
            top_batters,
            x="batter",
            y="total_runs",
            title=f"Top {top_n_bat} Run Scorers",
            labels={"batter": "Batter", "total_runs": "Runs"},
            text="total_runs"
        )
        fig_top_bat.update_layout(xaxis_tickangle=-45)
        fig_top_bat.update_traces(textposition="outside")
        st.plotly_chart(fig_top_bat, use_container_width=True)

        selected_batter = st.selectbox(
            "Select a batter for detailed view",
            options=top_batters["batter"]
        )

        p_df = deliveries_f[deliveries_f["batter"] == selected_batter]

        total_runs = int(p_df["batsman_runs"].sum())
        total_balls = int(p_df.shape[0])
        fours = int((p_df["batsman_runs"] == 4).sum())
        sixes = int((p_df["batsman_runs"] == 6).sum())
        strike_rate = round((total_runs / total_balls) * 100, 2) if total_balls > 0 else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Runs", total_runs)
        c2.metric("Balls", total_balls)
        c3.metric("4s", fours)
        c4.metric("6s", sixes)
        c5.metric("Strike Rate", strike_rate)

        if "season" in matches_f.columns:
            bat_season = deliveries_f.merge(
                matches_f[["id", "season"]],
                left_on="match_id",
                right_on="id",
                how="left"
            )
            bat_season = bat_season[bat_season["batter"] == selected_batter]
            bat_season_grp = (
                bat_season.groupby("season")["batsman_runs"]
                .sum()
                .reset_index()
                .sort_values("season")
            )
            bat_season_grp = bat_season_grp.rename(columns={"batsman_runs": "season_runs"})

            fig_season_runs = px.line(
                bat_season_grp,
                x="season",
                y="season_runs",
                markers=True,
                title=f"Season-wise Runs: {selected_batter}",
                labels={"season_runs": "Runs"}
            )
            st.plotly_chart(fig_season_runs, use_container_width=True)

        st.markdown("### Boundary Distribution")
        boundary_counts = pd.DataFrame({
            "boundary_type": ["4s", "6s"],
            "boundary_count": [fours, sixes]
        })
        fig_boundary = px.pie(
            boundary_counts,
            names="boundary_type",
            values="boundary_count",
            title=f"Boundary Split for {selected_batter}",
            hole=0.4
        )
        st.plotly_chart(fig_boundary, use_container_width=True)
    else:
        st.write("Required columns for batting analysis are missing in deliveries dataset.")

# =========================
# TAB 4: BOWLING ANALYSIS
# =========================
with tab4:
    st.subheader("Bowling Analysis")

    needed_cols = {"bowler", "is_wicket", "dismissal_kind", "total_runs"}
    if needed_cols.issubset(deliveries_f.columns):
        wicket_df = deliveries_f[
            (deliveries_f["is_wicket"] == 1) &
            (~deliveries_f["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"]))
        ]

        bowler_wk = (
            wicket_df.groupby("bowler")["is_wicket"]
            .count()
            .reset_index()
            .rename(columns={"is_wicket": "wickets_taken"})
            .sort_values("wickets_taken", ascending=False)
        )

        top_n_bowl = st.slider("Top N bowlers by wickets", 5, 30, 10)
        top_bowlers = bowler_wk.head(top_n_bowl)

        fig_top_bowl = px.bar(
            top_bowlers,
            x="bowler",
            y="wickets_taken",
            title=f"Top {top_n_bowl} Wicket Takers",
            labels={"bowler": "Bowler", "wickets_taken": "Wickets"},
            text="wickets_taken"
        )
        fig_top_bowl.update_layout(xaxis_tickangle=-45)
        fig_top_bowl.update_traces(textposition="outside")
        st.plotly_chart(fig_top_bowl, use_container_width=True)

        selected_bowler = st.selectbox(
            "Select a bowler for detailed view",
            options=top_bowlers["bowler"]
        )

        b_df = deliveries_f[deliveries_f["bowler"] == selected_bowler]
        if "extras_type" in b_df.columns:
            legal_del = b_df[~b_df["extras_type"].isin(["wides", "noballs"])]
        else:
            legal_del = b_df

        runs_conceded = int(b_df["total_runs"].sum())
        balls_bowled = int(legal_del.shape[0])
        overs = balls_bowled / 6 if balls_bowled > 0 else 0
        economy = round(runs_conceded / overs, 2) if overs > 0 else 0
        wickets_taken = int(
            wicket_df[wicket_df["bowler"] == selected_bowler].shape[0]
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wickets", wickets_taken)
        c2.metric("Runs Conceded", runs_conceded)
        c3.metric("Balls", balls_bowled)
        c4.metric("Economy", economy)

        if "season" in matches_f.columns:
            bowl_season = deliveries_f.merge(
                matches_f[["id", "season"]],
                left_on="match_id",
                right_on="id",
                how="left"
            )
            bowl_season = bowl_season[
                (bowl_season["bowler"] == selected_bowler) &
                (bowl_season["is_wicket"] == 1) &
                (~bowl_season["dismissal_kind"].isin(["run out", "retired hurt", "obstructing the field"]))
            ]
            bowl_season_grp = (
                bowl_season.groupby("season")["is_wicket"]
                .count()
                .reset_index()
                .rename(columns={"is_wicket": "season_wickets"})
                .sort_values("season")
            )

            fig_season_wk = px.line(
                bowl_season_grp,
                x="season",
                y="season_wickets",
                markers=True,
                title=f"Season-wise Wickets: {selected_bowler}",
                labels={"season_wickets": "Wickets"}
            )
            st.plotly_chart(fig_season_wk, use_container_width=True)
    else:
        st.write("Required columns for bowling analysis are missing in deliveries dataset.")
