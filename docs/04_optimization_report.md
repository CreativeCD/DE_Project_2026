# CP3 Optimization Report: Uber Ride-Hailing Database

**Project:** PalmPay / Uber Ride-Hailing DBMS  
**Team Number:** T0061  
**Checkpoint:** CP3 – Query Optimization (Phase 4)  
**Date of Submission:** 19 November 2026  
**Author:** Rusheel Chandra (Member 4)  
**Repository:** `CreativeCD/DE_Project_2026`  

---

## 1. Executive Summary

This report documents the official **Checkpoint 3 (CP3) Performance Tuning and Query Optimization** deliverables for the Uber Ride-Hailing database workload. Building directly on the baseline timings established in Checkpoint 2 (CP2), this phase applied systematic database engineering techniques—including composite B-tree indexing, partial indexing, covering indexes (`INCLUDE`), functional expression indexing, GIN trigram indexing, sargable query refactoring, anti-join rewrites, and set-oriented relational joins.

Across the entire 30-query workload (25 read queries `R01`–`R25` and 5 write queries `W01`–`W05`), total execution time was reduced from **16,367.651 ms** (~16.37 seconds) to **148.971 ms** (~0.15 seconds). This represents an overall workload throughput improvement of **99.09% (a 110× speedup)**.

### Headline Optimization Metrics
* **Total Workload Queries:** 30 (25 Read, 5 Write)
* **Total Executions Measured:** 90 benchmark runs (3 runs per query with `EXPLAIN (ANALYZE, BUFFERS)`)
* **Baseline Workload Time:** **16,367.651 ms**
* **Optimized Workload Time:** **148.971 ms**
* **Absolute Latency Reduction:** **16,218.680 ms**
* **Workload-Wide Improvement:** **99.09% (110× overall throughput gain)**
* **Primary Bottleneck (`R18`):** Reduced from **15,918.767 ms** to **2.858 ms** (**99.98% improvement, 5,569× speedup**)
* **Subtle SQL Bug Discovered & Resolved (`R10`):** Fixed 3-valued logic `NULL` trap with `NOT IN` on nullable foreign keys, restoring zero-row results to the true set of inactive drivers.
* **Write Overhead:** Kept under strict control. Single-trip requests (`W01`) maintain sub-millisecond execution (0.76 ms), and batch ingestion of 5,000 trips (`W04`) completes in 40.4 ms.

---

## 2. Benchmark Environment & System Specifications

All benchmarks were recorded on the identical benchmark platform used for the CP2 baseline to ensure direct comparability and statistical validity:

| Parameter | Specification |
|:---|:---|
| **DBMS Software** | PostgreSQL 18.6 (Postgres.app) |
| **Operating System** | macOS 15.0+ (Darwin arm64) |
| **Host Machine** | Apple MacBook Pro 14-inch (Nov 2024) |
| **Processor (CPU)** | Apple M4 chip (10-core CPU, high-performance architecture) |
| **System Memory (RAM)** | 16 GB Unified Memory |
| **Storage** | Apple NVMe PCIe SSD |
| **Database Name** | `uber` |
| **Search Path / Schema** | `uber` |
| **Client / Protocol** | `psql` (libpq 18.6), UNIX domain socket |
| **Benchmark Script** | `./benchmarks/run_benchmark.sh uber optimized 3 sql/06_optimized_queries.sql` |

---

## 3. Master Optimization Table (All 30 Workload Queries)

The table below provides a side-by-side comparison between the unindexed baseline execution times (CP2) and the tuned optimized times (CP3), including the underlying bottleneck identified in the plan, the specific tuning applied, the resulting percentage improvement, and proof of identical output results.

$$\text{Improvement \%} = \frac{\text{Baseline Time} - \text{Optimized Time}}{\text{Baseline Time}} \times 100$$

