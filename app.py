import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(page_title="Connect 4 AI Dashboard", layout="wide")

st.title("Connect 4 AI Dashboard")
st.write("Interactive analysis of Connect 4 games played by MCTS, Minimax, and Random agents.")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    move_log = pd.read_csv("move_log.csv")
    game_log = pd.read_csv("game_log.csv")
    return move_log, game_log

move_log, game_log = load_data()

# -----------------------------
# PREPARE DATA
# -----------------------------
game_log["matchup"] = (
    game_log["player_one_algorithm"] + " vs " + game_log["player_two_algorithm"]
)

game_log["nodes_per_move"] = (
    game_log["final_nodes_player_one"] + game_log["final_nodes_player_two"]
) / game_log["total_moves"]

move_log = move_log.sort_values(["game_tuple_id", "game_id", "move_number"]).copy()

move_log["nodes_visited_per_move"] = move_log.groupby(
    ["game_tuple_id", "game_id", "player"]
)["nodes_visited_running_sum"].diff()

move_log["nodes_visited_per_move"] = move_log["nodes_visited_per_move"].fillna(
    move_log["nodes_visited_running_sum"]
)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("Filters")

matchup_options = ["All"] + sorted(game_log["matchup"].unique().tolist())
selected_matchup = st.sidebar.selectbox("Matchup", matchup_options)

winner_options = ["All"] + sorted(game_log["winner_algorithm"].unique().tolist())
selected_winner = st.sidebar.selectbox("Winner", winner_options)

algo_view = st.sidebar.radio(
    "Algorithm View",
    ["All", "mcts", "minimax", "random"],
    index=0
)

show_advanced = st.sidebar.checkbox("Show Advanced Analysis", value=True)

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_game_log = game_log.copy()

if selected_matchup != "All":
    filtered_game_log = filtered_game_log[
        filtered_game_log["matchup"] == selected_matchup
    ]

if selected_winner != "All":
    filtered_game_log = filtered_game_log[
        filtered_game_log["winner_algorithm"] == selected_winner
    ]

filtered_move_log = move_log.merge(
    filtered_game_log[["game_tuple_id", "game_id"]],
    on=["game_tuple_id", "game_id"],
    how="inner"
)

if algo_view != "All":
    filtered_move_log = filtered_move_log[
        filtered_move_log["algorithm"] == algo_view
    ]

if filtered_game_log.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# HELPER VALUES
# -----------------------------
total_games_filtered = len(filtered_game_log)
total_games_all = len(game_log)
total_moves_filtered = len(filtered_move_log)

avg_game_duration = filtered_game_log["game_duration_sec"].mean()
avg_moves = filtered_game_log["total_moves"].mean()

winner_counts = filtered_game_log["winner_algorithm"].value_counts()
top_algorithm = winner_counts.idxmax()
top_algorithm_wins = int(winner_counts.max())

best_game = filtered_game_log.sort_values(
    by=["total_moves", "game_duration_sec"],
    ascending=[False, False]
).iloc[0]

worst_game = filtered_game_log.sort_values(
    by=["total_moves", "game_duration_sec"],
    ascending=[True, True]
).iloc[0]

# -----------------------------
# KPI CARDS
# -----------------------------
st.subheader("Dashboard Summary")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Games (Filtered)",
        total_games_filtered,
        delta=total_games_filtered - total_games_all
    )

with col2:
    st.metric("Moves (Filtered)", total_moves_filtered)

with col3:
    st.metric("Avg Duration", f"{avg_game_duration:.2f}s")

with col4:
    st.metric("Avg Moves", f"{avg_moves:.2f}")

with col5:
    st.metric("🏆 Top Algorithm", top_algorithm, f"{top_algorithm_wins} wins")

# -----------------------------
# INSIGHT BOXES
# -----------------------------
st.markdown("### Key Insights")

insight_col1, insight_col2, insight_col3 = st.columns(3)

with insight_col1:
    st.success(f"**{top_algorithm.upper()}** is the top-performing algorithm in the current filtered view.")

with insight_col2:
    if "mcts" in filtered_move_log["algorithm"].unique():
        st.info("ℹ️ MCTS often explores more nodes and usually takes more time per move.")

