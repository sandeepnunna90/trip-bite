import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="TripBite",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state defaults
defaults = {
    "auth_token": None,
    "user_id": None,
    "trip_id": None,
    "current_place_id": None,
    "search_results": [],
    "backend_url": os.getenv("BACKEND_URL", "http://localhost:8000"),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

st.title("🍽️ TripBite")
st.markdown("*Discover the best dishes at top-rated restaurants — curated by AI.*")

st.markdown("---")
st.markdown("### Welcome to TripBite!")
st.markdown(
    """
Use the sidebar to navigate:

- **🔍 Search** — Find top-rated restaurants by city and cuisine
- **🍜 Restaurant** — View AI-extracted top dishes for any restaurant
- **📋 My Trip** — Save restaurants and export your trip list
- **🔗 Shared Trip** — View a trip someone shared with you
"""
)

if st.session_state.auth_token:
    st.success(f"✅ Logged in")
else:
    st.info("💡 Sign in on the My Trip page to save restaurants to your trip.")