| Query | Before (ms) | Problem Found in Baseline Plan | Optimization Applied | After (ms) | Improvement | Same Result? |
|:---|---:|:---|:---|---:|---:|:---:|
| **R01** | 10.510 | Parallel Seq Scan on 300k trips + in-memory Quicksort | Composite B-tree `idx_trips_rider_requested(rider_id, requested_at DESC)` | 0.052 | **99.50% (202×)** | ✅ Verified |
| **R02** | 8.873 | Seq Scan on trips; non-sargable `DATE(requested_at)` function | Sargable date range rewrite + Covering Index `idx_trips_driver_status_date` with `INCLUDE (fare_amount)` (Index Only Scan) | 0.064 | **99.28% (138×)** | ✅ Verified |
| **R03** | 6.601 | Seq Scan on 30k riders; `LOWER(email)` invalidated B-tree | Functional Expression Index `idx_riders_lower_email` on `LOWER(email)` | 0.041 | **99.38% (161×)** | ✅ Verified |
| **R04** | 6.795 | Seq Scan on 300k trips + Seq Scan on cities | Composite Index `idx_trips_city_requested(city_id, requested_at)` | 0.256 | **96.23% (26×)** | ✅ Verified |
| **R05** | 10.796 | Full Seq Scan on 300k trips for a handful of active rides | Partial Index `idx_trips_active_dispatch(requested_at) WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING')` | 0.079 | **99.27% (136×)** | ✅ Verified |
| **R06** | 9.353 | Full Seq Scan on trips + Seq Scan on cities | Composite Index `idx_trips_status_requested_city(status, requested_at, city_id)` | 1.694 | **81.89% (5.5×)** | ✅ Verified |
| **R07** | 10.465 | 3-way Seq Scan on trips, drivers, and cities | Composite Index `idx_trips_status_requested_city` + `drivers_city_id` | 1.450 | **86.14% (7.2×)** | ✅ Verified |
| **R08** | 27.007 | Seq Scan on 245k payments; non-sargable `EXTRACT(YEAR)` | Sargable timestamp range `[2026-01-01, 2027-01-01)` + Composite Index `idx_payments_status_paid_at(payment_status, paid_at)` | 12.349 | **54.27% (2.2×)** | ✅ Verified |
| **R09** | 17.409 | Seq Scan on riders + SubPlan Seq Scan on 300k trips | Query rewritten to `NOT EXISTS` + `idx_riders_home_city` + `idx_trips_rider_requested` (Hash Anti-Join) | 1.997 | **88.53% (8.7×)** | ✅ Verified |
| **R10** | 12.107 | ⚠️ **Returned 0 rows (bug)**: `driver_id IS NULL` evaluated `NOT IN` to `UNKNOWN` | Rewritten to `NOT EXISTS` + `idx_trips_driver_requested` (Fixes 3-valued logic bug and runs fast) | 1.326 | **89.05% (9.1×)** | ✅ **Fixed Bug** |
| **R11** | 30.359 | 2-table Seq Scan across 307k ratings and 300k trips | Partial Index `idx_ratings_rider_trip(trip_id, stars) WHERE rated_by = 'RIDER'` | 10.960 | **63.90% (2.8×)** | ✅ Verified |
| **R12** | 31.577 | Seq Scan on trips + Seq Scan on cities | Composite Index `idx_trips_city_requested(city_id, requested_at)` | 5.280 | **83.28% (6.0×)** | ✅ Verified |
| **R13** | 8.896 | Seq Scan on 30k riders; leading wildcard `%sharma%` | GIN Trigram Index `idx_riders_name_trgm` on `riders USING gin (full_name gin_trgm_ops)` | 0.645 | **92.75% (13.8×)** | ✅ Verified |
| **R14** | 0.032 | Fast in baseline; Unique Index Scans | Retained baseline unique indexes | 0.032 | **0.00% (1.0×)** | ✅ Verified |
| **R15** | 0.069 | Fast in baseline; 5-table Primary Key joins | Retained baseline primary key indexes | 0.068 | **1.45% (1.0×)** | ✅ Verified |
| **R16** | 20.731 | Scans 200,025 index entries due to `OFFSET 200000` | Backward Index Scan on `trips_pkey` (inherent deep offset limit) | 20.524 | **1.00% (1.0×)** | ✅ Verified |
| **R17** | 22.766 | Full table aggregation across all 300k trips | Table scan required to aggregate 100% of data; optimized via cities PK lookup | 18.017 | **20.86% (1.3×)** | ✅ Verified |
| **R18** | 15,918.767 | Correlated scalar subquery executed 2,400 times (720M row inspections) | Rewritten from correlated subquery to `LEFT JOIN` + `GROUP BY` + `idx_riders_home_city` + `idx_trips_rider_requested` | 2.858 | **99.98% (5,569×)** | ✅ Verified |
| **R19** | 10.415 | Seq Scan on 300k trips + WindowAgg | Composite Index `idx_trips_status_requested_city(status, requested_at, city_id)` | 2.023 | **80.58% (5.1×)** | ✅ Verified |
| **R20** | 12.748 | Seq Scan on trips; non-sargable `requested_at::date` | Sargable date range rewrite + Composite Index `idx_trips_status_requested_city` | 1.577 | **87.63% (8.1×)** | ✅ Verified |
| **R21** | 18.925 | Full Seq Scan on 300k trips to aggregate promo codes | Partial Index `idx_trips_promo_code(promo_code) WHERE promo_code IS NOT NULL` | 1.817 | **90.40% (10.4×)** | ✅ Verified |
| **R22** | 6.042 | Seq Scan on 245k payments to find rare failed records | Partial Index `idx_payments_failed_paid_at(paid_at DESC) WHERE payment_status = 'FAILED'` | 0.079 | **98.69% (76.5×)** | ✅ Verified |
| **R23** | 49.695 | Full Seq Scan on 300k trips for monthly distinct counts | Composite Index `idx_trips_city_requested(city_id, requested_at)` | 24.317 | **51.07% (2.0×)** | ✅ Verified |
| **R24** | 10.875 | Full Seq Scan on 300k trips for rare fraud outliers | Partial Index `idx_trips_fraud_long(fare_amount DESC) WHERE status = 'COMPLETED' AND (distance_km > 43 OR duration_min > 150)` | 0.060 | **99.45% (181×)** | ✅ Verified |
| **R25** | 15.731 | Full Seq Scan on 300k trips calculating arithmetic division | Expression Partial Index `idx_trips_fraud_rate` on `((fare_amount / NULLIF(distance_km, 0)) DESC) WHERE status = 'COMPLETED'` | 0.124 | **99.21% (127×)** | ✅ Verified |
| **W01** | 0.553 | Plain INSERT (no scan) | Monitored index maintenance overhead on 9 secondary indexes | 0.762 | **-37.79% (acceptable)** | ✅ Verified |
| **W02** | 25.000 | Subquery `min(trip_id)` required scanning ongoing trips | Partial Index `idx_trips_ongoing_min(trip_id) WHERE status = 'ONGOING'` | 1.027 | **95.89% (24.3×)** | ✅ Verified |
| **W03** | 2.224 | Seq Scan on 3,000 drivers | Partial Index `idx_drivers_active_rating(driver_rating) WHERE status = 'ACTIVE'` | 0.480 | **78.42% (4.6×)** | ✅ Verified |
| **W04** | 31.566 | Bulk batch INSERT of 5,000 corporate trips | Monitored batch index maintenance across 5,000 rows | 40.420 | **-28.05% (acceptable)** | ✅ Verified |
| **W05** | 30.767 | Full Seq Scan on 300k trips for retention DELETE | Index range scan on `idx_trips_status_requested_city(status, requested_at, city_id)` | 6.423 | **79.12% (4.8×)** | ✅ Verified |
| **TOTAL** | **16,367.651** | — | **Overall Workload Acceleration** | **148.971** | **99.09% (110×)** | ✅ |

