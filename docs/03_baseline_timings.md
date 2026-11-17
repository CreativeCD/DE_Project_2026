# CP2 Baseline Timings Report: Uber Ride-Hailing Database

**Project:** PalmPay / Uber Ride-Hailing DBMS  
**Team Number:** T0061  
**Checkpoint:** CP2 – Baseline Timings (Phase 3)  
**Date of Execution:** 17 November 2026  
**Repository:** `CreativeCD/DE_Project_2026`  

---

## 1. Executive Summary

This report documents the official **Checkpoint 2 (CP2) Baseline Benchmark** results for the Uber Ride-Hailing database workload. 

In this phase, all **30 standard workload queries** (25 read queries `R01`–`R25` and 5 write queries `W01`–`W05`) were executed against the PostgreSQL database in its pure, unoptimized baseline state. No performance-tuning indexes or query rewrites were applied. Only the schema constraints established in Checkpoint 1 (Primary Keys and Unique constraints) are active.

Each query was executed **three times** consecutively using `EXPLAIN (ANALYZE, BUFFERS)` via the project benchmark script `benchmarks/run_benchmark.sh`. All write queries (`W01`–`W05`) were executed within isolated transactions (`BEGIN ... ROLLBACK`) to ensure data integrity and guarantee that identical database states were maintained across all runs.

### Key Headline Metrics
* **Total Workload Queries:** 30 (25 Read, 5 Write)
* **Total Benchmark Executions:** 90 runs (3 runs per query)
* **Total Workload Execution Time (Sum of Averages):** **16,367.651 ms** (~16.37 seconds)
* **Fastest Query:** `R14` (0.032 ms avg, exact Unique Index Scan on vehicle registration)
* **Slowest Query:** `R18` (15,918.767 ms avg, correlated subquery causing sequential table scans across ~900M candidate comparisons)
* **Bottleneck Concentration:** Query `R18` alone accounts for **97.26%** of the entire workload execution time.

---

## 2. Benchmark Environment & System Specifications

To ensure scientific repeatability and reproducibility, all benchmarks were conducted under controlled system conditions.

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
| **Optimization State** | Pure Baseline (Zero secondary indexes, default planner parameters) |

### Database Size & Dataset Inventory
The dataset reflects the production export of 300,000 trips across 10 Indian metropolitan cities (1 Jan 2025 to 30 Jun 2026):

| Table Name | Row Count | Primary Key | Foreign Key Dependencies | Existing Baseline Indexes |
|:---|---:|:---|:---|:---|
| `cities` | 10 | `city_id` | None | `cities_pkey`, `cities_city_name_key` |
| `riders` | 30,000 | `rider_id` | `cities` | `riders_pkey`, `riders_email_key`, `riders_phone_key` |
| `drivers` | 3,000 | `driver_id` | `cities` | `drivers_pkey`, `drivers_license_no_key`, `drivers_phone_key` |
| `vehicles` | 3,300 | `vehicle_id` | `drivers` | `vehicles_pkey`, `vehicles_registration_no_key` |
| `promo_codes` | 40 | `promo_code` | None | `promo_codes_pkey` |
| `trips` | 300,000 | `trip_id` | `riders`, `drivers`, `vehicles`, `cities`, `promo_codes` | `trips_pkey` |
| `payments` | 245,839 | `payment_id` | `trips` | `payments_pkey`, `payments_trip_id_key` |
| `ratings` | 307,214 | `(trip_id, rated_by)` | `trips` | `ratings_pkey` |
| **Total** | **889,403** | — | — | **15 Indexes (PK & UNIQUE only)** |

---

## 3. Benchmark Methodology

The benchmarking procedure strictly adhered to the Phase 3 specification in `README.md` and `CHECKPOINTS.md`:

1. **Isolation & Buffer Cache Warm-Up:**
   * Prior to recording, the database was verified using `ANALYZE` to guarantee updated catalog statistics for the PostgreSQL query planner.
   * Background desktop applications were closed to avoid CPU scheduling contention.
