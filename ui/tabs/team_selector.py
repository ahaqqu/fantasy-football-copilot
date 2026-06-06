"""Team Selector tab — optimize or manually pick your FIFA Fantasy team."""
import streamlit as st

from analysis.team_optimizer import optimize_team, validate_formation
from analysis.player_stats import calculate_fantasy_points
from analysis.player_fitness import assess_fitness_status
from data.fetcher import fetch_players


def render_team_summary(team: list[dict]) -> str:
    """Render team summary as HTML."""
    total_pts = sum(p.get("fantasy_points", 0) for p in team)

    html = '<div style="background:#f8f9fa; border-radius:12px; padding:16px; margin:8px 0;">'
    html += '<h3 style="margin:0;">Team Summary</h3>'
    html += f'<p><b>Total Fantasy Points:</b> {total_pts:.1f}</p>'
    html += f'<p><b>Players Selected:</b> {len(team)}/11</p>'

    # Position breakdown
    positions = {}
    for p in team:
        pos = p["player"]["position"]
        positions[pos] = positions.get(pos, 0) + 1

    for pos, count in sorted(positions.items()):
        html += f'<p style="margin:2px 0;"><b>{pos}:</b> {count}</p>'

    html += '<hr style="margin:8px 0;">'
    for p in team:
        name = p["player"]["name"]
        pts = p.get("fantasy_points", 0)
        html += f'<p style="margin:2px 0;">{name} — {pts:.1f} pts</p>'

    html += '</div>'
    return html


def render_formation_display(team: list[dict]) -> str:
    """Render team in formation layout."""
    html = '<div style="background:#1a1a2e; border-radius:12px; padding:20px; color:white;">'
    html += '<h3 style="margin:0 0 16px 0; text-align:center;">Your XI</h3>'

    positions_by_type = {"Goalkeeper": [], "Defender": [], "Midfielder": [], "Attacker": []}
    for p in team:
        pos = p["player"]["position"]
        if pos in positions_by_type:
            positions_by_type[pos].append(p["player"]["name"])

    row_order = [("Attacker", "FORWARDS"), ("Midfielder", "MIDFIELD"), ("Defender", "DEFENSE"), ("Goalkeeper", "GOALKEEPER")]

    for pos, label in row_order:
        players = positions_by_type.get(pos, [])
        if players:
            html += f'<div style="text-align:center; margin:12px 0;"><small style="opacity:0.6;">{label}</small><br>'
            for name in players:
                html += f'<span style="background:rgba(46,204,113,0.3); padding:6px 16px; border-radius:20px; margin:4px; display:inline-block;">{name}</span> '
            html += '</div>'

    html += '</div>'
    return html


def render():
    """Render the Team Selector tab."""
    st.header("Team Selector")

    players = fetch_players()
    if not players:
        st.warning("No player data available. Set API key in config.py.")
        return

    for p in players:
        p["fantasy_points"] = calculate_fantasy_points(p)
        p["fitness"] = assess_fitness_status(p)

    tab_auto, tab_manual = st.tabs(["Auto-Optimize", "Manual Pick"])

    with tab_auto:
        st.subheader("Auto-Optimize Your Team")

        col1, col2 = st.columns(2)
        with col1:
            formation = st.selectbox("Formation", ["4-4-2", "3-5-2", "4-3-3", "5-3-2", "4-2-3-1"])
        with col2:
            budget = st.slider("Budget", min_value=50, max_value=150, value=100, step=5)

        if st.button("Optimize Team", type="primary"):
            if not validate_formation(formation):
                st.error("Invalid formation. Must have exactly 10 outfield + 1 GK.")
            else:
                team = optimize_team(players, budget=budget, formation=formation)
                if team:
                    st.success(f"Optimized {formation} team found!")
                    st.markdown(render_formation_display(team), unsafe_allow_html=True)
                    st.markdown(render_team_summary(team), unsafe_allow_html=True)
                else:
                    st.warning("Could not optimize team with given constraints.")

    with tab_manual:
        st.subheader("Manually Pick Your Team")

        positions_needed = {"Goalkeeper": 1, "Defender": 4, "Midfielder": 4, "Attacker": 2}
        selected_team = []

        for pos, count in positions_needed.items():
            st.markdown(f"**{pos}** (pick {count})")
            position_players = [p for p in players if p["player"]["position"] == pos]
            ranked = sorted(position_players, key=lambda x: x.get("fantasy_points", 0), reverse=True)

            names = [p["player"]["name"] for p in ranked]
            chosen = st.multiselect(
                f"Select {count} {pos.lower()}s",
                names,
                key=f"manual_{pos}",
                max_selections=count,
            )
            for name in chosen:
                player = next(p for p in players if p["player"]["name"] == name)
                selected_team.append(player)

        if len(selected_team) == 11:
            st.markdown(render_formation_display(selected_team), unsafe_allow_html=True)
            st.markdown(render_team_summary(selected_team), unsafe_allow_html=True)
        elif selected_team:
            st.info(f"Selected {len(selected_team)}/11 players. Keep picking!")