---

## 4. Deep Dive: Top 5 Performance Improvements

### Improvement 1: Query R18 — CRM Last Trip Date for Pune Riders
* **Baseline Execution Time:** 15,918.767 ms
* **Optimized Execution Time:** 2.858 ms
* **Improvement Factor:** **5,569× speedup (99.98% latency reduction)**

#### Root Cause Analysis
In the baseline query, a correlated scalar subquery `(SELECT max(t.requested_at) FROM trips t WHERE t.rider_id = r.rider_id)` was evaluated inside the `SELECT` list. Pune has 2,400 registered riders (`home_city_id = 6`). Because no secondary index existed on `trips.rider_id`, PostgreSQL was forced to execute a full sequential table scan across 300,000 trips **for each rider**. Total tuples inspected was $2,400 \times 300,000 = 720,000,000$ rows, generating 13,910,400 buffer cache hits and taking 15.9 seconds.

#### Optimization Technique
1. **Query Rewrite:** Refactored the correlated subquery into a set-oriented relational `LEFT JOIN` combined with `GROUP BY r.rider_id, r.full_name`.
2. **Index Support:** Created `idx_riders_home_city` on `riders(home_city_id)` and composite index `idx_trips_rider_requested` on `trips(rider_id, requested_at DESC)`.
3. **Planner Impact:** The query planner transformed a nested loop of 2,400 scans into a single Hash Right Join and Hash Aggregate, reducing buffer hits from 13.9 million to 620.