2. **Execution Protocol:**
   * The automated script [benchmarks/run_benchmark.sh](file:///Users/srisaidheekshith/de%20project/DE_Project_2026/benchmarks/run_benchmark.sh) was invoked with parameters `uber baseline`.
   * For each query, `EXPLAIN (ANALYZE, BUFFERS)` was executed across 3 iterations.
   * PostgreSQL's actual planner output was parsed for `Execution Time` (excluding client network latency and format rendering overhead).
3. **Read vs. Write Handling:**
   * **Read Queries (`R01`–`R25`):** Executed directly against the `uber` schema.
   * **Write Queries (`W01`–`W05`):** Wrapped in `BEGIN ... ROLLBACK` blocks. This ensures write costs (tuple insertion, constraint evaluation, rollback processing) are accurately measured without modifying or bloating the underlying tables.
4. **Data Persistence:**
   * Full execution plans with buffer hit/read statistics for all 90 runs are permanently archived in [benchmarks/results/baseline/](file:///Users/srisaidheekshith/de%20project/DE_Project_2026/benchmarks/results/baseline).
   * Aggregated metrics are recorded in [benchmarks/results/baseline/summary.csv](file:///Users/srisaidheekshith/de%20project/DE_Project_2026/benchmarks/results/baseline/summary.csv).

---

## 4. Complete Baseline Timing Table (30 Workload Queries)

Below is the verified timing table containing all 30 queries across their three measured runs and the resulting mathematical average.

| SQL Query | Type | Run 1 (ms) | Run 2 (ms) | Run 3 (ms) | Average (ms) |
|:---|:---:|---:|---:|---:|---:|
| **R01:** Rider's last 20 trips | READ | 16.928 | 7.475 | 7.128 | **10.510** |
| **R02:** Driver's March 2026 earnings | READ | 10.022 | 8.499 | 8.097 | **8.873** |
| **R03:** Login by email (case-insensitive) | READ | 7.580 | 6.201 | 6.021 | **6.601** |
| **R04:** Bengaluru trips on 10 May 2026 | READ | 6.715 | 6.988 | 6.681 | **6.795** |
| **R05:** Oldest in-progress trips (dispatch) | READ | 10.767 | 10.710 | 10.911 | **10.796** |
| **R06:** Completed trips per city, June 2026 | READ | 9.793 | 9.118 | 9.147 | **9.353** |
| **R07:** Top 10 earning drivers in Mumbai, Q1 2026 | READ | 10.204 | 10.966 | 10.225 | **10.465** |
| **R08:** Revenue per payment method per month, 2026 | READ | 27.793 | 26.675 | 26.553 | **27.007** |
| **R09:** Bengaluru riders inactive since April 2026 | READ | 17.093 | 17.504 | 17.629 | **17.409** |
| **R10:** Active drivers with no trip since 25 June 2026 | READ | 12.129 | 12.090 | 12.101 | **12.107** |
| **R11:** 20 lowest-rated drivers | READ | 31.651 | 28.985 | 30.442 | **30.359** |
| **R12:** Average surge by hour in Delhi | READ | 30.389 | 30.577 | 33.766 | **31.577** |
| **R13:** Search riders by surname | READ | 8.886 | 8.776 | 9.025 | **8.896** |
| **R14:** Vehicle + driver by registration number | READ | 0.035 | 0.031 | 0.029 | **0.032** |
| **R15:** Trip receipt | READ | 0.076 | 0.067 | 0.065 | **0.069** |
| **R16:** Admin panel page 8,001 | READ | 21.288 | 20.575 | 20.331 | **20.731** |
| **R17:** Cancellation rate per city | READ | 22.932 | 23.077 | 22.289 | **22.766** |
| **R18:** Last trip date of every Pune rider | READ | 15,764.226 | 15,947.645 | 16,044.430 | **15,918.767** |
| **R19:** Top 3 drivers per city, May 2026 | READ | 10.752 | 10.177 | 10.316 | **10.415** |
| **R20:** Daily revenue + running total, May 2026 | READ | 12.844 | 12.650 | 12.750 | **12.748** |
| **R21:** Promo code usage | READ | 18.982 | 18.811 | 18.981 | **18.925** |
| **R22:** Failed payments, last 7 days | READ | 6.733 | 5.711 | 5.681 | **6.042** |
| **R23:** Distinct active riders per city per month | READ | 50.291 | 49.261 | 49.532 | **49.695** |
| **R24:** Unusually long trips | READ | 10.803 | 11.132 | 10.689 | **10.875** |
| **R25:** Trips charging more than ₹100/km | READ | 15.695 | 15.481 | 16.016 | **15.731** |
| **W01:** Request a new trip | WRITE | 0.625 | 0.509 | 0.525 | **0.553** |
| **W02:** Complete the oldest ongoing trip | WRITE | 25.400 | 24.444 | 25.155 | **25.000** |
| **W03:** Suspend low-rated drivers | WRITE | 2.351 | 2.144 | 2.178 | **2.224** |
| **W04:** Bulk import of 5,000 trips | WRITE | 36.659 | 29.050 | 28.990 | **31.566** |
| **W05:** Purge cancelled trips from Jan 2025 | WRITE | 31.301 | 30.277 | 30.722 | **30.767** |
| **Total (sum of all 30 queries)** | — | **16,230.943** | **16,385.606** | **16,486.405** | **16,367.651** |

---

## 5. Query Execution Plans, Scan Types & Performance Analysis

This section analyzes the execution plan node types identified in the raw plan files and provides the architectural reason for the observed speed of each query.

### Summary Scan Distribution
* **Sequential Scans (`Seq Scan` / `Parallel Seq Scan`):** 24 queries
* **Index Scans (`Index Scan` on PK/Unique):** 4 queries (`R14`, `R15`, `R16`, `W02`)
* **Pure In-Memory / Result / Triggers (`no scan`):** 2 queries (`W01`, `W04`)

---

### Detailed Query Breakdown

#### `R01`: Rider's Last 20 Trips
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 10.510 ms
* **Why it is slow:** Filter `WHERE rider_id = 1042` has no index on `trips(rider_id)`. The planner launches 2 parallel worker processes to scan all 300,000 rows in `trips`, discards 299,993 non-matching rows, and sorts the remaining 7 rows in memory.

#### `R02`: Driver's March 2026 Earnings
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 8.873 ms
* **Why it is slow:** Scans all 300,000 trip rows because no composite index exists on `(driver_id, status, requested_at)`. Furthermore, the filter wraps `requested_at` in the `DATE()` function, preventing direct range index lookups.

#### `R03`: Login by Email (Case-Insensitive)
* **Plan Scan Nodes:** `Parallel Seq Scan on riders`
* **Average Time:** 6.601 ms
* **Why it is slow:** Although a unique index exists on `riders(email)`, the query searches using `LOWER(email) = '...'`. Standard B-tree indexes cannot be used for transformed expressions without an expression index. All 30,000 riders are scanned sequentially.

#### `R04`: Bengaluru Trips on 10 May 2026
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on cities`
* **Average Time:** 6.795 ms
* **Why it is slow:** Scans all 10 cities to find 'Bengaluru' and performs a sequential scan over `trips` to filter by city foreign key and timestamp range without a composite index on `(city_id, requested_at)`.

#### `R05`: Oldest In-Progress Trips (Dispatch)
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 10.796 ms
* **Why it is slow:** Filter `status IN ('REQUESTED', 'ACCEPTED', 'ONGOING')` matches only a tiny percentage of rows, yet all 300,000 rows are scanned and sorted. A partial index on active statuses is missing.

#### `R06`: Completed Trips per City, June 2026
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on cities`
* **Average Time:** 9.353 ms
* **Why it is slow:** Hash Join of sequential scans on `trips` and `cities`. Aggregates 300,000 rows in memory via HashAggregate.

#### `R07`: Top 10 Earning Drivers in Mumbai, Q1 2026
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on drivers | Seq Scan on cities`
* **Average Time:** 10.465 ms
* **Why it is slow:** Three-way table join requiring full sequential scans on `trips`, `drivers`, and `cities`, followed by a Sort node on aggregated earnings.

#### `R08`: Monthly Revenue per Payment Method (2026)
* **Plan Scan Nodes:** `Parallel Seq Scan on payments`
* **Average Time:** 27.007 ms
* **Why it is slow:** Scans all 245,839 payment records and applies date extraction (`EXTRACT(YEAR FROM paid_at) = 2026`) sequentially.

#### `R09`: Bengaluru Riders Inactive Since April 2026
* **Plan Scan Nodes:** `Seq Scan on riders | Seq Scan on trips`
* **Average Time:** 17.409 ms
* **Why it is slow:** Employs `NOT IN (SELECT t.rider_id FROM trips ...)`. The subplan builds a hash table of all riders active since April by scanning `trips`, while sequentially filtering `riders`.

#### `R10`: Active Drivers with No Trips Since 25 June 2026
* **Plan Scan Nodes:** `Seq Scan on drivers | Seq Scan on trips`
* **Average Time:** 12.107 ms
* **Why it is slow:** Similar to R09, builds an in-memory hash set of recent drivers via sequential scan on `trips` and probes against `drivers`.

#### `R11`: 20 Lowest-Rated Drivers
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on ratings`
* **Average Time:** 30.359 ms
* **Why it is slow:** Joins 307,214 ratings against 300,000 trips using Hash Join without foreign key indexes, computing aggregate averages and sorting.

#### `R12`: Average Surge by Hour in Delhi
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on cities`
* **Average Time:** 31.577 ms
* **Why it is slow:** Filters `trips` for Delhi city ID via full table scan, extracts the hour component from timestamps, and performs group aggregation.

#### `R13`: Search Riders by Surname
* **Plan Scan Nodes:** `Parallel Seq Scan on riders`
* **Average Time:** 8.896 ms
* **Why it is slow:** Uses wildcard substring matching (`ILIKE '%sharma%'`). Standard B-trees cannot satisfy leading wildcards, forcing a complete sequential scan of 30,000 rider strings.

#### `R14`: Vehicle + Driver by Registration Number
* **Plan Scan Nodes:** `Index Scan using vehicles_registration_no_key on vehicles | Index Scan using drivers_pkey on drivers`
* **Average Time:** **0.032 ms**
* **Why it is fast:** Leverages the Unique B-tree index on `vehicles(registration_no)` (0 buffer misses) followed by a direct Primary Key Index Scan on `drivers(driver_id)`. Exemplary point-lookup performance.

#### `R15`: Complete Trip Receipt
* **Plan Scan Nodes:** `Index Scan using trips_pkey on trips | Index Scan using riders_pkey on riders | Index Scan using drivers_pkey on drivers | Index Scan using vehicles_pkey on vehicles | Index Scan using payments_trip_id_key on payments`
* **Average Time:** **0.069 ms**
* **Why it is fast:** Highly optimized nested index lookups across 5 tables entirely satisfied via Primary Key and Unique indexes in shared buffer memory.

#### `R16`: Admin Panel Page 8,001 (Offset Pagination)
* **Plan Scan Nodes:** `Index Scan using trips_pkey on trips`
* **Average Time:** 20.731 ms
* **Why it is slow:** Although it utilizes the Primary Key index to traverse in reverse order, `OFFSET 200000 LIMIT 25` forces the database engine to traverse and discard 200,000 index entries and heap tuples before returning 25 rows.

#### `R17`: Cancellation Rate per City
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on cities`
* **Average Time:** 22.766 ms
* **Why it is slow:** Full sequential aggregation over 300,000 trips calculating conditional `FILTER (WHERE t.status LIKE 'CANCELLED%')`.

#### `R18`: Last Trip Date of Every Pune Rider (System Bottleneck)
* **Plan Scan Nodes:** `Seq Scan on riders | Seq Scan on trips`
* **Average Time:** **15,918.767 ms** (~15.92 seconds)
* **Why it is slow:** **Severe architectural bottleneck.** Contains a correlated scalar subquery:  
  `(SELECT max(t.requested_at) FROM trips t WHERE t.rider_id = r.rider_id)`.  
  Because there is no index on `trips(rider_id)`, PostgreSQL executes a full sequential scan of all 300,000 trips for **each** of the ~3,000 Pune riders. This results in nearly **900 million row evaluations** executed in a single query turn!

#### `R19`: Top 3 Drivers per City (May 2026)
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on drivers`
* **Average Time:** 10.415 ms
* **Why it is slow:** Full scan on `trips` to filter May 2026 completed rides, followed by window function ranking (`RANK() OVER (PARTITION BY city_id ...)`).

#### `R20`: Daily Revenue and Running Total (May 2026)
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 12.748 ms
* **Why it is slow:** Evaluates date casts on 300,000 trips sequentially, aggregates daily sums, and applies a cumulative window sum.

#### `R21`: Promo Code Usage
* **Plan Scan Nodes:** `Seq Scan on trips | Seq Scan on promo_codes`
* **Average Time:** 18.925 ms
* **Why it is slow:** Outer join of `promo_codes` with 300,000 trips. Lacks foreign key indexing on `trips(promo_code)`.

#### `R22`: Failed Payments in Last 7 Days
* **Plan Scan Nodes:** `Seq Scan on payments | Index Scan using trips_pkey on trips | Index Scan using riders_pkey on riders`
* **Average Time:** 6.042 ms
* **Why it is slow:** Full scan on `payments` (245,839 rows) to find `payment_status = 'FAILED'`. Once found, joins to `trips` and `riders` use primary keys.

#### `R23`: Distinct Active Riders per City per Month
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 49.695 ms
* **Why it is slow:** Requires heavy multi-column hashing and distinct sorting (`count(DISTINCT rider_id)`) across 300,000 records.

#### `R24`: Fraud Check: Unusually Long Trips
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 10.875 ms
* **Why it is slow:** Sequential scan of all trips evaluating boolean condition `(distance_km > 43 OR duration_min > 150)`.

#### `R25`: Fraud Check: High Fare per Km (> ₹100/km)
* **Plan Scan Nodes:** `Parallel Seq Scan on trips`
* **Average Time:** 15.731 ms
* **Why it is slow:** Sequential scan over all trips computing division `fare_amount / NULLIF(distance_km, 0)` for every completed row.

#### `W01`: Request a New Trip
* **Plan Scan Nodes:** `(no scan)` (Result node + Insert)
* **Average Time:** **0.553 ms**
* **Why it is fast:** Single tuple insertion. Minimal overhead; checks foreign key constraints on rider, driver, vehicle, and city via existing primary key indexes.

#### `W02`: Complete Oldest Ongoing Trip
* **Plan Scan Nodes:** `Index Scan using trips_pkey on trips`
* **Average Time:** 25.000 ms
* **Why it is slow:** The subquery `(SELECT min(trip_id) FROM trips WHERE status = 'ONGOING')` scans the primary key index backwards but must check the heap visibility of every ongoing trip tuple. The update then incurs tuple rewriting and trigger verification.

#### `W03`: Suspend Low-Rated Drivers
* **Plan Scan Nodes:** `Seq Scan on drivers`
* **Average Time:** 2.224 ms
* **Why it is fast:** Table `drivers` is small (3,000 rows). Sequential scan and in-place tuple updates complete rapidly.

#### `W04`: Bulk Import of 5,000 Corporate Trips
* **Plan Scan Nodes:** `(no scan)` (Function Scan on `generate_series` + Batch Insert)
* **Average Time:** 31.566 ms
* **Why it is slow:** Generates 5,000 synthetic rows and evaluates 5 foreign key constraints for every row (25,000 foreign key lookups total) inside a single transaction.

#### `W05`: Purge Cancelled Trips from January 2025
* **Plan Scan Nodes:** `Seq Scan on trips`
* **Average Time:** 30.767 ms
* **Why it is slow:** Scans all 300,000 rows in `trips` to find cancelled records from January 2025, marks dead tuples, and verifies cascade constraints.

---

## 6. Synthesis of Baseline Observations for CP3

The baseline measurements provide concrete empirical evidence regarding where the database engine spends its execution time:

1. **Foreign Key Index Deficiency:**
   PostgreSQL automatically indexes Primary Keys, but **does not automatically index Foreign Keys**. Columns such as `trips.rider_id`, `trips.driver_id`, and `trips.city_id` lack indexes, causing multi-table joins to fall back on expensive sequential scans.
2. **Correlated Subquery Amplification (The R18 Catastrophe):**
   Query `R18` illustrates the danger of correlated subqueries without index support. Adding an index on `trips(rider_id, requested_at DESC)` or rewriting the query into a joined aggregation in CP3 will provide immense performance gains.
3. **Expression Index Opportunities:**
   Queries `R02`, `R03`, and `R20` filter by transformed values (e.g. `LOWER(email)` or `DATE(requested_at)`). Baseline B-trees are bypassed because the functions mask column values.
4. **Pagination Inefficiencies:**
   Query `R16` demonstrates that high-offset pagination (`OFFSET 200000`) degrades linearly as offsets grow. Keyset pagination (cursor-based pagination) will be evaluated in Phase 4.

---

## 7. Deliverables Checklist & Integrity Statement

* [x] All 30 workload queries executed against PostgreSQL 18.6
* [x] Each query executed exactly 3 times consecutively
* [x] Raw query plans with execution times stored in `benchmarks/results/baseline/*.txt`
* [x] Summary CSV generated at `benchmarks/results/baseline/summary.csv`
* [x] Baseline Markdown report created at `docs/03_baseline_timings.md`
* [x] No fake, fabricated, or simulated timings used; all values taken from live PostgreSQL planner output
* [x] Database state preserved (all write queries rolled back; trips table count verified at 300,000)

**Certified by Team T0061 (PalmPay DE Team)**  
*Member 2: Sri Sai Deekshit Thitla (`Srisaiw`)*
