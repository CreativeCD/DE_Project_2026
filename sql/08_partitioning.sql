-- =====================================================================
-- Uber Ride-Hailing Database: Table Partitioning Architecture (CP4)
-- File: sql/08_partitioning.sql
-- Database: PostgreSQL 15+
--
-- Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
-- Date: 23 November 2026
--
-- PARTITIONING DESIGN SPECIFICATION:
--   1. Target Table: `trips` (Accounts for ~85% of total database storage)
--   2. Partitioning Strategy: RANGE Partitioning by `requested_at`
--   3. Partition Granularity: Monthly partitions (2025-01 through 2026-12)
--      plus a DEFAULT catch-all partition.
--
-- WHY RANGE PARTITIONING ON `requested_at`?
--   a) Query Pruning: Over 70% of high-volume workload queries filter by date
--      ranges (R02, R04, R06, R07, R10, R12, R19, R20, R23, W05).
--      PostgreSQL planner eliminates non-matching partitions during plan time
--      and run time, reading only 1/18th to 1/24th of the table.
--   b) Zero-Cost Data Lifecycle & Retention: Purging old data (W05: purge trips
--      older than a certain date) becomes an instant metadata operation:
--      `ALTER TABLE trips DETACH PARTITION ...; DROP TABLE ...;` taking 1 ms
--      instead of scanning millions of rows and generating massive WAL bloat.
--   c) Maintenance & VACUUM Isolation: Autovacuum operates independently on
--      individual partitions. Old closed months become read-only and freeze,
--      preventing transaction ID wraparound without churning active pages.
--
-- THE POSTGRESQL PRIMARY KEY RULE ON PARTITIONED TABLES:
--   In PostgreSQL, any PRIMARY KEY or UNIQUE constraint on a partitioned
--   table MUST include all partition key columns.
--   Therefore, the primary key cannot simply be `PRIMARY KEY (trip_id)`;
--   it MUST be composite: `PRIMARY KEY (trip_id, requested_at)`.
--   Reason: Each partition maintains its own local B-tree index. To enforce
--   uniqueness without cross-partition global index locking, the partition key
--   must be part of the tuple identifier.
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS uber;
SET search_path TO uber;

-- ---------------------------------------------------------------------
-- 1. Create the Partitioned Master Table
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS trips_partitioned CASCADE;

CREATE TABLE trips_partitioned (
    trip_id           BIGINT NOT NULL,
    rider_id          INT NOT NULL REFERENCES riders(rider_id) ON DELETE RESTRICT,
    driver_id         INT REFERENCES drivers(driver_id) ON DELETE RESTRICT,
    vehicle_id        INT REFERENCES vehicles(vehicle_id) ON DELETE RESTRICT,
    city_id           INT NOT NULL REFERENCES cities(city_id) ON DELETE RESTRICT,
    promo_code        VARCHAR(20) REFERENCES promo_codes(promo_code) ON DELETE SET NULL,
    requested_at      TIMESTAMPTZ NOT NULL,
    pickup_at         TIMESTAMPTZ,
    dropoff_at        TIMESTAMPTZ,
    pickup_lat        NUMERIC(9, 6) NOT NULL CHECK (pickup_lat BETWEEN -90.000000 AND 90.000000),
    pickup_lng        NUMERIC(9, 6) NOT NULL CHECK (pickup_lng BETWEEN -180.000000 AND 180.000000),
    drop_lat          NUMERIC(9, 6) NOT NULL CHECK (drop_lat BETWEEN -90.000000 AND 90.000000),
    drop_lng          NUMERIC(9, 6) NOT NULL CHECK (drop_lng BETWEEN -180.000000 AND 180.000000),
    distance_km       NUMERIC(6, 2) CHECK (distance_km IS NULL OR distance_km >= 0),
    duration_min      INT CHECK (duration_min IS NULL OR duration_min >= 0),
    surge_multiplier  NUMERIC(4, 2) NOT NULL DEFAULT 1.00 CHECK (surge_multiplier >= 1.00),
    fare_amount       NUMERIC(8, 2) CHECK (fare_amount IS NULL OR fare_amount >= 0),
    status            VARCHAR(25) NOT NULL CHECK (status IN (
                          'REQUESTED', 'ACCEPTED', 'ONGOING', 'COMPLETED',
                          'CANCELLED_BY_RIDER', 'CANCELLED_BY_DRIVER'
                      )),
    -- PostgreSQL Partitioning Constraint Rule: Partition key MUST be part of PK
    CONSTRAINT pk_trips_partitioned PRIMARY KEY (trip_id, requested_at),
    CONSTRAINT chk_part_pickup_time CHECK (pickup_at IS NULL OR pickup_at >= requested_at),
    CONSTRAINT chk_part_dropoff_time CHECK (dropoff_at IS NULL OR (pickup_at IS NOT NULL AND dropoff_at >= pickup_at)),
    CONSTRAINT chk_part_completed_attrs CHECK (
        status != 'COMPLETED' OR (
            driver_id IS NOT NULL AND
            vehicle_id IS NOT NULL AND
            pickup_at IS NOT NULL AND
            dropoff_at IS NOT NULL AND
            distance_km IS NOT NULL AND
            duration_min IS NOT NULL AND
            fare_amount IS NOT NULL
        )
    )
) PARTITION BY RANGE (requested_at);

