# 🍽️ TripBite

A solo traveler restaurant discovery app. Search by city and cuisine, get top-rated restaurants (4.5★+ · 1,000+ reviews), and see AI-extracted top dishes pulled from real reviews. Save restaurants to a trip list you can share or export as PDF.

Built as part of the [100x Engineers / Applied AI Mastery](https://100xengineers.com) course.

---

## Features

- **Restaurant Search** — Google Places API filtered to 4.5★+ with 1,000+ reviews
- **AI Dish Extraction** — Apify scrapes Google Maps reviews → Claude extracts top dishes with confidence levels
- **Trip List** — Save restaurants to a personal trip, remove them, view top dishes inline
- **Share Link** — Generate a public read-only link to your trip
- **PDF Export** — Download your trip as a formatted PDF
- **Auth** — Email/password signup + login via Supabase Auth
- **Welcome Email** — Onboarding email sent via Resend on signup
- **Mock Mode** — All external services have `USE_MOCK_*` flags for local dev without API keys

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Database | Supabase (Postgres + Auth + RLS) |
| Restaurant data | Google Places API (New) |
| Review scraping | Apify (`compass/google-maps-reviews-scraper`) |
| Dish extraction | Anthropic Claude (`claude-sonnet-4-6`) |
| PDF generation | WeasyPrint + Jinja2 |
| Email | Resend |

---

## Project Structure

```
trip-bite/
├── backend/
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Pydantic BaseSettings (env vars)
│   ├── models.py                 # Pydantic request/response models
│   ├── routers/
│   │   ├── restaurants.py        # GET /restaurants/search, /restaurants/{id}
│   │   ├── dishes.py             # GET /dishes/{place_id}
│   │   ├── trips.py              # CRUD /trips
│   │   ├── share.py              # POST /share, GET /share/{token}
│   │   ├── export.py             # GET /export/pdf/{trip_id}
│   │   └── auth.py               # POST /auth/signup, /auth/login
│   ├── services/
│   │   ├── google_places.py
│   │   ├── apify_service.py
│   │   ├── claude_ai.py
│   │   ├── supabase_client.py
│   │   ├── pdf_service.py
│   │   └── email_service.py
│   └── templates/
│       └── trip_pdf.html
├── frontend/
│   ├── app.py                    # Streamlit entry point
│   └── pages/
│       ├── 1_Search.py
│       ├── 2_Restaurant.py
│       ├── 3_My_Trip.py
│       └── 4_Shared_Trip.py
├── supabase/
│   └── schema.sql                # DDL + RLS policies
├── requirements.txt
└── .env.example
```

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/sandeepnunna90/trip-bite.git
cd trip-bite
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 3. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Open the SQL Editor and run `supabase/schema.sql`
3. Copy your project URL, anon key, and service role key into `.env`

### 4. Run

```bash
# Backend (from trip-bite/)
uvicorn backend.main:app --reload

# Frontend (new terminal, from trip-bite/)
streamlit run frontend/app.py
```

Backend runs at `http://localhost:8000` · Frontend at `http://localhost:8501`

---

## Mock Mode (no API keys needed)

Set any of these in `.env` to use fake data:

```env
USE_MOCK_GOOGLE=true    # 5 hardcoded Nashville BBQ restaurants
USE_MOCK_APIFY=true     # 20 fake reviews for any place_id
USE_MOCK_CLAUDE=true    # 7 fake dish objects
USE_MOCK_RESEND=true    # logs welcome email to console
```

---

## API Keys Required

| Service | Where to get it |
|---------|----------------|
| Google Places API | [Google Cloud Console](https://console.cloud.google.com) — enable "Places API (New)" |
| Supabase | [supabase.com](https://supabase.com) — project settings |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) |
| Apify | [apify.com](https://apify.com) — account settings |
| Resend | [resend.com](https://resend.com) |

---

## API Reference

```
GET  /health
GET  /restaurants/search?city=Nashville&cuisine=BBQ
GET  /restaurants/{place_id}
GET  /dishes/{place_id}
POST /auth/signup
POST /auth/login
POST /trips
GET  /trips/me
GET  /trips/{trip_id}
POST /trips/{trip_id}/restaurants
DELETE /trips/{trip_id}/restaurants/{place_id}
POST /share
GET  /share/{token}
GET  /export/pdf/{trip_id}
```

Interactive docs at `http://localhost:8000/docs`