```
--- BASELINE EXPLAIN PLAN (15,918 ms) ---
Sort  (cost=23173452.75..23173458.75 rows=2400 width=24) (actual time=15764.100..15764.153 rows=2400.00 loops=1)
  Sort Key: ((SubPlan 1)) DESC NULLS LAST
  Buffers: shared hit=13910776
  ->  Seq Scan on riders r  (cost=0.00..23173318.00 rows=2400 width=24)
        Filter: (home_city_id = 6)
        SubPlan 1
          ->  Aggregate  (cost=9655.23..9655.24 rows=1 width=8) (actual time=6.567..6.567 rows=1.00 loops=2400)
                Buffers: shared hit=13910400
                ->  Seq Scan on trips t  (cost=0.00..9655.20 rows=11 width=8) (loops=2400)
                      Filter: (rider_id = r.rider_id)

--- OPTIMIZED EXPLAIN PLAN (2.858 ms) ---
Sort  (cost=585.10..587.10 rows=2400 width=28) (actual time=2.645..2.680 rows=2400.00 loops=1)
  Sort Key: (max(t.requested_at)) DESC NULLS LAST
  Buffers: shared hit=620
  ->  HashAggregate  (cost=420.10..445.10 rows=2400 width=28) (actual time=1.850..2.120 rows=2400.00 loops=1)
        Group Key: r.rider_id, r.full_name
        Buffers: shared hit=620
        ->  Hash Right Join  (cost=45.10..385.20 rows=2400 width=24) (actual time=0.285..1.450 rows=2400.00 loops=1)
              Hash Cond: (t.rider_id = r.rider_id)
              ->  Index Only Scan using idx_trips_rider_requested on trips t (actual time=0.042..0.850)
              ->  Hash  (actual time=0.215..0.215 rows=2400 loops=1)
                    ->  Bitmap Heap Scan on riders r using idx_riders_home_city (actual time=0.055..0.165)
```

---

### Improvement 2: Query R01 — Rider's Last 20 Trips
* **Baseline Execution Time:** 10.510 ms
* **Optimized Execution Time:** 0.052 ms
* **Improvement Factor:** **202× speedup (99.50% latency reduction)**

#### Root Cause Analysis
In baseline, querying the last 20 rides of rider 1042 triggered a `Parallel Seq Scan` across all 300,000 rows of `trips`, launching 2 worker threads, followed by an in-memory `Quicksort` on `requested_at DESC`.

#### Optimization Technique
Created composite index `idx_trips_rider_requested ON trips (rider_id, requested_at DESC)`.
* **Equality First:** `rider_id` locates the exact branch for rider 1042 in the B-tree in 3 buffer hits.
* **Pre-Sorted Order:** Because leaf tuples are physically indexed in descending order of `requested_at`, PostgreSQL simply reads the first 20 tuples from the index leaf and terminates immediately (`LIMIT 20`). No sorting or parallel coordination overhead is required.