-- ---------------------------------------------------------------------
-- 2. Create Monthly Partitions (2025-01 through 2026-12)
-- ---------------------------------------------------------------------

-- Year 2025 Partitions
CREATE TABLE trips_y2025m01 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-01-01 00:00:00+05:30') TO ('2025-02-01 00:00:00+05:30');
CREATE TABLE trips_y2025m02 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-02-01 00:00:00+05:30') TO ('2025-03-01 00:00:00+05:30');
CREATE TABLE trips_y2025m03 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-03-01 00:00:00+05:30') TO ('2025-04-01 00:00:00+05:30');
CREATE TABLE trips_y2025m04 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-04-01 00:00:00+05:30') TO ('2025-05-01 00:00:00+05:30');
CREATE TABLE trips_y2025m05 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-05-01 00:00:00+05:30') TO ('2025-06-01 00:00:00+05:30');
CREATE TABLE trips_y2025m06 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-06-01 00:00:00+05:30') TO ('2025-07-01 00:00:00+05:30');
CREATE TABLE trips_y2025m07 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-07-01 00:00:00+05:30') TO ('2025-08-01 00:00:00+05:30');
CREATE TABLE trips_y2025m08 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-08-01 00:00:00+05:30') TO ('2025-09-01 00:00:00+05:30');
CREATE TABLE trips_y2025m09 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-09-01 00:00:00+05:30') TO ('2025-10-01 00:00:00+05:30');
CREATE TABLE trips_y2025m10 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-10-01 00:00:00+05:30') TO ('2025-11-01 00:00:00+05:30');
CREATE TABLE trips_y2025m11 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-11-01 00:00:00+05:30') TO ('2025-12-01 00:00:00+05:30');
CREATE TABLE trips_y2025m12 PARTITION OF trips_partitioned FOR VALUES FROM ('2025-12-01 00:00:00+05:30') TO ('2026-01-01 00:00:00+05:30');

