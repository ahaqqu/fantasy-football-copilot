"""Fixture Analysis tab — fixture cards with attack/defense ratings."""
import streamlit as st
import plotly.graph_objects as go

from analysis.fixture_analysis import classify_fixture, get_fixture_difficulty
from data.fetcher import fetch_fixtures


DIFFICULTY_COLORS = {"easy": "#2ecc71", "medium": "#f39c12", "hard": "#e74c3c"}


def render_fixture_card(fixture: dict, home_difficulty: str = "medium", away_difficulty: str = "medium") -> str:
    """Render a fixture card as HTML string."""
    home = fixture["teams"]["home"]
    away = fixture["teams"]["away"]
    date = fixture["fixture"]["date"][:10]
    home_color = DIFFICULTY_COLORS.get(home_difficulty, "gray")
    away_color = DIFFICULTY_COLORS.get(away_difficulty, "gray")

    return f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:16px; margin:8px; background:white;">
        <p style="color:#999; margin:0;">{date}</p>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
            <div style="text-align:center; flex:1;">
                <h3 style="margin:0;">{home['name']}</h3>
                <span style="background:{home_color}; color:white; padding:4px 12px; border-radius:20px; font-size:12px;">{home_difficulty.upper()}</span>
            </div>
            <div style="font-size:24px; color:#999; padding:0 16px;">vs</div>
            <div style="text-align:center; flex:1;">
                <h3 style="margin:0;">{away['name']}</h3>
                <span style="background:{away_color}; color:white; padding:4px 12px; border-radius:20px; font-size:12px;">{away_difficulty.upper()}</span>
            </div>
        </div>
    </div>
    """


def render_difficulty_chart(fixtures: list[dict]) -> go.Figure:
    """Render fixture difficulty as a bar chart."""
    if not fixtures:
        return go.Figure()

    opponents = [f["opponent"] for f in fixtures]
    venues = [f["venue"] for f in fixtures]
    difficulties = [f["difficulty"] for f in fixtures]
    colors = [DIFFICULTY_COLORS.get(d, "gray") for d in difficulties]

    fig = go.Figure(data=[
        go.Bar(
            x=opponents,
            y=[1] * len(opponents),
            marker_color=colors,
            text=[f"{v} vs {o}" for v, o in zip(venues, opponents)],
            textposition="inside",
        )
    ])
    fig.update_layout(
        title="Fixture Difficulty",
        yaxis=dict(showticklabels=False, showgrid=False),
        xaxis=dict(title="Opponent"),
        height=300,
    )
    return fig


def render():
    """Render the Fixture Analysis tab."""
    st.header("Fixture Analysis")

    fixtures = fetch_fixtures()
    if not fixtures:
        st.warning("No fixture data available. Set API key or check data sources.")
        return

    # Team filter
    all_teams = sorted(set(
        f["teams"]["home"]["name"] for f in fixtures
    ) | set(
        f["teams"]["away"]["name"] for f in fixtures
    ))
    selected_team = st.selectbox("Select team to analyze", all_teams)

    # Get fixtures for selected team
    team_fixtures = []
    for fix in fixtures:
        home = fix["teams"]["home"]["name"]
        away = fix["teams"]["away"]["name"]
        if home == selected_team or away == selected_team:
            classification = classify_fixture(home, away)
            team_fixtures.append({
                "fixture": fix,
                "home_difficulty": classification["home_difficulty"],
                "away_difficulty": classification["away_difficulty"],
            })

    # Show difficulty chart
    difficulty_data = get_fixture_difficulty(fixtures, selected_team)
    if difficulty_data:
        fig = render_difficulty_chart(difficulty_data)
        st.plotly_chart(fig, use_container_width=True)

    # Show fixture cards
    st.subheader(f"Fixtures for {selected_team}")
    for item in team_fixtures:
        fix = item["fixture"]
        st.markdown(
            render_fixture_card(fix, item["home_difficulty"], item["away_difficulty"]),
            unsafe_allow_html=True,
        )
