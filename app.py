"""Fantasy Football World Cup 2026 Copilot — Main Entry Point."""
import streamlit as st

st.set_page_config(
    page_title="Fantasy Football World Cup 2026 Copilot",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Fantasy Football World Cup 2026 Copilot")

tab1, tab2, tab3, tab4 = st.tabs([
    "🧑 Player Hub",
    "📅 Fixture Analysis",
    "🏟️ Team Hub",
    "📋 Team Selector",
])

with tab1:
    st.info("Player Hub — coming soon (Task 11)")

with tab2:
    st.info("Fixture Analysis — coming soon (Task 12)")

with tab3:
    st.info("Team Hub — coming soon (Task 13)")

with tab4:
    st.info("Team Selector — coming soon (Task 14)")

st.markdown("---")
st.caption("Fantasy Football World Cup 2026 Copilot v0.1 — Built with ❤️ by opencode")