-- Year 2026 Partitions
CREATE TABLE trips_y2026m01 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-01-01 00:00:00+05:30') TO ('2026-02-01 00:00:00+05:30');
CREATE TABLE trips_y2026m02 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-02-01 00:00:00+05:30') TO ('2026-03-01 00:00:00+05:30');
CREATE TABLE trips_y2026m03 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-03-01 00:00:00+05:30') TO ('2026-04-01 00:00:00+05:30');
CREATE TABLE trips_y2026m04 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-04-01 00:00:00+05:30') TO ('2026-05-01 00:00:00+05:30');
CREATE TABLE trips_y2026m05 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-05-01 00:00:00+05:30') TO ('2026-06-01 00:00:00+05:30');
CREATE TABLE trips_y2026m06 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-06-01 00:00:00+05:30') TO ('2026-07-01 00:00:00+05:30');
CREATE TABLE trips_y2026m07 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-07-01 00:00:00+05:30') TO ('2026-08-01 00:00:00+05:30');
CREATE TABLE trips_y2026m08 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-08-01 00:00:00+05:30') TO ('2026-09-01 00:00:00+05:30');
CREATE TABLE trips_y2026m09 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-09-01 00:00:00+05:30') TO ('2026-10-01 00:00:00+05:30');
CREATE TABLE trips_y2026m10 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-10-01 00:00:00+05:30') TO ('2026-11-01 00:00:00+05:30');
CREATE TABLE trips_y2026m11 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-11-01 00:00:00+05:30') TO ('2026-12-01 00:00:00+05:30');
CREATE TABLE trips_y2026m12 PARTITION OF trips_partitioned FOR VALUES FROM ('2026-12-01 00:00:00+05:30') TO ('2027-01-01 00:00:00+05:30');

-- Default Catch-All Partition for Future / Boundary Rides
CREATE TABLE trips_default PARTITION OF trips_partitioned DEFAULT;

-- ---------------------------------------------------------------------
-- 3. Local Partition Indexes (Propagated Automatically to Partitions)
-- ---------------------------------------------------------------------

-- Local Index 1: Composite on (rider_id, requested_at DESC)
CREATE INDEX idx_trips_part_rider_requested
ON trips_partitioned (rider_id, requested_at DESC);

-- Local Index 2: Covering Composite on (driver_id, status, requested_at) INCLUDE (fare_amount)
CREATE INDEX idx_trips_part_driver_status_date
ON trips_partitioned (driver_id, status, requested_at)
INCLUDE (fare_amount);

-- Local Index 3: Composite on (city_id, requested_at)
CREATE INDEX idx_trips_part_city_requested
ON trips_partitioned (city_id, requested_at);

-- Local Index 4: Partial index on Active Trips
CREATE INDEX idx_trips_part_active_dispatch
ON trips_partitioned (requested_at)
WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING');

-- ---------------------------------------------------------------------
-- 4. Partition Pruning Proof & Verification Queries
-- ---------------------------------------------------------------------

-- Ensure partition pruning is enabled in PostgreSQL
SET enable_partition_pruning = on;

-- PRUNING PROOF 1: Single Month Query (June 2026 - R06)
-- Expected: Scans ONLY `trips_y2026m06`, prunes all other 24 partitions!
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.city_name, count(*) AS completed_trips
FROM trips_partitioned t
JOIN cities c ON c.city_id = t.city_id
WHERE t.status = 'COMPLETED'
  AND t.requested_at >= '2026-06-01 00:00:00+05:30'
  AND t.requested_at < '2026-07-01 00:00:00+05:30'
GROUP BY c.city_name;

-- PRUNING PROOF 2: Single Day Query in Bengaluru (May 10, 2026 - R04)
-- Expected: Scans ONLY `trips_y2026m05`, prunes all other 24 partitions!
EXPLAIN (ANALYZE, BUFFERS)
SELECT t.trip_id, t.status, t.requested_at, t.fare_amount
FROM trips_partitioned t
JOIN cities c ON c.city_id = t.city_id
WHERE c.city_name = 'Bengaluru'
  AND t.requested_at >= '2026-05-10 00:00:00+05:30'
  AND t.requested_at < '2026-05-11 00:00:00+05:30'
ORDER BY t.requested_at;

-- PRUNING PROOF 3: Instant Data Lifecycle Archival (W05 Alternative)
-- Demonstrating O(1) instantaneous metadata purge without DELETE scanning:
-- ALTER TABLE trips_partitioned DETACH PARTITION trips_y2025m01;
-- DROP TABLE trips_y2025m01;
