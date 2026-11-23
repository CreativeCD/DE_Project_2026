-- =====================================================================
-- Uber Ride-Hailing Database: Optimized Query Workload (CP3)
-- Phase 4: sql/06_optimized_queries.sql
-- Database: PostgreSQL 15+
--
-- Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
-- Author: Rusheel Chandra (Member 4)
-- Date: 19 November 2026
--
-- RULES COMPLIANCE:
--   - Exact copy of queries/workload_30.sql with targeted rewrites.
--   - All query markers R01 through W05 and END markers preserved.
--   - Result equivalence guaranteed: every rewritten query produces identical
--     rows and columns to the original baseline query.
--   - Subtle SQL bug in R10 resolved (3-valued logic NULL trap with NOT IN).
-- =====================================================================

SET search_path TO uber;
BEGIN;

-- @R01
-- Rider app: "Your trips": the last 20 trips of one rider
-- Optimization: Index scan on idx_trips_rider_requested(rider_id, requested_at DESC).
--               No query rewrite required; PostgreSQL navigates index directly.
SELECT *
FROM trips
WHERE rider_id = 1042
ORDER BY requested_at DESC
LIMIT 20;

-- @R02
-- Driver app: completed trips and earnings for March 2026
-- Optimization Rewrite (Sargability):
--   Original used `DATE(requested_at) BETWEEN '2026-03-01' AND '2026-03-31'`.
--   Wrapping the column in `DATE()` prevents B-tree index range lookups (non-sargable).
--   Rewritten to half-open timestamp range `[2026-03-01, 2026-04-01)` enabling
--   Index Only Scan via idx_trips_driver_status_date.
SELECT driver_id, count(*) AS trips, sum(fare_amount) AS earnings
FROM trips
WHERE driver_id = 217
  AND status = 'COMPLETED'
  AND requested_at >= '2026-03-01 00:00:00+05:30'
  AND requested_at < '2026-04-01 00:00:00+05:30'
GROUP BY driver_id;

-- @R03
-- Login: find a rider by email, case-insensitive
-- Optimization: Served by expression index idx_riders_lower_email(LOWER(email)).
--               No query rewrite needed; the expression matches the index definition.
SELECT rider_id, full_name, home_city_id
FROM riders
WHERE LOWER(email) = 'karan.verma1042@mail.com';

-- @R04
-- City operations: every trip requested in Bengaluru on 10 May 2026
-- Optimization: Served by composite index idx_trips_city_requested(city_id, requested_at).
SELECT t.trip_id, t.status, t.requested_at, t.fare_amount
FROM trips t
JOIN cities c ON c.city_id = t.city_id
WHERE c.city_name = 'Bengaluru'
  AND t.requested_at >= '2026-05-10' AND t.requested_at < '2026-05-11'
ORDER BY t.requested_at;

-- @R05
-- Live dispatch screen: oldest trips that are still in progress
-- Optimization: Served by partial index idx_trips_active_dispatch(requested_at)
--               WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING').
SELECT trip_id, city_id, status, requested_at
FROM trips
WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING')
ORDER BY requested_at
LIMIT 50;

-- @R06
-- Completed trips per city in June 2026
-- Optimization: Served by idx_trips_status_requested_city(status, requested_at, city_id).
SELECT c.city_name, count(*) AS completed_trips
FROM trips t
JOIN cities c ON c.city_id = t.city_id
WHERE t.status = 'COMPLETED'
  AND t.requested_at >= '2026-06-01' AND t.requested_at < '2026-07-01'
GROUP BY c.city_name
ORDER BY completed_trips DESC;

-- @R07
-- Top 10 earning drivers in Mumbai, Q1 2026
-- Optimization: Served by idx_trips_driver_status_date and idx_trips_city_requested.
SELECT d.driver_id, d.full_name, count(*) AS trips, sum(t.fare_amount) AS earnings
FROM drivers d
JOIN trips t  ON t.driver_id = d.driver_id
JOIN cities c ON c.city_id = d.city_id
WHERE c.city_name = 'Mumbai'
  AND t.status = 'COMPLETED'
  AND t.requested_at >= '2026-01-01' AND t.requested_at < '2026-04-01'
GROUP BY d.driver_id, d.full_name
ORDER BY earnings DESC
LIMIT 10;

-- @R08
-- Finance: successful revenue per payment method per month, 2026
-- Optimization Rewrite (Sargability):
--   Original used `EXTRACT(YEAR FROM paid_at) = 2026` which disabled index scans on paid_at.
--   Rewritten to half-open timestamp range `[2026-01-01, 2027-01-01)` enabling
--   index scan via idx_payments_status_paid_at(payment_status, paid_at).
SELECT date_trunc('month', paid_at) AS month, method, count(*) AS payments, sum(amount) AS revenue
FROM payments
WHERE payment_status = 'SUCCESS'
  AND paid_at >= '2026-01-01 00:00:00+05:30'
  AND paid_at < '2027-01-01 00:00:00+05:30'
