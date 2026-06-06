"""Team Hub tab — squad overview, fitness, and lineup predictor."""
import streamlit as st

from analysis.lineup_predictor import predict_lineup
from analysis.player_fitness import assess_fitness_status
from analysis.player_stats import calculate_fantasy_points
from data.fetcher import fetch_team_players


FORMATION_442 = {
    "Goalkeeper": {"row": 0, "cols": [1]},
    "Defender": {"row": 1, "cols": [0, 1, 2, 3]},
    "Midfielder": {"row": 2, "cols": [0, 1, 2, 3]},
    "Attacker": {"row": 3, "cols": [1, 2]},
}

TEAM_IDS = {
    "Brazil": 10, "France": 11, "England": 12, "Argentina": 13,
    "USA": 14, "Germany": 15, "Spain": 16, "Netherlands": 17,
    "Portugal": 18, "Belgium": 19, "Croatia": 20, "Morocco": 21,
    "Mexico": 22, "Japan": 23, "South Korea": 24, "Senegal": 25,
    "Canada": 26, "Uruguay": 27, "Switzerland": 28, "Ecuador": 29,
}


def render_squad_list(squad: list[dict]) -> str:
    """Render squad list as HTML."""
    html = '<div style="display:flex; flex-wrap:wrap; gap:8px;">'
    for p in squad:
        name = p["player"]["name"]
        pos = p["player"]["position"]
        prob = p.get("start_probability", 0)
        fitness = p.get("fitness", {})
        color = fitness.get("color", "gray")
        status = fitness.get("status", "Unknown")

        html += f"""
        <div style="border:1px solid {color}; border-radius:8px; padding:8px 12px; min-width:120px;">
            <b>{name}</b><br>
            <small>{pos}</small><br>
            <span style="color:{color};">● {status}</span><br>
            <small>Start: {prob:.0%}</small>
        </div>
        """
    html += "</div>"
    return html


def render_lineup_formation(lineup: list[dict]) -> str:
    """Render predicted lineup in formation layout."""
    html = '<div style="background:#2ecc71; border-radius:12px; padding:20px; color:white; text-align:center;">'
    html += '<h3 style="margin:0 0 16px 0;">Predicted Starting XI</h3>'

    positions_by_row = {}
    for p in lineup:
        pos = p["player"]["position"]
        if pos not in positions_by_row:
            positions_by_row[pos] = []
        positions_by_row[pos].append(p)

    row_order = ["Goalkeeper", "Defender", "Midfielder", "Attacker"]
    for pos in row_order:
        players_in_pos = positions_by_row.get(pos, [])
        if players_in_pos:
            html += '<div style="margin:8px 0;">'
            html += f'<small style="opacity:0.7;">{pos.upper()}</small><br>'
            for pl in players_in_pos:
                name = pl["player"]["name"]
                prob = pl.get("start_probability", 0)
                html += f'<span style="background:rgba(255,255,255,0.2); padding:4px 12px; border-radius:20px; margin:4px; display:inline-block;">{name} ({prob:.0%})</span> '
            html += '</div>'

    html += '</div>'
    return html


def render():
    """Render the Team Hub tab."""
    st.header("Team Hub")

    team_name = st.selectbox("Select national team", list(TEAM_IDS.keys()))

    tab_squad, tab_lineup, tab_fitness = st.tabs(["Squad Overview", "Lineup Predictor", "Fitness Report"])

    with tab_squad:
        st.subheader(f"{team_name} Squad")
        team_id = TEAM_IDS[team_name]
        squad = fetch_team_players(team_id=team_id)

        if not squad:
            st.warning(f"No squad data for {team_name} yet.")
            st.info("Data is updated daily.")
            return

        for p in squad:
            p["fantasy_points"] = calculate_fantasy_points(p)
            p["fitness"] = assess_fitness_status(p)

        st.markdown(render_squad_list(squad), unsafe_allow_html=True)

    with tab_lineup:
        st.subheader(f"Predicted Lineup — {team_name}")
        squad_for_lineup = fetch_team_players(team_id=team_id)
        if not squad_for_lineup:
            st.warning("No squad data available yet.")
            return

        for p in squad_for_lineup:
            p["fantasy_points"] = calculate_fantasy_points(p)
            p["fitness"] = assess_fitness_status(p)

        lineup = predict_lineup(squad_for_lineup, formation="4-4-2")
        if lineup:
            st.markdown(render_lineup_formation(lineup), unsafe_allow_html=True)
        else:
            st.info("Not enough data to predict lineup.")

    with tab_fitness:
        st.subheader(f"Fitness Report — {team_name}")
        squad_fitness = fetch_team_players(team_id=team_id)
        if not squad_fitness:
            st.warning("No squad data available.")
            return

        for p in squad_fitness:
            p["fantasy_points"] = calculate_fantasy_points(p)
            p["fitness"] = assess_fitness_status(p)

        healthy = [p for p in squad_fitness if p.get("fitness", {}).get("status") == "Healthy"]
        risk = [p for p in squad_fitness if p.get("fitness", {}).get("status") != "Healthy"]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Healthy", len(healthy))
        with col2:
            st.metric("At Risk", len(risk))

        if risk:
            st.warning("Players at risk:")
            for p in risk:
                f = p.get("fitness", {})
                st.write(f"• **{p['player']['name']}** — {f.get('status', 'Unknown')}: {f.get('details', '')}")
