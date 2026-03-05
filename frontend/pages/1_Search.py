import streamlit as st
import httpx

st.set_page_config(page_title="Search — TripBite", page_icon="🔍", layout="wide")

CUISINES = ["Any", "BBQ", "Ramen", "Sushi", "Pizza", "Tacos", "Thai", "Italian", "Indian", "Mexican", "Burgers", "Seafood", "Vegan"]

st.title("🔍 Find Restaurants")

with st.form("search_form"):
    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", placeholder="e.g. Nashville, TN")
    with col2:
        cuisine = st.selectbox("Cuisine", CUISINES)
    submitted = st.form_submit_button("Search", use_container_width=True, type="primary")

if submitted:
    if not city.strip():
        st.error("Please enter a city.")
    else:
        backend_url = st.session_state.get("backend_url", "http://localhost:8000")
        with st.spinner(f"Searching for {cuisine} restaurants in {city}..."):
            try:
                resp = httpx.get(
                    f"{backend_url}/restaurants/search",
                    params={"city": city.strip(), "cuisine": cuisine},
                    timeout=20,
                )
                resp.raise_for_status()
                st.session_state.search_results = resp.json()
            except httpx.HTTPStatusError as e:
                st.error(f"Search failed: {e.response.text}")
            except Exception as e:
                st.error(f"Could not connect to backend: {e}")

results = st.session_state.get("search_results", [])

if results:
    st.markdown(f"### {len(results)} restaurants found (4.5★+ · 1,000+ reviews)")
    st.markdown("---")

    cols = st.columns(3)
    for i, r in enumerate(results):
        with cols[i % 3]:
            with st.container(border=True):
                if r.get("photo_url"):
                    st.image(r["photo_url"], use_container_width=True)
                else:
                    st.image("https://placehold.co/400x300?text=No+Photo", use_container_width=True)

                st.markdown(f"**{r['name']}**")
                stars = "⭐" * int(r["rating"]) + f" {r['rating']}"
                price = r.get("price_level") or ""
                st.markdown(f"{stars} · {r['review_count']:,} reviews · {price}")
                st.caption(r.get("address", ""))

                if st.button("View Dishes →", key=f"view_{r['place_id']}", use_container_width=True):
                    st.session_state.current_place_id = r["place_id"]
                    st.switch_page("pages/2_Restaurant.py")
elif submitted:
    st.info("No restaurants found matching your criteria. Try a different city or cuisine.")