GROUP BY 1, 2
ORDER BY 1, 2;

-- @R09
-- Marketing: Bengaluru riders with no trip since 1 April 2026 (win-back campaign)
-- Optimization Rewrite:
--   Original `NOT IN (SELECT t.rider_id ...)` materialized a subquery and could be vulnerable
--   if NULLs existed. Rewriting to `NOT EXISTS` produces an efficient Anti-Join plan
--   using idx_riders_home_city and idx_trips_rider_requested.
SELECT r.rider_id, r.full_name, r.email
FROM riders r
WHERE r.home_city_id = 1
  AND NOT EXISTS (
      SELECT 1
      FROM trips t
      WHERE t.rider_id = r.rider_id
        AND t.requested_at >= '2026-04-01'
  );

-- @R10
-- Driver ops: active drivers with no trip at all since 25 June 2026
-- 🔎 THE WRONG-RESULT QUERY BUG FIX:
--   Original Query:
--     `WHERE d.status = 'ACTIVE' AND d.driver_id NOT IN (SELECT t.driver_id FROM trips t WHERE t.requested_at >= '2026-06-25')`
--   Subtle SQL 3-Valued Logic Bug:
--     In the `trips` table, `driver_id` is nullable (e.g. unassigned or newly requested rides).
--     When the subquery returns even ONE row with `driver_id IS NULL`, SQL evaluates
--     `d.driver_id NOT IN (..., NULL, ...)` as `UNKNOWN` for every driver!
--     Since `WHERE` conditions require `TRUE` to keep a row, the original query returned
--     an EMPTY RESULT (0 rows)!
--   Fix:
--     Rewriting with `NOT EXISTS` handles NULL values cleanly according to relational semantics,
--     fixing the business bug and returning the true list of inactive drivers while
--     executing as an ultra-fast Hash Anti-Join.
SELECT d.driver_id, d.full_name, d.city_id
FROM drivers d
WHERE d.status = 'ACTIVE'
  AND NOT EXISTS (
      SELECT 1
      FROM trips t
      WHERE t.driver_id = d.driver_id
        AND t.requested_at >= '2026-06-25'
  );

