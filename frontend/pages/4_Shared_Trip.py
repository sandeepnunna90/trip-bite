import streamlit as st
import httpx

st.set_page_config(page_title="Shared Trip — TripBite", page_icon="🔗", layout="wide")

backend_url = st.session_state.get("backend_url", "http://localhost:8000")

token = st.query_params.get("token")

if not token:
    st.title("🔗 Shared Trip")
    st.info("No share token provided. Use a valid share link like `?token=abc123`")
    st.stop()

with st.spinner("Loading shared trip..."):
    try:
        resp = httpx.get(f"{backend_url}/share/{token}", timeout=15)
        resp.raise_for_status()
        trip = resp.json()
    except httpx.HTTPStatusError as e:
        st.error(f"Share link not found or expired: {e.response.text}")
        st.stop()
    except Exception as e:
        st.error(f"Failed to load shared trip: {e}")
        st.stop()

restaurants = trip.get("restaurants", [])

st.title(f"🍽️ {trip['name']}")
st.caption(f"{len(restaurants)} restaurant{'s' if len(restaurants) != 1 else ''} · Read-only shared view")

if not restaurants:
    st.info("This trip has no restaurants yet.")
    st.stop()

CONFIDENCE_COLORS = {"high": "🟢", "medium": "🟡", "low": "🔴"}

for tr in restaurants:
    restaurant = tr.get("restaurant") or {}
    dishes = tr.get("dishes", [])

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            photo = restaurant.get("photo_url")
            if photo:
                st.image(photo, use_container_width=True)
            else:
                st.image("https://placehold.co/200x150?text=No+Photo", use_container_width=True)
        with col2:
            st.markdown(f"**{restaurant.get('name', tr['place_id'])}**")
            rating = restaurant.get("rating")
            review_count = restaurant.get("review_count")
            price = restaurant.get("price_level", "")
            if rating:
                st.markdown(f"⭐ {rating} · {review_count:,} reviews · {price}")
            st.caption(restaurant.get("address", ""))

        if dishes:
            st.markdown("**Top Dishes:**")
            dish_cols = st.columns(2)
            for i, dish in enumerate(dishes):
                with dish_cols[i % 2]:
                    conf = dish.get("confidence", "medium")
                    veg = " 🥗" if dish.get("is_vegetarian") else ""
                    st.markdown(
                        f"{CONFIDENCE_COLORS[conf]} **{dish['dish_name']}**{veg}  \n"
                        f"*{dish['reason']}*"
                    )
        else:
            st.caption("No dish data available")

st.markdown("---")
st.caption("Powered by [TripBite](http://localhost:8501) · Discover the best dishes at top-rated restaurants")