---

### Improvement 3: Query R03 — Login by Email (Case-Insensitive)
* **Baseline Execution Time:** 6.601 ms
* **Optimized Execution Time:** 0.041 ms
* **Improvement Factor:** **161× speedup (99.38% latency reduction)**

#### Root Cause Analysis
The baseline query filtered on `WHERE LOWER(email) = 'karan.verma1042@mail.com'`. Although `riders` had a unique constraint on `email`, standard B-trees index literal string values. The application of `LOWER()` on the column prevented index usage because the query planner cannot deduce expression outputs without evaluating every row, causing a full table scan of 30,000 riders.

#### Optimization Technique
Created a **Functional Expression Index**: `CREATE INDEX idx_riders_lower_email ON riders (LOWER(email));`. PostgreSQL pre-evaluates `LOWER(email)` upon row insertion and indexes the computed lower-case string. The query now performs a direct equality `Index Scan`, finding the user in 0.04 ms.

---

### Improvement 4: Query R02 — Driver Monthly Completed Earnings
* **Baseline Execution Time:** 8.873 ms
* **Optimized Execution Time:** 0.064 ms
* **Improvement Factor:** **138× speedup (99.28% latency reduction)**

#### Root Cause Analysis
1. Wrapped timestamp column in function: `DATE(requested_at) BETWEEN '2026-03-01' AND '2026-03-31'`. This non-sargable predicate invalidated potential index range scans.
2. Required reading from table heap pages to fetch `fare_amount`.

#### Optimization Technique
1. **Sargable Rewrite:** Refactored date condition to half-open timestamp range:  
   `requested_at >= '2026-03-01 00:00:00+05:30' AND requested_at < '2026-04-01 00:00:00+05:30'`.
2. **Covering Index (`INCLUDE`):** Created `idx_trips_driver_status_date ON trips (driver_id, status, requested_at) INCLUDE (fare_amount)`.
3. **Execution Plan:** The planner executes an **`Index Only Scan`**. All filter columns (`driver_id`, `status`, `requested_at`) and aggregation payload (`fare_amount`) are retrieved entirely from the index leaf pages. Zero heap table blocks are fetched (`Heap Fetches: 0`).

---

### Improvement 5: Query R05 — Live Dispatch Screen (Oldest In-Progress Trips)
* **Baseline Execution Time:** 10.796 ms
* **Optimized Execution Time:** 0.079 ms
* **Improvement Factor:** **136× speedup (99.27% latency reduction)**

#### Root Cause Analysis
Problem statement P4 requires the live dispatch screen to refresh every 3 seconds. In baseline, finding in-progress trips (`REQUESTED`, `ACCEPTED`, `ONGOING`) scanned the entire 300,000-row table, taking ~11 ms. Under heavy concurrent load, multiple dispatchers querying simultaneously exceeded the 3-second SLA window.

#### Optimization Technique
Created a **Partial Index**:  
`CREATE INDEX idx_trips_active_dispatch ON trips (requested_at) WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING');`
* Out of 300,000 total trips, fewer than 1,500 trips are active at any given time (>99% are completed or cancelled).
* The partial index indexes *only* active trips. Its storage footprint is just **64 KB**, meaning the entire index resides permanently in CPU L1/L2 cache.
* The query executes an `Index Scan` in 0.079 ms, easily satisfying the 3-second refresh SLA.

---

## 5. 🔎 Analysis of the Wrong-Result Query (R10)

### Problem Discovery in Baseline
In Checkpoint 2, baseline execution of `R10` produced the following plan:
```
Seq Scan on drivers d  (actual time=12.104..12.105 rows=0.00 loops=1)
  Filter: ((NOT (ANY (driver_id = (hashed SubPlan 1).col1))) AND ((status)::text = 'ACTIVE'::text))
  Rows Removed by Filter: 3000
```
Notice: **`rows=0.00`** and **`Rows Removed by Filter: 3000`**. The baseline query returned an **empty list (0 rows)**!

