-- TripBite Supabase Schema
-- Run this in the Supabase SQL editor

-- 1. Restaurant cache (populated by backend from Google Places)
CREATE TABLE IF NOT EXISTS restaurant_cache (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rating NUMERIC(2,1),
    review_count INTEGER,
    price_level TEXT,
    address TEXT,
    photo_url TEXT,
    lat NUMERIC(10,7),
    lng NUMERIC(10,7),
    cached_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Dish cache (populated by Apify + Claude pipeline)
CREATE TABLE IF NOT EXISTS dish_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id TEXT NOT NULL REFERENCES restaurant_cache(place_id) ON DELETE CASCADE,
    dish_name TEXT NOT NULL,
    reason TEXT,
    is_vegetarian BOOLEAN DEFAULT FALSE,
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(place_id, dish_name)
);

-- 3. Trips (one per user for MVP)
CREATE TABLE IF NOT EXISTS trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'My Trip',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Trip restaurants (saved restaurants per trip)
CREATE TABLE IF NOT EXISTS trip_restaurants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    place_id TEXT NOT NULL REFERENCES restaurant_cache(place_id),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(trip_id, place_id)
);

-- 5. Share tokens
CREATE TABLE IF NOT EXISTS share_tokens (
    token TEXT PRIMARY KEY DEFAULT encode(gen_random_bytes(16), 'hex'),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- RLS Policies
-- ============================================================

-- Enable RLS on user-owned tables
ALTER TABLE trips ENABLE ROW LEVEL SECURITY;
ALTER TABLE trip_restaurants ENABLE ROW LEVEL SECURITY;
ALTER TABLE share_tokens ENABLE ROW LEVEL SECURITY;

-- Cache tables: public read, service-role write
ALTER TABLE restaurant_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE dish_cache ENABLE ROW LEVEL SECURITY;

-- restaurant_cache: anyone can read, only service role can write
CREATE POLICY "Public can read restaurant_cache"
    ON restaurant_cache FOR SELECT
    USING (true);

CREATE POLICY "Service role can upsert restaurant_cache"
    ON restaurant_cache FOR ALL
    USING (auth.role() = 'service_role');

-- dish_cache: anyone can read, only service role can write
CREATE POLICY "Public can read dish_cache"
    ON dish_cache FOR SELECT
    USING (true);

CREATE POLICY "Service role can upsert dish_cache"
    ON dish_cache FOR ALL
    USING (auth.role() = 'service_role');

-- trips: users own their own trips
CREATE POLICY "Users can manage their own trips"
    ON trips FOR ALL
    USING (auth.uid() = user_id);

-- trip_restaurants: users access via their trips
CREATE POLICY "Users can manage their trip restaurants"
    ON trip_restaurants FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = trip_restaurants.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- share_tokens: users can manage tokens for their own trips
CREATE POLICY "Users can manage share tokens for their trips"
    ON share_tokens FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM trips
            WHERE trips.id = share_tokens.trip_id
            AND trips.user_id = auth.uid()
        )
    );

-- share_tokens: public can read (for shared trip views)
CREATE POLICY "Public can read share tokens"
    ON share_tokens FOR SELECT
    USING (true);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_dish_cache_place_id ON dish_cache(place_id);
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trip_restaurants_trip_id ON trip_restaurants(trip_id);
CREATE INDEX IF NOT EXISTS idx_share_tokens_trip_id ON share_tokens(trip_id);
