"""Player Hub tab — player stats, fitness, expert opinions, comparison."""
import streamlit as st
import pandas as pd

from analysis.player_stats import calculate_fantasy_points, rank_players, get_top_players_by_position
from analysis.player_fitness import assess_fitness_status
from data.fetcher import fetch_players


def render_player_card(player: dict) -> str:
    """Render a player card as HTML string."""
    p = player["player"]
    stats = player["statistics"][0] if player.get("statistics") else {}
    fitness = player.get("fitness", {})
    pts = player.get("fantasy_points", 0)

    color = fitness.get("color", "gray")
    status = fitness.get("status", "Unknown")

    return f"""
    <div style="border:2px solid {color}; border-radius:12px; padding:16px; margin:8px; width:220px; display:inline-block;">
        <h3 style="margin:0;">{p['name']}</h3>
        <p style="color:#666; margin:4px 0;">{p['position']} | Age {p.get('age', '?')}</p>
        <p style="font-size:24px; font-weight:bold; margin:8px 0;">{pts:.1f} pts</p>
        <p>Goals: {stats.get('goals', {}).get('total', 0)} | Rating: {stats.get('rating', 'N/A')}</p>
        <p style="color:{color}; font-weight:bold;">● {status}</p>
    </div>
    """


def render_comparison_table(player1: dict, player2: dict) -> str:
    """Render comparison table as HTML string."""
    s1 = player1["statistics"][0] if player1.get("statistics") else {}
    s2 = player2["statistics"][0] if player2.get("statistics") else {}
    p1 = player1["player"]
    p2 = player2["player"]

    return f"""
    <table style="width:100%; border-collapse:collapse;">
        <tr style="background:#f0f2f6;"><th></th><th>{p1['name']}</th><th>{p2['name']}</th></tr>
        <tr><td><b>Position</b></td><td>{p1['position']}</td><td>{p2['position']}</td></tr>
        <tr><td><b>Goals</b></td><td>{s1.get('goals',{}).get('total',0)}</td><td>{s2.get('goals',{}).get('total',0)}</td></tr>
        <tr><td><b>Key Passes</b></td><td>{s1.get('passes',{}).get('key',0)}</td><td>{s2.get('passes',{}).get('key',0)}</td></tr>
        <tr><td><b>Rating</b></td><td>{s1.get('rating','N/A')}</td><td>{s2.get('rating','N/A')}</td></tr>
        <tr><td><b>Fantasy Pts</b></td><td>{player1.get('fantasy_points',0):.1f}</td><td>{player2.get('fantasy_points',0):.1f}</td></tr>
    </table>
    """