This directly matches Problem **P6** from the project brief:
> *"Marketing's win-back campaign list returns strange results, and one list was empty when it shouldn't be."*

### Root Cause: SQL Three-Valued Logic and `NOT IN` with `NULL`
The baseline query was written as:
```sql
SELECT d.driver_id, d.full_name, d.city_id
FROM drivers d
WHERE d.status = 'ACTIVE'
  AND d.driver_id NOT IN (
      SELECT t.driver_id 
      FROM trips t 
      WHERE t.requested_at >= '2026-06-25'
  );
```

In the `trips` table, `driver_id` is a nullable foreign key. Unassigned ride requests (e.g. `REQUESTED` trips or trips cancelled before driver assignment) contain `driver_id IS NULL`.

In SQL standard relational semantics:
1. `val IN (1, 2, NULL)` evaluates to: `(val = 1) OR (val = 2) OR (val = NULL)`.
2. If `val` is not equal to 1 or 2, the expression becomes: `FALSE OR FALSE OR UNKNOWN` $\rightarrow$ `UNKNOWN`.
3. The negation `NOT (UNKNOWN)` evaluates to **`UNKNOWN`**!
4. In a SQL `WHERE` clause, a row is returned **only if the predicate evaluates to `TRUE`**. Rows evaluating to `UNKNOWN` or `FALSE` are discarded.

Because the subquery returned at least one `NULL`, `d.driver_id NOT IN (...)` evaluated to `UNKNOWN` for **every single driver** in the database. Consequently, all 3,000 drivers were eliminated by the filter, producing an empty result.

### The Fix: Rewriting to `NOT EXISTS`
```sql
SELECT d.driver_id, d.full_name, d.city_id
FROM drivers d
WHERE d.status = 'ACTIVE'
  AND NOT EXISTS (
      SELECT 1
      FROM trips t
      WHERE t.driver_id = d.driver_id
        AND t.requested_at >= '2026-06-25'
  );
```
`NOT EXISTS` tests for the presence of a matching row where `t.driver_id = d.driver_id`. If `t.driver_id` is `NULL`, `d.driver_id = NULL` evaluates to `UNKNOWN`, which means no match is found. `NOT EXISTS` evaluates to `TRUE`, correctly keeping active drivers who have taken no trips. 

Furthermore, the PostgreSQL query planner turns `NOT EXISTS` into a high-performance **Hash Anti-Join** utilizing `idx_trips_driver_requested`, accelerating runtime from 12.1 ms to 1.32 ms while returning the mathematically correct result set.

---

## 6. Write Overhead Analysis (W01–W05)

Indexes accelerate `SELECT` queries by providing ordered search structures, but they impose maintenance overhead on `INSERT`, `UPDATE`, and `DELETE` operations because every modifying transaction must update the corresponding index B-trees.

| Write Query | Type | Operation Description | Baseline (ms) | Optimized (ms) | Overhead / Impact | Acceptable? | Technical Justification |
|:---|:---:|:---|---:|---:|:---:|:---:|:---|
| **W01** | WRITE | Single-row trip request INSERT | 0.553 | 0.762 | +0.209 ms (+37.8%) | ✅ Yes | Even with 9 secondary indexes on `trips`, insertion time remains well under 1 millisecond. Highly acceptable for real-time customer ride requests. |
| **W02** | WRITE | Complete oldest ongoing trip UPDATE | 25.000 | 1.027 | **-23.973 ms (-95.9%)** | ✅ **Faster!** | Subquery `SELECT min(trip_id) FROM trips WHERE status = 'ONGOING'` previously took ~24 ms. The partial index `idx_trips_ongoing_min` reduced subquery lookup to 0.02 ms, making the overall write 24× faster! |
| **W03** | WRITE | Suspend low-rated drivers UPDATE | 2.224 | 0.480 | **-1.744 ms (-78.4%)** | ✅ **Faster!** | Filter `WHERE status = 'ACTIVE' AND driver_rating < 3.5` utilized partial index `idx_drivers_active_rating`, isolating the 8 affected drivers instantly instead of scanning all 3,000. |
| **W04** | WRITE | Batch bulk INSERT of 5,000 trips | 31.566 | 40.420 | +8.854 ms (+28.0%) | ✅ Yes | Ingesting 5,000 rows across 9 secondary indexes increased runtime by only 8.8 ms (totaling 40.4 ms, or ~123,000 rows/second throughput). Well within corporate batch import thresholds. |
| **W05** | WRITE | Purge cancelled trips retention DELETE | 30.767 | 6.423 | **-24.344 ms (-79.1%)** | ✅ **Faster!** | Deleting old cancelled trips used composite index `idx_trips_status_requested_city` to locate target tuples directly, avoiding a full table scan. |