with insight_col3:
    if "random" in filtered_move_log["algorithm"].unique():
        st.warning("⚠️ Random is fast, but usually weaker than search-based strategies.")

# -----------------------------
# PROGRESS BARS
# -----------------------------
st.markdown("### Win Share")

progress_cols = st.columns(3)
total_wins = winner_counts.sum()

for idx, algo in enumerate(["mcts", "minimax", "random"]):
    wins = int(winner_counts.get(algo, 0))
    ratio = wins / total_wins if total_wins > 0 else 0
    with progress_cols[idx]:
        st.write(f"**{algo.upper()}**: {wins} wins")
        st.progress(ratio)

# -----------------------------
# BEST / WORST GAME CARDS
# -----------------------------
st.markdown("### Representative Games")

card1, card2 = st.columns(2)

with card1:
    st.info(
        f"**Best Game**  \n"
        f"Game ID: {best_game['game_id']}  \n"
        f"Tuple ID: {best_game['game_tuple_id']}  \n"
        f"Matchup: {best_game['matchup']}  \n"
        f"Winner: {best_game['winner_algorithm']}  \n"
        f"Moves: {best_game['total_moves']}  \n"
        f"Duration: {best_game['game_duration_sec']:.2f}s"
    )

with card2:
    st.info(
        f"**Worst Game**  \n"
        f"Game ID: {worst_game['game_id']}  \n"
        f"Tuple ID: {worst_game['game_tuple_id']}  \n"
        f"Matchup: {worst_game['matchup']}  \n"
        f"Winner: {worst_game['winner_algorithm']}  \n"
        f"Moves: {worst_game['total_moves']}  \n"
        f"Duration: {worst_game['game_duration_sec']:.2f}s"
    )

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Performance", "Matchups", "Game Explorer"]
)

# -----------------------------
# TAB 1: OVERVIEW
# -----------------------------
with tab1:
    st.subheader("Overview")

    c1, c2 = st.columns(2)

    with c1:
        fig, ax = plt.subplots()
        filtered_game_log["winner_algorithm"].value_counts().plot(kind="bar", ax=ax)
        ax.set_title("Winner Distribution by Algorithm")
        ax.set_xlabel("Algorithm")
        ax.set_ylabel("Number of Wins")
        st.pyplot(fig)

    with c2:
        fig, ax = plt.subplots()

        games_played = pd.concat([
            filtered_game_log["player_one_algorithm"],
            filtered_game_log["player_two_algorithm"]
        ]).value_counts()

        wins = filtered_game_log[
            filtered_game_log["winner_algorithm"] != "Draw"
        ]["winner_algorithm"].value_counts()

        wins = wins.reindex(games_played.index, fill_value=0)

        win_rate = ((wins / games_played) * 100).sort_values(ascending=False)

        win_rate.plot(kind="bar", ax=ax)

        ax.set_title("Win Rate by Algorithm")
        ax.set_xlabel("Algorithm")
        ax.set_ylabel("Win Rate (%)")

        st.pyplot(fig)

        st.caption(
            "Win rate is calculated based on games each algorithm participated in. "
            "Self-play matchups result in about 50% because the same algorithm competes against itself."
        )

    c3, c4 = st.columns(2)

    with c3:
        fig, ax = plt.subplots()
        filtered_game_log["total_moves"].hist(bins=20, ax=ax)
        ax.set_title("Distribution of Total Moves")
        ax.set_xlabel("Moves")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

    with c4:
        fig, ax = plt.subplots()
        filtered_move_log["column_selected"].value_counts().sort_index().plot(kind="bar", ax=ax)
        ax.set_title("Column Selection Pattern")
        ax.set_xlabel("Column")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

