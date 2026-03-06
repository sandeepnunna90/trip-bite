import streamlit as st
import httpx

st.set_page_config(page_title="Restaurant — TripBite", page_icon="🍜", layout="wide")

place_id = st.session_state.get("current_place_id")
backend_url = st.session_state.get("backend_url", "http://localhost:8000")

if not place_id:
    st.warning("No restaurant selected. Go to Search first.")
    if st.button("← Back to Search"):
        st.switch_page("pages/1_Search.py")
    st.stop()

# Fetch restaurant metadata
try:
    r = httpx.get(f"{backend_url}/restaurants/{place_id}", timeout=15)
    r.raise_for_status()
    restaurant = r.json()
except Exception as e:
    st.error(f"Failed to load restaurant: {e}")
    st.stop()

# Header
col1, col2 = st.columns([1, 2])
with col1:
    if restaurant.get("photo_url"):
        st.image(restaurant["photo_url"], use_container_width=True)
    else:
        st.image("https://placehold.co/400x300?text=No+Photo", use_container_width=True)
with col2:
    st.title(restaurant["name"])
    stars = "⭐" * int(restaurant["rating"]) + f" **{restaurant['rating']}**"
    price = restaurant.get("price_level") or ""
    st.markdown(f"{stars} · {restaurant['review_count']:,} reviews · {price}")
    st.caption(restaurant.get("address", ""))

    if st.session_state.get("auth_token"):
        if st.button("💾 Save to Trip", type="primary"):
            try:
                resp = httpx.post(
                    f"{backend_url}/trips/{st.session_state.trip_id}/restaurants",
                    json={"place_id": place_id},
                    headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
                    timeout=10,
                )
                resp.raise_for_status()
                st.success("Saved to your trip!")
            except Exception as e:
                st.error(f"Failed to save: {e}")
    else:
        st.info("Sign in to save this restaurant to your trip.")

st.markdown("---")
st.subheader("🤖 Top Dishes (AI-Extracted from Reviews)")

with st.spinner("Analyzing reviews with AI... this may take 30-60 seconds the first time."):
    try:
        d = httpx.get(f"{backend_url}/dishes/{place_id}", timeout=180)
        d.raise_for_status()
        dishes = d.json()
    except httpx.HTTPStatusError as e:
        st.error(f"Failed to extract dishes: {e.response.text}")
        st.stop()
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

if not dishes:
    st.info("No dish data available for this restaurant.")
    st.stop()

CONFIDENCE_COLORS = {"high": "🟢", "medium": "🟡", "low": "🔴"}
CONFIDENCE_LABELS = {"high": "High confidence", "medium": "Medium confidence", "low": "Low confidence"}

cols = st.columns(2)
for i, dish in enumerate(dishes):
    with cols[i % 2]:
        with st.container(border=True):
            header_parts = [f"**{dish['dish_name']}**"]
            if dish.get("is_vegetarian"):
                header_parts.append("🥗 Vegetarian")
            st.markdown(" · ".join(header_parts))
            st.markdown(f"*{dish['reason']}*")

            conf = dish.get("confidence", "medium")
            badge = CONFIDENCE_COLORS.get(conf, "🟡")
            label = CONFIDENCE_LABELS.get(conf, conf)
            st.markdown(f"{badge} {label}")

            if conf == "low":
                st.caption("⚠️ Mentioned once — verify before visiting")

if st.button("← Back to Search"):
    st.switch_page("pages/1_Search.py")
