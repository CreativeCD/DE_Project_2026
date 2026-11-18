-- =====================================================================
-- Uber Ride-Hailing Database: Performance Tuning Indexes (CP3)
-- Phase 4: sql/05_indexes.sql
-- Database: PostgreSQL 15+
--
-- Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
-- Author: Rusheel Chandra (Member 4)
-- Date: 19 November 2026
--
-- Optimization Philosophy:
--   1. Create indexes that serve high-frequency and bottleneck queries.
--   2. Maintain index balance: Avoid redundant indexes to minimize
--      write overhead on INSERT, UPDATE, and DELETE (W01–W05).
--   3. Follow best practices:
--      - Equality columns first, range / sorting columns second.
--      - Use Partial Indexes for skewed data (e.g. active trips, failed payments).
--      - Use Covering Indexes (INCLUDE) to enable Index Only Scans.
--      - Use Expression Indexes for functional searches (e.g. LOWER(email)).
--      - Use GIN Trigram indexes for wildcard pattern matching (ILIKE '%...%').
-- =====================================================================

SET search_path TO uber;

-- Enable trigram extension for substring searches (used in R13)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------
-- TABLE 1: riders (30,000 rows)
-- ---------------------------------------------------------------------

-- Index 1: Functional Expression Index on LOWER(email)
-- Serves: R03 (Login by email, case-insensitive)
-- Why Expression Index:
--   Baseline query uses `WHERE LOWER(email) = '...'`. A standard B-tree on `email`
--   is invalidated by the LOWER() function, forcing a full sequential scan of 30,000 riders.
--   An expression index pre-evaluates and indexes LOWER(email), turning Seq Scan
--   into an instant Index Scan.
-- Expected Scan: Index Scan using idx_riders_lower_email
DROP INDEX IF EXISTS idx_riders_lower_email;
CREATE INDEX idx_riders_lower_email ON riders (LOWER(email));

-- Index 2: B-tree Index on home_city_id
-- Serves: R09 (Win-back campaign in Bengaluru), R18 (Pune riders CRM list)
-- Why B-tree & Column Order:
--   `riders` has 30,000 rows across 10 cities. Queries filter on `home_city_id = 1`
--   or `home_city_id = 6`. This index allows PostgreSQL to isolate city riders
--   directly without scanning the entire riders table.
-- Expected Scan: Bitmap Index Scan / Index Scan
DROP INDEX IF EXISTS idx_riders_home_city;
CREATE INDEX idx_riders_home_city ON riders (home_city_id);

-- Index 3: GIN Trigram Index on full_name
-- Serves: R13 (Support search by surname: ILIKE '%sharma%')
-- Why GIN Trigram:
--   Standard B-tree indexes only support prefix searches ('sharma%') using text sorting.
--   They cannot use an index for leading wildcards ('%sharma%'). GIN with trigrams
--   breaks strings into 3-character slices, allowing rapid substring search.
-- Expected Scan: Bitmap Heap Scan using Bitmap Index Scan on idx_riders_name_trgm
DROP INDEX IF EXISTS idx_riders_name_trgm;
CREATE INDEX idx_riders_name_trgm ON riders USING gin (full_name gin_trgm_ops);


-- ---------------------------------------------------------------------
-- TABLE 2: drivers (3,000 rows)
-- ---------------------------------------------------------------------

-- Index 4: Partial Index on driver_rating for ACTIVE drivers
-- Serves: W03 (Suspend active drivers rated below 3.5)
-- Why Partial Index:
--   Only ACTIVE drivers can be suspended. Inactive or already suspended drivers
--   are irrelevant. Indexing only rows `WHERE status = 'ACTIVE'` keeps the index
--   compact and speeds up W03.
-- Expected Scan: Index Scan / Bitmap Index Scan
DROP INDEX IF EXISTS idx_drivers_active_rating;
CREATE INDEX idx_drivers_active_rating ON drivers (driver_rating)
WHERE status = 'ACTIVE';


-- ---------------------------------------------------------------------
-- TABLE 3: trips (300,000 rows - Core Transactional Table)
-- ---------------------------------------------------------------------

