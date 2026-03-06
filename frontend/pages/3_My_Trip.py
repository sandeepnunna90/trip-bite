import streamlit as st
import httpx
import extra_streamlit_components as stx
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="My Trip — TripBite", page_icon="📋", layout="wide")

backend_url = st.session_state.get("backend_url", "http://localhost:8000")

# ── Cookie-based session restore ─────────────────────────────
cookie_manager = stx.CookieManager()
if not st.session_state.get("auth_token"):
    token = cookie_manager.get("auth_token")
    if token:
        st.session_state.auth_token = token

st.title("📋 My Trip")

# ── Auth gate ────────────────────────────────────────────────
if not st.session_state.get("auth_token"):
    st.info("Sign in to save and manage your trip.")

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", type="primary")
        if submitted:
            try:
                resp = httpx.post(
                    f"{backend_url}/auth/login",
                    json={"email": email, "password": password},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.auth_token = data["access_token"]
                st.session_state.user_id = data["user_id"]
                expires = datetime.now(timezone.utc) + timedelta(minutes=30)
                cookie_manager.set("auth_token", data["access_token"], expires_at=expires, key="set_auth")
                st.rerun()
            except httpx.HTTPStatusError as e:
                st.error(f"Login failed: {e.response.json().get('detail', e.response.text)}")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Name")
            email_s = st.text_input("Email", key="signup_email")
            password_s = st.text_input("Password", type="password", key="signup_pw")
            submitted_s = st.form_submit_button("Create Account", type="primary")
        if submitted_s:
            try:
                resp = httpx.post(
                    f"{backend_url}/auth/signup",
                    json={"name": name, "email": email_s, "password": password_s},
                    timeout=10,
                )
                resp.raise_for_status()
                st.success(resp.json()["message"])
            except httpx.HTTPStatusError as e:
                st.error(f"Signup failed: {e.response.json().get('detail', e.response.text)}")
            except Exception as e:
                st.error(f"Error: {e}")
    st.stop()

# ── Logged in ────────────────────────────────────────────────
auth_headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

col_title, col_logout = st.columns([4, 1])
with col_logout:
    if st.button("Log Out"):
        cookie_manager.delete("auth_token", key="del_auth")
        st.session_state.auth_token = None
        st.session_state.user_id = None
        st.session_state.trip_id = None
        st.rerun()

# Get or create trip
if not st.session_state.get("trip_id"):
    try:
        trips_resp = httpx.get(f"{backend_url}/trips/me", headers=auth_headers, timeout=10)
        trips_resp.raise_for_status()
        trips = trips_resp.json()
        if trips:
            st.session_state.trip_id = trips[0]["id"]
        else:
            create_resp = httpx.post(
                f"{backend_url}/trips",
                json={"name": "My Trip"},
                headers=auth_headers,
                timeout=10,
            )
            create_resp.raise_for_status()
            st.session_state.trip_id = create_resp.json()["id"]
    except Exception as e:
        st.error(f"Failed to load trip: {e}")
        st.stop()

trip_id = st.session_state.trip_id

# Load trip detail
try:
    trip_resp = httpx.get(f"{backend_url}/trips/{trip_id}", headers=auth_headers, timeout=15)
    trip_resp.raise_for_status()
    trip = trip_resp.json()
except Exception as e:
    st.error(f"Failed to load trip: {e}")
    st.stop()

restaurants = trip.get("restaurants", [])

if not restaurants:
    st.info("Your trip is empty. Search for restaurants and save them here!")
    if st.button("🔍 Go to Search"):
        st.switch_page("pages/1_Search.py")
    st.stop()

st.markdown(f"### {trip['name']} · {len(restaurants)} restaurants")

# Share + Export row
share_col, export_col = st.columns(2)
with share_col:
    if st.button("🔗 Share Trip", use_container_width=True):
        try:
            share_resp = httpx.post(
                f"{backend_url}/share",
                json={"trip_id": trip_id},
                headers=auth_headers,
                timeout=10,
            )
            share_resp.raise_for_status()
            share_url = share_resp.json()["share_url"]
            st.success(f"Share link: {share_url}")
            st.code(share_url)
        except Exception as e:
            st.error(f"Failed to create share link: {e}")

with export_col:
    if st.button("📄 Export PDF", use_container_width=True):
        try:
            pdf_resp = httpx.get(
                f"{backend_url}/export/pdf/{trip_id}",
                headers=auth_headers,
                timeout=30,
            )
            pdf_resp.raise_for_status()
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_resp.content,
                file_name=f"trip-{trip['name'].replace(' ', '-').lower()}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Failed to export PDF: {e}")

st.markdown("---")

CONFIDENCE_COLORS = {"high": "🟢", "medium": "🟡", "low": "🔴"}

for tr in restaurants:
    restaurant = tr.get("restaurant") or {}
    dishes = tr.get("dishes", [])
    place_id = tr["place_id"]

    with st.container(border=True):
        r_col, btn_col = st.columns([4, 1])
        with r_col:
            st.markdown(f"**{restaurant.get('name', place_id)}**")
            rating = restaurant.get("rating", "")
            review_count = restaurant.get("review_count", "")
            price = restaurant.get("price_level", "")
            if rating:
                st.caption(f"⭐ {rating} · {review_count:,} reviews · {price}")
            st.caption(restaurant.get("address", ""))
        with btn_col:
            if st.button("✕ Remove", key=f"remove_{place_id}"):
                try:
                    del_resp = httpx.delete(
                        f"{backend_url}/trips/{trip_id}/restaurants/{place_id}",
                        headers=auth_headers,
                        timeout=10,
                    )
                    del_resp.raise_for_status()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to remove: {e}")

        if dishes:
            with st.expander(f"🍽️ Top dishes ({len(dishes)})"):
                for dish in dishes[:5]:
                    conf = dish.get("confidence", "medium")
                    veg = " · 🥗" if dish.get("is_vegetarian") else ""
                    st.markdown(
                        f"{CONFIDENCE_COLORS[conf]} **{dish['dish_name']}**{veg} — *{dish['reason']}*"
                    )
        else:
            st.caption("No dish data available")
