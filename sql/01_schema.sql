-- =====================================================================
-- Uber Ride-Hailing Database Schema
-- Phase 2: sql/01_schema.sql
-- Database: PostgreSQL 15+
--
-- Tables:
--   1. cities
--   2. riders
--   3. drivers
--   4. vehicles
--   5. promo_codes
--   6. trips
--   7. payments
--   8. ratings
--
-- Rules:
--   - Schema name: uber
--   - Only constraints (PK, FK, UNIQUE, NOT NULL, CHECK)
--   - No secondary indexes (baseline state for Phase 3)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS uber;
SET search_path TO uber;

-- Clean up existing tables for idempotent execution
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS promo_codes CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;
DROP TABLE IF EXISTS riders CASCADE;
DROP TABLE IF EXISTS cities CASCADE;

-- ---------------------------------------------------------------------
-- 1. CITIES
-- ---------------------------------------------------------------------
CREATE TABLE cities (
    city_id       INT PRIMARY KEY,
    city_name     VARCHAR(50) NOT NULL UNIQUE,
    state         VARCHAR(50) NOT NULL,
    base_fare     NUMERIC(6, 2) NOT NULL CHECK (base_fare >= 0),
    per_km_rate   NUMERIC(6, 2) NOT NULL CHECK (per_km_rate >= 0),
    per_min_rate  NUMERIC(6, 2) NOT NULL CHECK (per_min_rate >= 0),
    launched_on   DATE NOT NULL
);

-- ---------------------------------------------------------------------
-- 2. RIDERS
-- ---------------------------------------------------------------------
CREATE TABLE riders (
    rider_id      INT PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    phone         VARCHAR(15) NOT NULL UNIQUE,
    home_city_id  INT NOT NULL REFERENCES cities(city_id) ON DELETE RESTRICT,
    signup_date   DATE NOT NULL,
    rider_rating  NUMERIC(3, 2) CHECK (rider_rating IS NULL OR (rider_rating >= 1.00 AND rider_rating <= 5.00)),
    is_active     BOOLEAN NOT NULL DEFAULT true
);

-- ---------------------------------------------------------------------
-- 3. DRIVERS
-- ---------------------------------------------------------------------
CREATE TABLE drivers (
    driver_id      INT PRIMARY KEY,
    full_name      VARCHAR(100) NOT NULL,
    phone          VARCHAR(15) NOT NULL UNIQUE,
    license_no     VARCHAR(25) NOT NULL UNIQUE,
    city_id        INT NOT NULL REFERENCES cities(city_id) ON DELETE RESTRICT,
    joined_on      DATE NOT NULL,
    driver_rating  NUMERIC(3, 2) NOT NULL CHECK (driver_rating >= 1.00 AND driver_rating <= 5.00),
    status         VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE', 'SUSPENDED'))
);

-- ---------------------------------------------------------------------
-- 4. VEHICLES
-- ---------------------------------------------------------------------
CREATE TABLE vehicles (
    vehicle_id        INT PRIMARY KEY,
    driver_id         INT NOT NULL REFERENCES drivers(driver_id) ON DELETE RESTRICT,
    registration_no   VARCHAR(15) NOT NULL UNIQUE,
    make              VARCHAR(50) NOT NULL,
    model             VARCHAR(50) NOT NULL,
    manufacture_year  INT NOT NULL CHECK (manufacture_year BETWEEN 2000 AND 2030),
    vehicle_type      VARCHAR(20) NOT NULL CHECK (vehicle_type IN ('BIKE', 'AUTO', 'MINI', 'SEDAN', 'SUV')),
    seat_capacity     SMALLINT NOT NULL CHECK (seat_capacity BETWEEN 1 AND 10),
    CONSTRAINT chk_vehicle_seat_type CHECK (
        (vehicle_type = 'BIKE' AND seat_capacity = 1) OR
        (vehicle_type = 'AUTO' AND seat_capacity = 3) OR
        (vehicle_type IN ('MINI', 'SEDAN') AND seat_capacity = 4) OR
        (vehicle_type = 'SUV' AND seat_capacity IN (6, 7))
    )
);

-- ---------------------------------------------------------------------
-- 5. PROMO CODES
-- ---------------------------------------------------------------------
CREATE TABLE promo_codes (
    promo_code    VARCHAR(20) PRIMARY KEY,
    discount_pct  INT NOT NULL CHECK (discount_pct > 0 AND discount_pct <= 100),
    max_discount  NUMERIC(8, 2) NOT NULL CHECK (max_discount > 0),
    valid_from    DATE NOT NULL,
    valid_to      DATE NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT true,
    CONSTRAINT chk_promo_dates CHECK (valid_to >= valid_from)
);

-- ---------------------------------------------------------------------
-- 6. TRIPS
-- ---------------------------------------------------------------------
CREATE TABLE trips (
    trip_id           BIGINT PRIMARY KEY,
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
    CONSTRAINT chk_trip_pickup_time CHECK (pickup_at IS NULL OR pickup_at >= requested_at),
    CONSTRAINT chk_trip_dropoff_time CHECK (dropoff_at IS NULL OR (pickup_at IS NOT NULL AND dropoff_at >= pickup_at)),
    CONSTRAINT chk_completed_trip_attributes CHECK (
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
);

-- ---------------------------------------------------------------------
-- 7. PAYMENTS
-- ---------------------------------------------------------------------
CREATE TABLE payments (
    payment_id      INT PRIMARY KEY,
    trip_id         BIGINT NOT NULL UNIQUE REFERENCES trips(trip_id) ON DELETE RESTRICT,
    amount          NUMERIC(8, 2) NOT NULL CHECK (amount >= 0),
    method          VARCHAR(20) NOT NULL CHECK (method IN ('CASH', 'UPI', 'CARD', 'WALLET')),
    payment_status  VARCHAR(20) NOT NULL CHECK (payment_status IN ('SUCCESS', 'FAILED', 'REFUNDED')),
    paid_at         TIMESTAMPTZ NOT NULL
);

-- ---------------------------------------------------------------------
-- 8. RATINGS
-- ---------------------------------------------------------------------
CREATE TABLE ratings (
    trip_id     BIGINT NOT NULL REFERENCES trips(trip_id) ON DELETE CASCADE,
    rated_by    VARCHAR(10) NOT NULL CHECK (rated_by IN ('RIDER', 'DRIVER')),
    stars       SMALLINT NOT NULL CHECK (stars BETWEEN 1 AND 5),
    comment     VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (trip_id, rated_by)
);