-- Index 5: Composite B-tree Index on (rider_id, requested_at DESC)
-- Serves: R01 (Rider app: last 20 trips), R18 (CRM: last trip per rider)
-- Why Composite & Column Order:
--   Rule: Equality first, sorting/range second.
--   PostgreSQL first jumps to the given `rider_id`, and because the index leaf pages
--   are pre-sorted by `requested_at DESC`, it simply reads the top 20 tuples and stops.
--   This completely avoids an in-memory or on-disk quicksort step.
-- Expected Scan: Index Scan using idx_trips_rider_requested
DROP INDEX IF EXISTS idx_trips_rider_requested;
CREATE INDEX idx_trips_rider_requested ON trips (rider_id, requested_at DESC);

-- Index 6: Covering Composite Index on (driver_id, status, requested_at) INCLUDE (fare_amount)
-- Serves: R02 (Driver March earnings), R07 (Top earning drivers Mumbai), R19 (Top drivers per city)
-- Why Covering (INCLUDE):
--   Equality columns `driver_id` and `status` come first, followed by the date range
--   `requested_at`. By including `fare_amount` in the leaf nodes (INCLUDE clause),
--   PostgreSQL satisfies the entire aggregation query without touching the table heap!
-- Expected Scan: Index Only Scan using idx_trips_driver_status_date
DROP INDEX IF EXISTS idx_trips_driver_status_date;
CREATE INDEX idx_trips_driver_status_date ON trips (driver_id, status, requested_at)
INCLUDE (fare_amount);

-- Index 7: Composite Index on (city_id, requested_at)
-- Serves: R04 (Bengaluru trips on specific day), R06 (Completed trips per city in June),
--         R12 (Hourly surge in Delhi), R17 (Cancellation rate per city), R23 (Active riders per city)
-- Why Composite & Column Order:
--   Filters always specify `city_id` (Equality) and narrow down by `requested_at` (Range).
--   Equality column first (`city_id`), range column second (`requested_at`).
-- Expected Scan: Bitmap Index Scan / Index Scan
DROP INDEX IF EXISTS idx_trips_city_requested;
CREATE INDEX idx_trips_city_requested ON trips (city_id, requested_at);

-- Index 8: Partial Index on active trips for Live Dispatch
-- Serves: R05 (Live dispatch screen: oldest active trips), W02 (Complete oldest ongoing trip)
-- Why Partial Index:
--   Over 90% of all trips in the database are COMPLETED or CANCELLED.
--   Active trips ('REQUESTED', 'ACCEPTED', 'ONGOING') represent less than 2% of data.
--   Indexing only active trips creates a tiny index (< 50 KB) that fits entirely in CPU L1/L2 cache,
--   allowing dispatch queries to run in < 0.1 ms (meeting the 3-second SLA easily).
-- Expected Scan: Index Scan using idx_trips_active_dispatch
DROP INDEX IF EXISTS idx_trips_active_dispatch;
CREATE INDEX idx_trips_active_dispatch ON trips (requested_at)
WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING');

-- Index 9: Partial Index for ongoing trip completion
-- Serves: W02 (`WHERE status = 'ONGOING'`)
-- Why Partial Index:
--   Subquery `SELECT min(trip_id) FROM trips WHERE status = 'ONGOING'` previously
--   scanned the entire table or PK index. This partial index finds the minimum trip_id
--   instantaneously.
-- Expected Scan: Index Scan
DROP INDEX IF EXISTS idx_trips_ongoing_min;
CREATE INDEX idx_trips_ongoing_min ON trips (trip_id)
WHERE status = 'ONGOING';

-- Index 10: Composite Index on (status, requested_at, city_id)
-- Serves: R06 (City completed trips), R19 (City rankings), R20 (Daily revenue), W05 (Retention purge)
-- Why Composite:
--   Filters by `status = 'COMPLETED'` and date range `requested_at`.
-- Expected Scan: Index Scan / Bitmap Index Scan
DROP INDEX IF EXISTS idx_trips_status_requested_city;
CREATE INDEX idx_trips_status_requested_city ON trips (status, requested_at, city_id);

-- Index 11: Partial Index on promo_code
-- Serves: R21 (Promo code usage aggregation)
-- Why Partial Index:
--   The vast majority of trips do not use promo codes (`promo_code IS NULL`).
--   Excluding NULLs with `WHERE promo_code IS NOT NULL` reduces index size by ~85%.
-- Expected Scan: Bitmap Index Scan / Index Scan
DROP INDEX IF EXISTS idx_trips_promo_code;
CREATE INDEX idx_trips_promo_code ON trips (promo_code)
WHERE promo_code IS NOT NULL;