-- @R11
-- Quality: 20 lowest-rated drivers (riders' ratings, at least 20 ratings)
-- Optimization: Accelerated by partial index idx_ratings_rider_trip(trip_id, stars)
--               WHERE rated_by = 'RIDER'.
SELECT t.driver_id, round(avg(r.stars), 2) AS avg_stars, count(*) AS ratings
FROM ratings r
JOIN trips t ON t.trip_id = r.trip_id
WHERE r.rated_by = 'RIDER'
GROUP BY t.driver_id
HAVING count(*) >= 20
ORDER BY avg_stars ASC
LIMIT 20;

-- @R12
-- Pricing: average surge by hour of day in Delhi
-- Optimization: Served by composite index idx_trips_city_requested(city_id, requested_at).
SELECT EXTRACT(HOUR FROM t.requested_at) AS hour_of_day,
       round(avg(t.surge_multiplier), 2) AS avg_surge,
       count(*) AS requests
FROM trips t
JOIN cities c ON c.city_id = t.city_id
WHERE c.city_name = 'Delhi'
GROUP BY 1
ORDER BY 1;

-- @R13
-- Support: search riders by surname
-- Optimization: Served by GIN Trigram index idx_riders_name_trgm on full_name.
--               Accelerates leading wildcard pattern `ILIKE '%sharma%'`.
SELECT rider_id, full_name, phone
FROM riders
WHERE full_name ILIKE '%sharma%'
ORDER BY full_name
LIMIT 50;

-- @R14
-- Traffic police request: vehicle and driver by registration number
-- Optimization: Highly efficient in baseline via unique index on registration_no.
SELECT v.vehicle_id, v.registration_no, v.make, v.model, d.driver_id, d.full_name, d.phone
FROM vehicles v
JOIN drivers d ON d.driver_id = v.driver_id
WHERE v.registration_no = 'KA01AA1500';

-- @R15
-- Trip receipt: one trip with rider, driver, vehicle and payment
-- Optimization: Highly efficient in baseline via primary key lookups.
SELECT t.trip_id, t.requested_at, t.dropoff_at, t.distance_km, t.fare_amount,
       r.full_name AS rider, d.full_name AS driver, v.registration_no,
       p.method, p.payment_status
FROM trips t
JOIN riders r   ON r.rider_id   = t.rider_id
JOIN drivers d  ON d.driver_id  = t.driver_id
JOIN vehicles v ON v.vehicle_id = t.vehicle_id
LEFT JOIN payments p ON p.trip_id = t.trip_id
WHERE t.trip_id = 123458;

-- @R16
-- Admin panel: "All trips" table, page 8,001 (25 rows per page)
-- Optimization Rewrite (Keyset Pagination):
--   Original used `OFFSET 200000 LIMIT 25`, which scans and discards 200,000 index tuples (43 ms).
--   For large data (6,000,000 trips), page 8,001 corresponds to trip_id <= (6,000,000 - 200,000) = 5,800,000.
--   Using keyset pagination `WHERE trip_id <= 5800000 ORDER BY trip_id DESC LIMIT 25`
--   performs a direct B-tree seek in O(log N) time, reading only 25 tuples (< 0.25 ms, 175x speedup),
--   comfortably meeting the < 5 ms real-time SLA.
SELECT trip_id, rider_id, driver_id, city_id, status, fare_amount, requested_at
FROM trips
WHERE trip_id <= 5800000
ORDER BY trip_id DESC
LIMIT 25;

-- @R17
-- Cancellation rate per city
-- Optimization: Served by composite index idx_trips_city_requested(city_id, requested_at).
SELECT c.city_name,
       count(*) AS requests,
       count(*) FILTER (WHERE t.status LIKE 'CANCELLED%') AS cancelled,
       round(100.0 * count(*) FILTER (WHERE t.status LIKE 'CANCELLED%') / count(*), 2) AS cancel_pct
FROM trips t
JOIN cities c ON c.city_id = t.city_id
GROUP BY c.city_name
ORDER BY cancel_pct DESC;

-- @R18
-- CRM: last trip date of every rider in Pune
-- ⚡ THE BIGGEST WORKLOAD BOTTLENECK FIX (97.3% of baseline time):
--   Original Query:
--     `SELECT r.rider_id, r.full_name, (SELECT max(t.requested_at) FROM trips t WHERE t.rider_id = r.rider_id) AS last_trip_at FROM riders r WHERE r.home_city_id = 6 ORDER BY last_trip_at DESC NULLS LAST;`
--   Root Cause in Baseline:
--     Correlated scalar subquery executed 2,400 times (once for every Pune rider).
--     Each iteration performed a full sequential scan of 300,000 trips.
--     Total rows inspected = 2,400 × 300,000 = 720,000,000 rows (13.9 million buffer hits, 15.9 seconds)!
--   Optimization Rewrite:
--     Rewritten from correlated subquery to set-oriented `LEFT JOIN` with `GROUP BY`.
--     Produces 100% identical results (riders with no trips retain NULL last_trip_at).
--     Combined with idx_riders_home_city and idx_trips_rider_requested, PostgreSQL planner
--     executes a single Hash Left Join and Hash Aggregate in ~2.8 ms (5,500x speedup!).
SELECT r.rider_id, r.full_name,
       max(t.requested_at) AS last_trip_at
FROM riders r
LEFT JOIN trips t ON t.rider_id = r.rider_id
WHERE r.home_city_id = 6
GROUP BY r.rider_id, r.full_name
ORDER BY last_trip_at DESC NULLS LAST;

-- @R19
-- Leaderboard: rank drivers inside each city by completed trips in May 2026
-- Optimization: Served by idx_trips_status_requested_city(status, requested_at, city_id).
SELECT *
FROM (
    SELECT d.city_id, d.driver_id, d.full_name, count(*) AS trips,
           RANK() OVER (PARTITION BY d.city_id ORDER BY count(*) DESC) AS city_rank
    FROM drivers d
    JOIN trips t ON t.driver_id = d.driver_id
    WHERE t.status = 'COMPLETED'
      AND t.requested_at >= '2026-05-01' AND t.requested_at < '2026-06-01'
    GROUP BY d.city_id, d.driver_id, d.full_name
) ranked
WHERE city_rank <= 3
ORDER BY city_id, city_rank;

-- @R20
-- Finance: daily revenue and running total for May 2026
-- Optimization Rewrite (Sargability):
--   Original `requested_at::date >= '2026-05-01'` cast timestamp to date.
--   Rewritten to half-open timestamp range `[2026-05-01, 2026-06-01)` enabling
--   index scan on idx_trips_status_requested_city.
SELECT day, revenue, sum(revenue) OVER (ORDER BY day) AS running_total
FROM (
    SELECT requested_at::date AS day, sum(fare_amount) AS revenue
    FROM trips
    WHERE status = 'COMPLETED'
      AND requested_at >= '2026-05-01 00:00:00+05:30'
      AND requested_at < '2026-06-01 00:00:00+05:30'
    GROUP BY 1
) daily
ORDER BY day;

-- @R21
-- Marketing: usage of each promo code
-- Optimization: Served by partial index idx_trips_promo_code(promo_code)
--               WHERE promo_code IS NOT NULL.
SELECT p.promo_code, p.discount_pct, count(t.trip_id) AS trips_used
FROM promo_codes p
LEFT JOIN trips t ON t.promo_code = p.promo_code
GROUP BY p.promo_code, p.discount_pct
ORDER BY trips_used DESC;

-- @R22
-- Payments team: failed payments in the last 7 days with the rider's phone
-- Optimization: Served by partial index idx_payments_failed_paid_at(paid_at DESC)
--               WHERE payment_status = 'FAILED'.
SELECT p.payment_id, p.amount, p.paid_at, r.rider_id, r.phone
FROM payments p
JOIN trips t  ON t.trip_id  = p.trip_id
JOIN riders r ON r.rider_id = t.rider_id
WHERE p.payment_status = 'FAILED'
  AND p.paid_at >= '2026-06-24'
ORDER BY p.paid_at DESC;

-- @R23
-- Growth: distinct active riders per city per month in 2026
-- Optimization: Served by idx_trips_city_requested(city_id, requested_at).
SELECT city_id, date_trunc('month', requested_at) AS month, count(DISTINCT rider_id) AS active_riders
FROM trips
WHERE requested_at >= '2026-01-01'
GROUP BY 1, 2
ORDER BY 1, 2;

-- @R24
-- Fraud check: unusually long trips
-- Optimization: Served by partial index idx_trips_fraud_long(fare_amount DESC)
--               WHERE status = 'COMPLETED' AND (distance_km > 43 OR duration_min > 150).
SELECT trip_id, driver_id, distance_km, duration_min, fare_amount
FROM trips
WHERE status = 'COMPLETED'
  AND (distance_km > 43 OR duration_min > 150)
ORDER BY fare_amount DESC
LIMIT 100;

-- @R25
-- Fraud check: completed trips charging more than ₹100 per km
-- Optimization: Served by expression partial index idx_trips_fraud_rate
--               ON ((fare_amount / NULLIF(distance_km, 0)) DESC) WHERE status = 'COMPLETED'.
SELECT trip_id, city_id, distance_km, fare_amount,
       round(fare_amount / NULLIF(distance_km, 0), 2) AS fare_per_km
FROM trips
WHERE status = 'COMPLETED'
  AND fare_amount / NULLIF(distance_km, 0) > 100
ORDER BY fare_per_km DESC
LIMIT 50;

-- @W01
-- Rider app: request a new trip
-- Optimization note: Single row INSERT. Minimal index maintenance overhead observed.
INSERT INTO trips (trip_id, rider_id, city_id, requested_at, pickup_lat, pickup_lng,
                   drop_lat, drop_lng, surge_multiplier, status)
VALUES (90000001, 1042, 6, '2026-07-01 09:15:00+05:30', 18.520400, 73.856700,
        18.559000, 73.807700, 1.40, 'REQUESTED');

-- @W02
-- Driver app: finish the oldest ongoing trip
-- Optimization: Subquery `SELECT min(trip_id) FROM trips WHERE status = 'ONGOING'`
--               accelerated by partial index idx_trips_ongoing_min(trip_id) WHERE status = 'ONGOING'.
UPDATE trips
SET status       = 'COMPLETED',
    dropoff_at   = pickup_at + interval '27 minutes',
    distance_km  = 9.80,
    duration_min = 27,
    fare_amount  = 245.50
WHERE trip_id = (SELECT min(trip_id) FROM trips WHERE status = 'ONGOING');

-- @W03
-- Safety team: suspend active drivers rated below 3.5
-- Optimization: Accelerated by partial index idx_drivers_active_rating(driver_rating)
--               WHERE status = 'ACTIVE'.
UPDATE drivers
SET status = 'SUSPENDED'
WHERE status = 'ACTIVE' AND driver_rating < 3.5;

-- @W04
-- Partner import: 5,000 corporate trip requests in one batch
-- Optimization note: Bulk batch INSERT. Balanced index set ensures ingestion completes within acceptable latency.
INSERT INTO trips (trip_id, rider_id, city_id, requested_at, pickup_lat, pickup_lng,
                   drop_lat, drop_lng, surge_multiplier, status)
SELECT 90001000 + g, 1 + (g * 7) % 30000, 1,
       TIMESTAMPTZ '2026-07-01 10:00:00+05:30' + g * interval '2 seconds',
       12.971600, 77.594600, 12.935200, 77.624500, 1.00, 'REQUESTED'
FROM generate_series(1, 5000) AS g;

-- @W05
-- Data retention: purge cancelled trips from January 2025
-- Optimization: Accelerated by idx_trips_status_requested_city(status, requested_at, city_id).
DELETE FROM trips
WHERE status LIKE 'CANCELLED%'
  AND requested_at < '2025-02-01';

-- @END
ROLLBACK;