# -----------------------------
# TAB 2: PERFORMANCE
# -----------------------------
with tab2:
    st.subheader("Performance Analysis")

    c1, c2 = st.columns(2)

    with c1:
        if not filtered_move_log.empty:
            fig, ax = plt.subplots()
            filtered_move_log.groupby("algorithm")["duration_seconds"].mean().plot(
                kind="bar", ax=ax
            )
            ax.set_title("Average Move Time by Algorithm")
            ax.set_xlabel("Algorithm")
            ax.set_ylabel("Seconds")
            st.pyplot(fig)
        else:
            st.warning("No move data available for current filters.")

    with c2:
        if not filtered_move_log.empty:

            search_moves = filtered_move_log[
                filtered_move_log["algorithm"].isin(["mcts", "minimax"])
            ]

            if search_moves.empty:
                st.info("No search-based algorithm data available for current filters.")
            else:
                fig, ax = plt.subplots()

                search_moves.groupby("algorithm")["nodes_visited_per_move"].mean().plot(
                    kind="bar", ax=ax
                )

                ax.set_title("Average Nodes Explored per Move by Search Algorithm")
                ax.set_xlabel("Algorithm")
                ax.set_ylabel("Nodes per Move")

                st.pyplot(fig)

                st.caption(
                    "Random is excluded because it does not perform tree search."
                )
        else:
            st.warning("No move data available for current filters.")

    c3, c4 = st.columns(2)

    # Define search-based moves (exclude Random)
    search_moves = filtered_move_log[
        filtered_move_log["algorithm"].isin(["mcts", "minimax"])
    ]

    with c3:
        if search_moves.empty:
            st.info("No search-based algorithm data available for current filters.")
        else:
            fig, ax = plt.subplots()

            search_moves.groupby("algorithm")["nodes_visited_per_move"].mean().plot(
                kind="bar", ax=ax
            )

            ax.set_title("Efficiency: Nodes per Move (Search Algorithms)")
            ax.set_xlabel("Algorithm")
            ax.set_ylabel("Nodes per Move")

            st.pyplot(fig)

            st.caption(
                "Random is excluded because it does not perform tree search."
            )

    with c4:
        avg_time = filtered_move_log.groupby("algorithm")["duration_seconds"].mean()
        wins = filtered_game_log["winner_algorithm"].value_counts()

        comparison = pd.DataFrame({
            "avg_time": avg_time,
            "wins": wins
        }).fillna(0)

        st.write("#### Time vs Strength Trade-off")
        st.dataframe(comparison, use_container_width=True)

# -----------------------------
# TAB 3: MATCHUPS
# -----------------------------
with tab3:
    st.subheader("Matchup Analysis")

    matchup_wins = filtered_game_log.groupby(
        ["matchup", "winner_algorithm"]
    ).size().unstack(fill_value=0)

    c1, c2 = st.columns(2)

    with c1:
        fig, ax = plt.subplots()
        matchup_wins.plot(kind="bar", stacked=True, ax=ax)
        ax.set_title("Win Count by Matchup")
        ax.set_xlabel("Matchup")
        ax.set_ylabel("Games")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with c2:
        matchup_percent = matchup_wins.div(matchup_wins.sum(axis=1), axis=0) * 100
        fig, ax = plt.subplots()
        matchup_percent.plot(kind="bar", stacked=True, ax=ax)
        ax.set_title("Win Percentage by Matchup")
        ax.set_xlabel("Matchup")
        ax.set_ylabel("Percentage")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    c3, c4 = st.columns(2)

    with c3:
        fig, ax = plt.subplots()
        filtered_game_log.groupby("matchup")["game_duration_sec"].mean().plot(
            kind="bar", ax=ax
        )
        ax.set_title("Average Game Duration by Matchup")
        ax.set_xlabel("Matchup")
        ax.set_ylabel("Seconds")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with c4:
        fig, ax = plt.subplots()
        filtered_game_log.groupby("matchup")["total_moves"].mean().plot(
            kind="bar", ax=ax
        )
        ax.set_title("Average Moves by Matchup")
        ax.set_xlabel("Matchup")
        ax.set_ylabel("Moves")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    