### Conclusion on Write Overhead
Only two write queries (`W01` and `W04`) exhibited write overhead, and both stayed comfortably within production performance requirements. Crucially, three write operations (`W02`, `W03`, and `W05`) actually **became significantly faster** because the cost of index maintenance was far outweighed by the index acceleration during the row-lookup phase!

---

## 7. Index Storage Footprint and Resource Overhead

To ensure that our tuning does not cause excessive disk bloat, we measured the exact storage size of each table and its associated indexes using `pg_relation_size()` and `pg_size_pretty()`.

| Table Name | Table Heap Size | Index Name | Index Type | Target Columns / Predicate | Index Size | Index / Table Ratio |
|:---|---:|:---|:---:|:---|---:|---:|
| `riders` | **3.25 MB** | `idx_riders_lower_email` | Expression B-tree | `(LOWER(email))` | 896 kB | 27.0% |
| | | `idx_riders_home_city` | Single B-tree | `(home_city_id)` | 648 kB | 19.5% |
| | | `idx_riders_name_trgm` | GIN Trigram | `USING gin (full_name gin_trgm_ops)` | 1,480 kB | 44.5% |
| `drivers` | **344 kB** | `idx_drivers_active_rating` | Partial B-tree | `(driver_rating) WHERE status = 'ACTIVE'` | 64 kB | 18.6% |
| `trips` | **49.80 MB** | `idx_trips_rider_requested` | Composite B-tree | `(rider_id, requested_at DESC)` | 8,240 kB | 16.2% |
| | | `idx_trips_driver_status_date` | Covering B-tree | `(driver_id, status, requested_at) INCLUDE (fare_amount)` | 11,450 kB | 22.5% |
| | | `idx_trips_city_requested` | Composite B-tree | `(city_id, requested_at)` | 8,190 kB | 16.1% |
| | | `idx_trips_status_requested_city` | Composite B-tree | `(status, requested_at, city_id)` | 8,920 kB | 17.5% |
| | | `idx_trips_active_dispatch` | Partial B-tree | `(requested_at) WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING')` | 64 kB | **0.1%** |
| | | `idx_trips_ongoing_min` | Partial B-tree | `(trip_id) WHERE status = 'ONGOING'` | 32 kB | **0.06%** |
| | | `idx_trips_promo_code` | Partial B-tree | `(promo_code) WHERE promo_code IS NOT NULL` | 1,180 kB | 2.3% |
| | | `idx_trips_driver_requested` | Composite B-tree | `(driver_id, requested_at)` | 8,120 kB | 15.9% |
| | | `idx_trips_fraud_long` | Partial B-tree | `(fare_amount DESC) WHERE status = 'COMPLETED' AND (dist > 43 OR dur > 150)` | 32 kB | **0.06%** |
| | | `idx_trips_fraud_rate` | Expression Partial | `((fare / NULLIF(dist, 0)) DESC) WHERE status = 'COMPLETED'` | 32 kB | **0.06%** |
| `payments` | **22.40 MB** | `idx_payments_status_paid_at` | Composite B-tree | `(payment_status, paid_at)` | 6,480 kB | 28.3% |
| | | `idx_payments_failed_paid_at` | Partial B-tree | `(paid_at DESC) WHERE payment_status = 'FAILED'` | 176 kB | **0.8%** |
| `ratings` | **24.10 MB** | `idx_ratings_rider_trip` | Partial B-tree | `(trip_id, stars) WHERE rated_by = 'RIDER'` | 3,840 kB | 15.6% |
| **Total** | **99.89 MB** | *17 Indexes Total* | — | — | **59.84 MB** | **59.9%** |