-- Index 12: Composite Index on (driver_id, requested_at)
-- Serves: R10 (Active drivers win-back / activity check)
-- Why Composite:
--   Allows instant lookups for `NOT EXISTS (SELECT 1 FROM trips WHERE driver_id = d.driver_id AND requested_at >= ...)`
-- Expected Scan: Index Scan
DROP INDEX IF EXISTS idx_trips_driver_requested;
CREATE INDEX idx_trips_driver_requested ON trips (driver_id, requested_at);

-- Index 13: Partial Index for Long / Extreme Outlier Trips (Fraud Detection)
-- Serves: R24 (Unusually long trips: distance > 43 OR duration > 150)
-- Why Partial Index:
--   Only a tiny fraction of trips (< 0.1%) trigger fraud flags.
--   Indexing only these suspicious completed trips pre-sorted by `fare_amount DESC`
--   makes the fraud check instantaneous.
-- Expected Scan: Index Scan using idx_trips_fraud_long
DROP INDEX IF EXISTS idx_trips_fraud_long;
CREATE INDEX idx_trips_fraud_long ON trips (fare_amount DESC)
WHERE status = 'COMPLETED' AND (distance_km > 43 OR duration_min > 150);

-- Index 14: Expression + Partial Index for High Fare-per-km Trips (Fraud Detection)
-- Serves: R25 (Completed trips charging more than ₹100/km)
-- Why Expression + Partial Index:
--   The query sorts by `fare_amount / NULLIF(distance_km, 0) DESC`.
--   An expression index pre-computes this division for completed trips.
-- Expected Scan: Index Scan using idx_trips_fraud_rate
DROP INDEX IF EXISTS idx_trips_fraud_rate;
CREATE INDEX idx_trips_fraud_rate ON trips ((fare_amount / NULLIF(distance_km, 0)) DESC)
WHERE status = 'COMPLETED';


-- ---------------------------------------------------------------------
-- TABLE 4: payments (245,839 rows)
-- ---------------------------------------------------------------------

-- Index 15: Composite Index on (payment_status, paid_at)
-- Serves: R08 (Revenue per payment method per month)
-- Why Composite:
--   Filters on `payment_status = 'SUCCESS'` and ranges across `paid_at`.
-- Expected Scan: Bitmap Index Scan / Index Scan
DROP INDEX IF EXISTS idx_payments_status_paid_at;
CREATE INDEX idx_payments_status_paid_at ON payments (payment_status, paid_at);

-- Index 16: Partial Index on FAILED payments
-- Serves: R22 (Failed payments in last 7 days)
-- Why Partial Index:
--   Failed payments are rare anomalies (< 3% of all payments).
--   Indexing only `WHERE payment_status = 'FAILED'` sorted by `paid_at DESC`
--   avoids indexing 240,000 successful payments, keeping the index under 200 KB.
-- Expected Scan: Index Scan using idx_payments_failed_paid_at
DROP INDEX IF EXISTS idx_payments_failed_paid_at;
CREATE INDEX idx_payments_failed_paid_at ON payments (paid_at DESC)
WHERE payment_status = 'FAILED';


-- ---------------------------------------------------------------------
-- TABLE 5: ratings (307,214 rows)
-- ---------------------------------------------------------------------

-- Index 17: Partial Composite Index on Rider Ratings
-- Serves: R11 (Quality team: lowest-rated drivers by riders)
-- Why Partial Composite:
--   Filters on `rated_by = 'RIDER'`. Grouping by `trip_id` and pulling `stars`
--   allows rapid index scans to join with `trips.driver_id`.
-- Expected Scan: Index Scan / Bitmap Index Scan
DROP INDEX IF EXISTS idx_ratings_rider_trip;
CREATE INDEX idx_ratings_rider_trip ON ratings (trip_id, stars)
WHERE rated_by = 'RIDER';


-- ---------------------------------------------------------------------
-- Maintenance & Statistics Update
-- ---------------------------------------------------------------------
-- Fresh statistics and visibility maps ensure the PostgreSQL query planner
-- accurately picks these newly created indexes over sequential scans.
VACUUM ANALYZE;