# -----------------------------
# TAB 4: GAME EXPLORER
# -----------------------------
with tab4:
    st.subheader("Game Explorer")

    game_options = filtered_game_log[
        [
            "game_tuple_id",
            "game_id",
            "player_one_algorithm",
            "player_two_algorithm",
            "winner_algorithm",
            "matchup",
            "total_moves",
            "game_duration_sec",
        ]
    ].copy()

    game_options["label"] = (
        "Tuple " + game_options["game_tuple_id"].astype(str)
        + " | Game " + game_options["game_id"].astype(str)
        + " | " + game_options["matchup"]
        + " | Winner: " + game_options["winner_algorithm"]
    )

    selected_label = st.selectbox("Select Game", game_options["label"])

    selected_row = game_options[game_options["label"] == selected_label].iloc[0]

    selected_game_summary = filtered_game_log[
        (filtered_game_log["game_tuple_id"] == selected_row["game_tuple_id"]) &
        (filtered_game_log["game_id"] == selected_row["game_id"])
    ]

    selected_moves = move_log[
        (move_log["game_tuple_id"] == selected_row["game_tuple_id"]) &
        (move_log["game_id"] == selected_row["game_id"])
    ].sort_values("move_number")

    selected_search_moves = selected_moves[
        selected_moves["algorithm"].isin(["mcts", "minimax"])
    ]

    st.write("### Selected Game Summary")
    st.dataframe(selected_game_summary, use_container_width=True)

    g1, g2 = st.columns(2)

    st.write("### Nodes Explored per Move")

    if selected_search_moves.empty:
        st.info("Node exploration is not shown because Random does not perform tree search.")
    else:
        fig, ax = plt.subplots()

        for player_name in ["One", "Two"]:
            subset = selected_search_moves[selected_search_moves["player"] == player_name]
            ax.bar(
                subset["move_number"],
                subset["nodes_visited_per_move"],
                label=f"Player {player_name}",
                alpha=0.8
            )

        ax.set_title("Nodes Explored per Move by Search Algorithm")
        ax.set_xlabel("Move Number")
        ax.set_ylabel("Nodes per Move")
        ax.legend()
        st.pyplot(fig)

        st.caption("Random is excluded because it does not perform tree search.")

    with g1:
        fig, ax = plt.subplots()

        for player_name in ["One", "Two"]:
            subset = selected_moves[selected_moves["player"] == player_name]
            ax.plot(
                subset["move_number"],
                subset["duration_seconds"],
                marker="o",
                label=f"Player {player_name}"
            )

        ax.set_title("Move Duration Over Time by Player")
        ax.set_xlabel("Move Number")
        ax.set_ylabel("Duration (sec)")
        ax.legend()
        st.pyplot(fig)

    with g2:
        if selected_search_moves.empty:
            st.info("Cumulative search nodes are not shown because Random does not perform tree search.")
        else:
            fig, ax = plt.subplots()

            for player_name in ["One", "Two"]:
                subset = selected_search_moves[selected_search_moves["player"] == player_name]
                ax.plot(
                    subset["move_number"],
                    subset["nodes_visited_running_sum"],
                    marker="o",
                    label=f"Player {player_name}"
                )

            ax.set_title("Cumulative Search Nodes by Player")
            ax.set_xlabel("Move Number")
            ax.set_ylabel("Cumulative Search Nodes")
            ax.legend()
            st.pyplot(fig)

            st.caption("Random is excluded because it does not perform tree search.")

    if show_advanced:
        with st.expander("Advanced Game Explorer"):
            st.write("### Move Log")
            st.dataframe(selected_moves, use_container_width=True)

            fig, ax = plt.subplots()

            for player_name in ["One", "Two"]:
                subset = selected_moves[selected_moves["player"] == player_name]
                ax.plot(
                    subset["move_number"],
                    subset["duration_seconds"],
                    marker="o",
                    label=f"Player {player_name}"
                )

            ax.set_title("Move Duration Comparison by Player")
            ax.set_xlabel("Move Number")
            ax.set_ylabel("Duration (sec)")
            ax.legend()
            st.pyplot(fig)

# -----------------------------
# FOOTER NOTES
# -----------------------------
with st.expander("Notes, Limitations, and Future Work"):
    st.markdown("""
**Limitations**
- All games start with Player One, which may introduce first-move bias.
- The number of simulations is fixed and may limit generalization.
- MCTS and Minimax performance depends on configuration and search settings.

**Future Work**
- Randomize the starting player.
- Increase the number of simulations.
- Tune hyperparameters for MCTS and Minimax.
- Add board-state replay for selected games.
- Build a human-vs-AI playable web version.
""")