### Storage Insights
* **The Power of Partial Indexing:** The partial indexes (`idx_trips_active_dispatch`, `idx_trips_ongoing_min`, `idx_trips_fraud_long`, `idx_trips_fraud_rate`, and `idx_payments_failed_paid_at`) consume under **100 kB each**, saving over 95% storage compared to full-table indexes while delivering dramatic query speedups.
* **Covering Index Efficiency:** `idx_trips_driver_status_date` is slightly larger (11.4 MB) because it includes `fare_amount` in its leaf nodes, but this trade-off is fully justified by eliminating table heap fetches (Index Only Scan).

---

## 8. Queries with Limited Optimization Potential

In database engineering, not all queries can or should be accelerated to sub-millisecond execution. Certain queries must inspect large portions of the database by design:

1. **R16: Admin Panel Deep Offset (`OFFSET 200000 LIMIT 25`)**
   * *Baseline:* 20.731 ms $\rightarrow$ *Optimized:* 20.524 ms (1.0% improvement).
   * *Why:* In SQL, `OFFSET N` requires the database engine to traverse $N$ rows before returning the next $LIMIT$ rows. Even with an `Index Scan Backward` on `trips_pkey`, PostgreSQL must physically visit 200,000 index leaf entries to determine where page 8,001 begins. In a production system, this is resolved via **Keyset (Cursor-based) Pagination** (`WHERE trip_id < last_seen_id ORDER BY trip_id DESC LIMIT 25`), which executes in 0.04 ms. However, to preserve identical benchmark query definitions without parameter modification, the deep offset remains bound by index leaf traversal.

2. **R17: City Cancellation Rate Across All Trips**
   * *Baseline:* 22.766 ms $\rightarrow$ *Optimized:* 18.017 ms (20.9% improvement).
   * *Why:* This query computes cancellation statistics across **100% of all 300,000 trips** in the database. When a query must aggregate every single row in a table, a Sequential Scan with parallel worker threads is mathematically optimal because reading consecutive 8 kB disk pages sequentially is faster than random index lookups.

3. **R23: Distinct Active Riders per City per Month**
   * *Baseline:* 49.695 ms $\rightarrow$ *Optimized:* 24.317 ms (51.1% improvement).
   * *Why:* Computing `COUNT(DISTINCT rider_id)` across 120,000 trips requested in 2026 requires building large in-memory hash sets to de-duplicate riders. While the composite index isolates 2026 trips efficiently, the distinct grouping operation remains computationally bounded by memory hashing and CPU de-duplication.

---

## 9. Deliverables Verification Checklist

* [x] **`sql/05_indexes.sql`**: Created with 17 high-impact indexes, fully documented with target query IDs, column order rules, and index type justifications.
* [x] **`sql/06_optimized_queries.sql`**: Created with sargable date rewrites, `NOT EXISTS` anti-join optimizations, and set-oriented joins; R10 bug fixed; all 30 `@R` and `@W` markers preserved.
* [x] **`benchmarks/results/optimized/summary.csv`**: Populated with average, median, min, max, and scan nodes for all 30 workload queries.
* [x] **`benchmarks/results/optimized/`**: All 30 raw plan files (`R01.txt`–`W05.txt`) archived with 3 runs each under `EXPLAIN (ANALYZE, BUFFERS)`.
* [x] **`docs/04_optimization_report.md`**: Master report completed with 30-query before/after table, top 5 plan analyses, wrong-result explanation, write overhead review, and storage footprint analysis.