def render():
    """Render the Player Hub tab."""
    st.header("Player Hub")

    # Load data
    players = fetch_players()
    if not players:
        st.warning("No player data available. Set API key in config.py or check data sources.")
        st.info("Tip: Set API_FOOTBALL_KEY environment variable or edit config.py")
        return

    # Add fantasy points and fitness
    for p in players:
        p["fantasy_points"] = calculate_fantasy_points(p)
        p["fitness"] = assess_fitness_status(p)

    # Sub-tabs
    tab_search, tab_rank, tab_compare, tab_experts = st.tabs([
        "Search Players", "Rankings", "Compare", "Expert Picks"
    ])

    with tab_search:
        st.subheader("Search & Browse Players")
        col1, col2 = st.columns([3, 1])
        with col2:
            position_filter = st.selectbox("Position", ["All", "Goalkeeper", "Defender", "Midfielder", "Attacker"])
        with col1:
            search = st.text_input("Search by name")

        filtered = players
        if position_filter != "All":
            filtered = [p for p in filtered if p["player"]["position"] == position_filter]
        if search:
            filtered = [p for p in filtered if search.lower() in p["player"]["name"].lower()]

        for p in filtered[:20]:
            st.markdown(render_player_card(p), unsafe_allow_html=True)

    with tab_rank:
        st.subheader("Player Rankings by Position")
        position = st.selectbox("Rank by position", ["All", "Goalkeeper", "Defender", "Midfielder", "Attacker"], key="rank_pos")
        if position == "All":
            ranked = rank_players(players)
        else:
            ranked = get_top_players_by_position(players, position)

        df = pd.DataFrame([{
            "Name": p["player"]["name"],
            "Position": p["player"]["position"],
            "Goals": p["statistics"][0].get("goals", {}).get("total", 0) if p.get("statistics") else 0,
            "Fantasy Pts": p.get("fantasy_points", 0),
            "Status": p.get("fitness", {}).get("status", "Unknown"),
        } for p in ranked[:20]])

        st.dataframe(df, use_container_width=True)

    with tab_compare:
        st.subheader("Compare Players")
        col1, col2 = st.columns(2)
        names = [p["player"]["name"] for p in players]
        with col1:
            p1_name = st.selectbox("Player 1", names, key="cmp1")
        with col2:
            p2_name = st.selectbox("Player 2", names, key="cmp2")

        p1 = next((p for p in players if p["player"]["name"] == p1_name), None)
        p2 = next((p for p in players if p["player"]["name"] == p2_name), None)

        if p1 and p2:
            st.markdown(render_comparison_table(p1, p2), unsafe_allow_html=True)

    with tab_experts:
        st.subheader("Expert Recommendations")

        # Load data
        from data.scraper import scrape_expert_opinions
        data = scrape_expert_opinions(use_cache=True)
        classified = data.get("classified", {})
        players_mentions = classified.get("players", {})
        countries_mentions = classified.get("countries", {})

        if not players_mentions and not countries_mentions:
            st.warning("No expert data yet. Run locally:")
            st.code("python scrape.py", language="bash")
            st.info("Then commit and push: `git add data/cache/ && git commit -m 'data: update' && git push`")
            return

        # Load data
        from data.scraper import scrape_expert_opinions
        data = scrape_expert_opinions(use_cache=True)
        classified = data.get("classified", {})
        players_mentions = classified.get("players", {})
        countries_mentions = classified.get("countries", {})

        if not players_mentions and not countries_mentions:
            st.info("No expert data yet. Click 'Scrape Now' above or run: `python scrape.py`")
            return

        # Show learned players
        from data.learned_store import get_learned_players
        learned = get_learned_players()
        learned_count = len(learned.get("players", {}))

        if learned_count > 0:
            with st.expander(f" Discovered Players ({learned_count} new players found by LLM)", expanded=False):
                for name, info in sorted(learned["players"].items()):
                    st.markdown(f"**{name}** — {info['country']} (from {info['source']}, added {info['added_at'][:10]})")

        tab_by_player, tab_by_country = st.tabs(["By Player", "By Country"])

        with tab_by_player:
            st.markdown(f"**{len(players_mentions)} players mentioned across all sources**")
            # Sort by number of mentions (most talked about first)
            sorted_players = sorted(
                players_mentions.items(),
                key=lambda x: len(x[1]["mentions"]),
                reverse=True,
            )
            for player_name, data_p in sorted_players[:30]:
                country = data_p["country"]
                mentions = data_p["mentions"]
                sentiments = [m["sentiment"] for m in mentions]
                pos = sentiments.count("positive")
                neg = sentiments.count("negative")
                sources = list(set(m["source"] for m in mentions))

                sentiment_bar = f"🟢 {pos}" if pos else ""
                sentiment_bar += f" 🔴 {neg}" if neg else ""

                with st.expander(f"**{player_name}** ({country}) — {len(mentions)} mentions {sentiment_bar}"):
                    st.caption(f"Sources: {', '.join(sources)}")
                    for m in mentions:
                        color = "green" if m["sentiment"] == "positive" else "red" if m["sentiment"] == "negative" else "gray"
                        st.markdown(f"**{m['source']}** [{m['sentiment']}] — _{m['context']}_")

        with tab_by_country:
            st.markdown(f"**{len(countries_mentions)} countries mentioned across all sources**")
            sorted_countries = sorted(
                countries_mentions.items(),
                key=lambda x: len(x[1]["mentions"]),
                reverse=True,
            )
            for country, data_c in sorted_countries:
                mentions = data_c["mentions"]
                players_list = data_c.get("players_mentioned", [])
                sentiments = [m["sentiment"] for m in mentions]
                pos = sentiments.count("positive")
                neg = sentiments.count("negative")

                sentiment_bar = f"🟢 {pos}" if pos else ""
                sentiment_bar += f" 🔴 {neg}" if neg else ""

                with st.expander(f"**{country}** — {len(mentions)} mentions {sentiment_bar}"):
                    if players_list:
                        st.caption(f"Players mentioned: {', '.join(players_list[:10])}")
                    for m in mentions[:5]:
                        color = "green" if m["sentiment"] == "positive" else "red" if m["sentiment"] == "negative" else "gray"
                        st.markdown(f"**{m['source']}** [{m['sentiment']}] — _{m['context']}_")
