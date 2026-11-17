# PalmPay / Uber DBMS Project: CP2 Viva Preparation Guide

**Author / Student:** Sri Sai Deekshit Thitla (Member 2)  
**Team Number:** T0061  
**Project:** PalmPay / Uber Ride-Hailing Database Management System  
**Course:** Database Management Systems (DBMS)  
**Target Checkpoint:** CP2 – Baseline Timings  
**Target Repository:** `CreativeCD/DE_Project_2026`  

---

## Welcome and How to Use This Guide

This guide is written specifically for you as a beginner preparing for your DBMS oral examination (Viva). Every technical concept is explained in simple, everyday language using real examples from our project files.

When your examiner asks a question:
1. Speak clearly and confidently.
2. Give a direct 1–2 sentence definition.
3. Anchor your answer with a concrete example from our PalmPay project (e.g. "In our `trips` table with 300,000 rows...").

---

# Section A: DBMS Fundamentals

### 1. What is a DBMS?
* **Simple Definition:** A Database Management System (DBMS) is computer software designed to store, organize, retrieve, and manage large amounts of data securely and reliably.
* **Analogy:** Think of an operating system for your data. Instead of saving raw text files in scattered folders where anyone could corrupt them, a DBMS acts as an intelligent librarian who knows exactly where every record lives and who has permission to view or edit it.

### 2. What is an RDBMS?
* **Simple Definition:** A **Relational** Database Management System is a type of DBMS that organizes data into two-dimensional tables (relations) made of rows and columns, where tables can be linked ("related") to each other using shared keys.
* **In Our Project:** Our `riders` table is related to our `trips` table because every trip contains a `rider_id` linking back to the rider who requested the ride.

### 3. What is PostgreSQL?
* **Simple Definition:** PostgreSQL (often called "Postgres") is a powerful, open-source object-relational database management system known for reliability, standards compliance, and performance.
* **In Our Project:** We are running **PostgreSQL 18.6** on an Apple M4 Mac. We store all our project tables inside a dedicated schema called `uber`.

### 4. What is SQL?
* **Simple Definition:** SQL stands for **Structured Query Language**. It is the standard programming language used by humans and software applications to communicate with relational databases to read, insert, update, and delete data.

### 5. What is a Table?
* **Simple Definition:** A table is a structured collection of related data organized in rows and columns, similar to a spreadsheet sheet.
* **In Our Project:** We have 8 tables: `cities`, `riders`, `drivers`, `vehicles`, `promo_codes`, `trips`, `payments`, and `ratings`.

### 6. What are Rows and Columns?
* **Row (Tuple / Record):** A single horizontal entry representing one individual item or event. In `trips`, one row represents one single ride taken by a passenger.
* **Column (Attribute / Field):** A vertical category that holds a specific piece of information for every row. In `trips`, columns include `trip_id`, `fare_amount`, `requested_at`, and `status`.

### 7. What is a Primary Key (PK)?
* **Simple Definition:** A column (or set of columns) that uniquely identifies each individual row in a table. It cannot be NULL, and no two rows can have the same value.
* **In Our Project:**
  * In `riders`, `rider_id` is the Primary Key.
  * In `ratings`, `(trip_id, rated_by)` is a composite Primary Key because each trip can only have one rating from the rider and one from the driver.

### 8. What is a Foreign Key (FK)?
* **Simple Definition:** A column in one table that points to the Primary Key of another table. It enforces "referential integrity" — you cannot book a ride for a rider who does not exist.
* **In Our Project:** In the `trips` table, `rider_id` is a Foreign Key pointing to `riders(rider_id)`. If someone tries to insert a trip with `rider_id = 999999` and that rider does not exist in `riders`, PostgreSQL immediately rejects the insert with an error.

---

# Section B: SQL Concepts Used in Our Workload

### 1. `SELECT` and `FROM`
* **Purpose:** Retrieves data from one or more tables.
* **Example:** `SELECT trip_id, fare_amount FROM trips;`

### 2. `WHERE` Clause
* **Purpose:** Filters rows so only those meeting a specific condition are returned.
* **Example in R01:** `WHERE rider_id = 1042` only looks at trips taken by user 1042.

### 3. `ORDER BY` and `LIMIT`
* **Purpose:** `ORDER BY` sorts the results in ascending (`ASC`) or descending (`DESC`) order. `LIMIT` restricts the number of rows returned to the client.
* **Example in R01:** `ORDER BY requested_at DESC LIMIT 20;` sorts trips from newest to oldest and only returns the top 20.

### 4. `GROUP BY` and `HAVING`
* **Purpose:** `GROUP BY` bundles rows with identical values together so aggregate functions can summarize them. `HAVING` filters the groups *after* aggregation (unlike `WHERE`, which filters rows *before* aggregation).
* **Example in R11:** 
  ```sql
  GROUP BY t.driver_id
  HAVING count(*) >= 20
  ```
  Groups all ratings by driver, but only keeps drivers who have received at least 20 ratings.

### 5. `JOIN` (Inner Join vs Left Join)
* **Inner JOIN (`JOIN`):** Combines rows from two tables only when there is a match in both.
  * *Example in R04:* `FROM trips t JOIN cities c ON c.city_id = t.city_id` keeps only trips that match a valid city.
* **Left Outer JOIN (`LEFT JOIN`):** Returns all rows from the left table, even if there is no matching row in the right table (filling empty fields with `NULL`).
  * *Example in R21:* `FROM promo_codes p LEFT JOIN trips t ON t.promo_code = p.promo_code` lists every promo code even if it was never used in any trip.

### 6. Aggregate Functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`)
* Mathematical calculations across multiple rows:
  * `count(*)`: counts the number of matching records.
  * `sum(fare_amount)`: adds up total money earned.
  * `avg(r.stars)`: calculates average rating score.
  * `min(trip_id)`: finds the lowest ID number.

### 7. Window Functions (`RANK()` and `SUM() OVER`)
* **Purpose:** Calculates values across a set of rows related to the current row without collapsing the rows into a single summary like `GROUP BY` does.
* **Example in R19:** `RANK() OVER (PARTITION BY d.city_id ORDER BY count(*) DESC)` ranks drivers inside their own city based on trip counts.
* **Example in R20:** `sum(revenue) OVER (ORDER BY day)` computes a running cumulative revenue total day by day.

### 8. Subqueries and Correlated Subqueries
* **Subquery:** A query nested inside another query.
* **Correlated Subquery:** An inner query that depends on values from the outer query for each row processed.
* **Crucial Example in R18:**
  ```sql
  SELECT r.rider_id, (SELECT max(t.requested_at) FROM trips t WHERE t.rider_id = r.rider_id)
  FROM riders r WHERE r.home_city_id = 6;
  ```
  The inner query runs for *every single rider in Pune*. Because `trips` has no index on `rider_id`, the database does 300,000 comparisons for each of the ~3,000 riders, taking ~16 seconds!

---

# Section C: Database Benchmarking & Performance

### 1. What is Database Benchmarking?
Benchmarking is executing a controlled, repeatable set of queries against a database to systematically measure its execution speed, resource consumption, and scalability.

### 2. What is Baseline Performance?
The baseline is our initial benchmark measurement taken on an unoptimized system. It establishes the "ground zero" or standard against which all future improvements (such as adding indexes or rewriting queries in CP3) are measured.

### 3. What is Query Execution Time?
The actual duration (in milliseconds, `ms`) taken by the database engine's executor to process the query plan and return the tuples. It excludes network transmission time to the client.

### 4. Why Run Each Query Three Times?
1. **Cold Cache vs. Warm Cache:** The first run may require reading pages from disk (cold cache). Subsequent runs find pages already loaded into PostgreSQL's shared buffer pool in RAM (warm cache).
2. **Smoothing Fluctuations:** Operating systems have background tasks and CPU scheduling variations. Running three times eliminates single-run flukes.
3. **Statistical Validity:** Calculating the average of 3 runs provides an honest, stable benchmark metric.

### 5. What is the Difference Between Average, Median, Min, and Max?
* **Average (Mean):** Sum of all runs divided by count. Shows overall expected throughput.
* **Median:** The middle value when sorted. Less sensitive to one sudden outlier spike.
* **Minimum (Min):** The best-case execution time (warmest cache, lowest CPU contention).
* **Maximum (Max):** The worst-case execution time (often the cold run).

### 6. What Factors Affect Execution Time?
* **Presence of Indexes:** Index lookups take `O(log N)` time, while full table scans take `O(N)` time.
* **Memory Buffer Cache:** Accessing RAM is thousands of times faster than reading from SSD storage.
* **Data Volume:** Scanning 300,000 rows takes roughly 10x longer than scanning 30,000 rows.
* **Query Construction:** Nested loops and correlated subqueries multiply execution costs exponentially.

---

# Section D: Technical Implementation & Script Walkthrough

### 1. Line-by-Line Breakdown of `benchmarks/run_benchmark.sh`

Here is how our benchmark script works under the hood:

```bash
# 1. Configuration & Safety
set -euo pipefail  # Exits immediately if any command fails or variable is unset
DB="${1:?database name required}"     # First argument: database name ("uber")
PHASE="${2:?phase required}"          # Second argument: benchmark phase ("baseline")
RUNS="${3:-3}"                        # Third argument: number of runs (defaults to 3)
```

```bash
# 2. Path Setup and CSV Header Creation
OUT="$ROOT/benchmarks/results/$PHASE"
SUMMARY="$OUT/summary.csv"
mkdir -p "$OUT"
echo "query_id,type,avg_ms,median_ms,min_ms,max_ms,scan_nodes" > "$SUMMARY"
```
* Creates directory `benchmarks/results/baseline/`.
* Initializes `summary.csv` with the required column headers.

```bash
# 3. Workload Splitting via AWK
TMP="$(mktemp -d)"
awk -v dir="$TMP" '
  /^-- @/ { id = ""; if ($2 ~ /^@[RW][0-9]+$/) { id = substr($2, 2); file = dir "/" id ".sql"; printf "" > file }; next }
  id != "" && !/^--/ { print >> file }
' "$WORKLOAD"
```
* Reads `queries/workload_30.sql`.
* Detects lines starting with `-- @R01`, `-- @W01`, etc.
* Splits the single large file into 30 small individual `.sql` files inside a temporary folder.

```bash
# 4. Execution Loop
for f in $(ls "$TMP"/*.sql | sort -V); do
  id="$(basename "$f" .sql)"
  type="READ"; [[ "$id" == W* ]] && type="WRITE"
  query="$(cat "$f")"
  
  for ((i = 1; i <= RUNS; i++)); do
    if [[ "$type" == "WRITE" ]]; then
      sql="SET search_path TO uber; BEGIN; EXPLAIN (ANALYZE, BUFFERS) $query ROLLBACK;"
    else
      sql="SET search_path TO uber; EXPLAIN (ANALYZE, BUFFERS) $query"
    fi
    plan="$(printf '%s\n' "$sql" | psql -d "$DB" -X -q -A -t -v ON_ERROR_STOP=1)"
    echo "=== $id run $i ===" >> "$OUT/$id.txt"
    echo "$plan" >> "$OUT/$id.txt"
    t="$(echo "$plan" | grep -oE 'Execution Time: [0-9.]+' | awk '{print $3}')"
    times+=("$t")
  done
```
* **Isolation of Writes:** Notice `BEGIN; ... ROLLBACK;`. Write queries (like adding 5,000 trips in W04) are tested realistically, but then rolled back so the database data never gets dirty!
* **Plan Capture:** The raw query execution plan from PostgreSQL is saved into `benchmarks/results/baseline/R01.txt`.
* **Timing Extraction:** Uses regular expressions to extract `Execution Time: XX.XXX ms`.

```bash
# 5. Averaging & Summary Generation
  avg="$(printf '%s\n' "${times[@]}" | awk '{ s += $1 } END { printf "%.3f", s / NR }')"
  node="$(echo "$plan" | grep -oE '(Parallel )?(Seq Scan|Index Scan|...)' ...)"
  echo "$id,$type,$avg,$median,${sorted[0]},${sorted[$((RUNS - 1))]},$node" >> "$SUMMARY"
```
* Calculates the average time across the 3 runs.
* Identifies whether the database performed a `Seq Scan` (Sequential Scan) or `Index Scan`.
* Appends the final row into `summary.csv`.

---

# Section E: PalmPay Project Findings & Baseline Results

### 1. What Did Our Team Implement for CP2?
* Verified PostgreSQL 18.6 installation and table schemas.
* Confirmed all 8 tables hold 889,403 rows of real seed data.
* Executed the benchmark suite of all 30 queries, 3 times each (90 executions total).
* Recorded raw plans for all queries in `benchmarks/results/baseline/*.txt`.
* Formatted and generated the official `benchmarks/results/baseline/summary.csv`.
* Authored the technical report `docs/03_baseline_timings.md`.

### 2. What Do Our Actual Numbers Reveal?
* **Total Baseline Execution Time:** **16,367.651 ms** (~16.37 seconds).
* **The R18 Catastrophe:** Query `R18` took **15,918.767 ms** (~15.9 seconds). That is **97.26%** of our total workload time!
  * Why? It searches the last trip of every rider in Pune. For each rider, it sequentially scans all 300,000 trips.
* **The High-Speed Queries:**
  * `R14` (0.032 ms) and `R15` (0.069 ms) are lightning-fast because they search on Primary Keys (`trip_id`, `vehicle_id`, `driver_id`) and Unique keys (`registration_no`), where B-tree indexes already exist.
* **The Missing Indexes:**
  * Foreign key columns (`trips.rider_id`, `trips.driver_id`, `trips.city_id`) have NO indexes yet.
  * Queries like `R01` (Rider's last 20 trips) and `R02` (Driver's earnings) must sequentially scan 300,000 rows to find just 10–20 rows.
* **Function Call Pitfalls:**
  * `R03` looks for riders by `LOWER(email)`. Even though `email` has a Unique index, wrapping it in `LOWER()` forces PostgreSQL to ignore the index and scan all 30,000 riders sequentially!

### 3. Difference Between CP2 and CP3
* **CP2 (Baseline):** We measure how the system performs **out of the box** without any special tuning or indexes.
* **CP3 (Optimization):** We will create targeted B-tree indexes, partial indexes, expression indexes, and rewrite problematic SQL queries to drop the execution time from 16 seconds down to less than 100 milliseconds!

---

# Section F: 60 Curated Viva Questions and Answers

## Part 1: 30 Basic Viva Questions (Warm-Up & Core Concepts)

#### Q1: What is a Database?
**Answer:** A database is an organized collection of structured data stored electronically in a computer system so it can be easily accessed, managed, and updated.

#### Q2: What is the difference between a DBMS and an RDBMS?
**Answer:** A DBMS stores data as files or records without strictly enforced tabular relationships. An RDBMS stores data in structured tables related to each other via Primary and Foreign Keys and enforces ACID properties.

#### Q3: What does SQL stand for?
**Answer:** Structured Query Language.

#### Q4: What is a Primary Key?
**Answer:** A column or combination of columns that uniquely identifies every single row in a table. It cannot contain NULL values.

#### Q5: Can a table have multiple Primary Keys?
**Answer:** No. A table can have only one Primary Key. However, that primary key can consist of multiple columns combined (called a composite primary key).

#### Q6: Give an example of a composite Primary Key from our project.
**Answer:** In our `ratings` table, the primary key is `(trip_id, rated_by)`. A trip can have at most one rating from the rider and one from the driver.

#### Q7: What is a Foreign Key?
**Answer:** A column in a table that references the Primary Key of another table, maintaining referential integrity between the two tables.

#### Q8: What happens if you try to delete a City that still has registered Riders?
**Answer:** In our schema, `riders.home_city_id` has `ON DELETE RESTRICT`. PostgreSQL will block the deletion and throw an error to prevent orphan records.

#### Q9: What is the `uber` schema in our database?
**Answer:** A schema is a logical namespace inside a database that groups tables and objects together. We created schema `uber` to keep our project tables separate from system tables.

#### Q10: How many tables exist in our PalmPay database?
**Answer:** 8 tables: `cities`, `riders`, `drivers`, `vehicles`, `promo_codes`, `trips`, `payments`, and `ratings`.

#### Q11: How many trip records exist in our seed data?
**Answer:** Exactly 300,000 trip rows.

#### Q12: What is a `NULL` value in SQL?
**Answer:** `NULL` represents missing, unknown, or inapplicable data. It is not equivalent to zero or an empty string `""`.

#### Q13: What does `NOT NULL` mean?
**Answer:** It is a column constraint ensuring that a column can never store an empty or missing value.

#### Q14: What is a `CHECK` constraint?
**Answer:** A rule that limits the values that can be inserted into a column. For example, in our `cities` table, `CHECK (base_fare >= 0)` guarantees fares cannot be negative.

#### Q15: What is the difference between `CHAR`, `VARCHAR`, and `TEXT`?
**Answer:** `CHAR(n)` is fixed-length (padded with spaces). `VARCHAR(n)` is variable-length up to $n$ characters. `TEXT` holds variable-length text of unlimited length.

#### Q16: What does `SELECT *` do?
**Answer:** It retrieves all columns from the specified table.

#### Q17: Why is `SELECT *` generally discouraged in production applications?
**Answer:** It wastes network bandwidth and memory by transferring columns the application may not need, and it prevents the database from using Index-Only Scans.

#### Q18: What is the function of the `WHERE` clause?
**Answer:** It filters rows based on a specified condition before any groupings or sorting take place.

#### Q19: What is the difference between `ASC` and `DESC` in `ORDER BY`?
**Answer:** `ASC` sorts from smallest to largest (ascending, default), while `DESC` sorts from largest to smallest (descending).

#### Q20: What does the `LIMIT` clause do?
**Answer:** It caps the maximum number of rows returned by the query.

#### Q21: What is the difference between `COUNT(*)` and `COUNT(column)`?
**Answer:** `COUNT(*)` counts all rows including those with NULLs, whereas `COUNT(column)` counts only rows where the specified column is NOT NULL.

#### Q22: What is an Inner Join?
**Answer:** A join that returns only rows where matching values exist in both joined tables.

#### Q23: What is a Left Outer Join?
**Answer:** A join that returns all rows from the left table, matched with corresponding rows from the right table if they exist, or NULL if they do not.

#### Q24: What is a database index?
**Answer:** A data structure (usually a B-tree) that allows the database engine to find specific rows quickly without having to scan the entire table.

#### Q25: Does creating a Primary Key create an index automatically?
**Answer:** Yes. PostgreSQL automatically creates a unique B-tree index on any column designated as a Primary Key or UNIQUE.

#### Q26: Does creating a Foreign Key create an index automatically in PostgreSQL?
**Answer:** No! PostgreSQL does NOT automatically create indexes on Foreign Key columns. Developers must manually create them.

#### Q27: What is a Sequential Scan (`Seq Scan`)?
**Answer:** An execution method where PostgreSQL reads every single block of a table from beginning to end to find matching rows.

#### Q28: What is an Index Scan?
**Answer:** An execution method where PostgreSQL navigates an index tree to locate matching row pointers, then visits only those specific rows in the table.

#### Q29: What is `EXPLAIN (ANALYZE, BUFFERS)`?
**Answer:** A PostgreSQL command that actually executes the query, records real execution time, displays the chosen execution plan, and reports how many shared memory buffer blocks were hit or read.

#### Q30: Why do write queries (`W01`–`W05`) need `ROLLBACK` during benchmarking?
**Answer:** Wrapping them in `BEGIN ... ROLLBACK` allows us to measure actual insert/update/delete performance while discarding the modifications so the underlying dataset remains unchanged for subsequent runs.

---

## Part 2: 20 Intermediate Viva Questions (Project Specifics & Mechanisms)

#### Q31: What was the total baseline execution time across all 30 queries?
**Answer:** 16,367.651 ms (~16.37 seconds).

#### Q32: Which query was the slowest in our baseline benchmark, and what was its average time?
**Answer:** Query `R18` (Last trip date of every Pune rider), taking an average of **15,918.767 ms** (~15.92 seconds).

#### Q33: Why is query `R18` so extraordinarily slow in our baseline?
**Answer:** It uses a correlated subquery: for every rider whose home city is Pune (~3,000 riders), PostgreSQL must run a subquery to find `max(requested_at)`. Because `trips` has no index on `rider_id`, the database scans all 300,000 trips 3,000 separate times, evaluating roughly 900 million rows!

#### Q34: Which query was the fastest, and why?
**Answer:** Query `R14` (0.032 ms). It looks up a vehicle by registration number using the unique index on `vehicles(registration_no)`, and then joins driver details using the primary key index on `drivers(driver_id)`. Both lookups are instant B-tree seeks.

#### Q35: In query `R03` (Login by email), why did PostgreSQL perform a Seq Scan even though `email` is UNIQUE?
**Answer:** The query filters with `WHERE LOWER(email) = '...'`. Standard B-tree indexes index the raw string, not the lowercase version. Applying a function disables standard index usage unless a specialized **expression index** on `LOWER(email)` is created.

#### Q36: What is a Cold Cache versus a Warm Cache?
**Answer:** A cold cache occurs when data pages are read from physical disk storage for the first time. A warm cache occurs when pages already reside in PostgreSQL's RAM buffer cache, making subsequent reads orders of magnitude faster.

#### Q37: How did we see caching in our actual numbers for Query `R01`?
**Answer:** In Run 1, `R01` took **16.928 ms** (cold run). In Run 2 and Run 3, it took **7.475 ms** and **7.128 ms** (warm cache in RAM), resulting in an average of 10.510 ms.

#### Q38: What does `grep -oE 'Execution Time: [0-9.]+' | awk '{print $3}'` do in our script?
**Answer:** It searches the PostgreSQL `EXPLAIN ANALYZE` output for the line containing `Execution Time: <number>`, isolates the match, and prints the numeric value so our script can calculate averages.

#### Q39: What is the purpose of `ANALYZE` in PostgreSQL?
**Answer:** `ANALYZE` scans table samples to gather statistics about value distribution and row counts, storing them in system catalogs (`pg_statistic`) so the query planner can make intelligent decisions.

#### Q40: What is the difference between `WHERE` and `HAVING`?
**Answer:** `WHERE` filters rows before any aggregation takes place. `HAVING` filters aggregated groups after the `GROUP BY` operation.

#### Q41: What does `date_trunc('month', requested_at)` do in query `R23`?
**Answer:** It truncates a timestamp down to the beginning of the month (e.g. `2026-05-18 14:30:00` becomes `2026-05-01 00:00:00`), allowing queries to aggregate data monthly.

#### Q42: What is the `FILTER` clause in modern PostgreSQL aggregates (as in R17)?
**Answer:** It allows conditional aggregation within a single query pass. For example, `count(*) FILTER (WHERE status LIKE 'CANCELLED%')` counts only cancelled trips without needing a separate subquery.

#### Q43: What is the issue with `OFFSET 200000 LIMIT 25` in query `R16`?
**Answer:** PostgreSQL must scan and discard all 200,000 previous rows in index order before reading the 25 rows requested, wasting 20 ms. This is known as the "high offset pagination" problem.

#### Q44: What is Keyset Pagination, and how will it fix `R16` in CP3?
**Answer:** Keyset pagination uses a `WHERE trip_id < last_seen_id ORDER BY trip_id DESC LIMIT 25` clause instead of `OFFSET`. The index jumps straight to `last_seen_id` in $O(\log N)$ time instead of scanning 200,000 rows.

#### Q45: In query `R02`, why is `DATE(requested_at) BETWEEN '2026-03-01' AND '2026-03-31'` non-sargable?
**Answer:** Wrapping `requested_at` in the `DATE()` function prevents the query planner from using an index on `requested_at`. It can be made "sargable" (search-argument-able) by writing `requested_at >= '2026-03-01' AND requested_at < '2026-04-01'`.

#### Q46: What does `shared hit` mean in `EXPLAIN (ANALYZE, BUFFERS)`?
**Answer:** It represents the number of 8 KB database pages that were found already present in PostgreSQL's shared buffer pool in RAM, avoiding disk I/O.

#### Q47: What does `shared read` mean in `EXPLAIN (ANALYZE, BUFFERS)`?
**Answer:** It represents the number of 8 KB database pages that were NOT in RAM and had to be read from the physical disk/storage subsystem.

#### Q48: How does PostgreSQL handle parallel query execution in baseline queries like `R01`?
**Answer:** The planner launches worker processes (e.g., 2 workers) using a `Gather` node. Each worker scans a portion of the table, and the parent process gathers and sorts the final results.

#### Q49: What is the purpose of `team.json`?
**Answer:** It stores standardized machine-readable team metadata (team number, student names, enrollment numbers, GitHub usernames, laptop hardware specifications, and PostgreSQL version) evaluated by automated evaluation grading scripts.

#### Q50: How many total queries are in the workload, and what is the breakdown?
**Answer:** 30 total queries: 25 read queries (`R01` through `R25`) and 5 write queries (`W01` through `W05`).

---

## Part 3: 10 Challenging Viva Questions (Advanced Query Plans & Theory)

#### Q51: In query `R09`, marketing looks for riders with no trips since April using `NOT IN (SELECT ...)`. Why is `NOT IN` dangerous with NULLs?
**Answer:** If the subquery returns even a single row with a `NULL` value, SQL's three-valued logic causes `x NOT IN (...)` to evaluate to `UNKNOWN` (false) for all rows, resulting in an empty result set! In CP3, replacing `NOT IN` with `NOT EXISTS` avoids this bug and allows the planner to use an anti-join.

#### Q52: What is a Hash Join, and when does PostgreSQL choose it?
**Answer:** A Hash Join reads the smaller table into memory, builds an in-memory hash table on the join key, and then scans the larger table, probing the hash table for matches. PostgreSQL chooses it when joining large unindexed tables where sorting would be too expensive.

#### Q53: What is a Nested Loop Join, and when is it preferred?
**Answer:** For every row in the outer table, it searches for matching rows in the inner table. It is preferred when the outer table has few rows and the inner table has an index on the join column, resulting in fast $O(1)$ or $O(\log N)$ seeks.

#### Q54: What is a Merge Join?
**Answer:** A join that requires both input tables to be sorted on the join key. It walks through both sorted streams simultaneously in $O(M + N)$ linear time.

#### Q55: Why did query `W04` (Bulk import of 5,000 trips) take ~31.5 ms?
**Answer:** Although generating series is fast, inserting 5,000 rows into `trips` requires PostgreSQL to verify foreign key constraints across 5 parent tables (`riders`, `drivers`, `vehicles`, `cities`, `promo_codes`) for every row, triggering 25,000 foreign key lookups inside one transaction.

#### Q56: Why does PostgreSQL automatically index Primary Keys and Unique constraints, but NOT Foreign Keys?
**Answer:** Primary Keys and Unique constraints enforce a uniqueness guarantee on write, requiring an immediate index lookup. Foreign Keys enforce that the referenced row exists, which only checks the parent table's Primary Key. The child table column itself does not need uniqueness, so indexing it is left to the developer depending on whether joins and deletes on that relationship are frequent.

#### Q57: What is an Index-Only Scan?
**Answer:** An execution plan where PostgreSQL retrieves all required columns directly from the index tree without having to visit the actual table heap pages at all. This requires that all requested columns be present in the index and the pages marked visible in the Visibility Map.

#### Q58: What is a Partial Index, and where could it help in our project?
**Answer:** A partial index includes only rows that satisfy a `WHERE` predicate (e.g. `CREATE INDEX ON trips(requested_at) WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING');`). In query `R05`, active trips represent less than 1% of the 300,000 rows. A partial index would index only a few hundred rows instead of 300,000, drastically speeding up dispatch queries.

#### Q59: What is a Trigram (GIN) Index, and which query requires it?
**Answer:** Query `R13` searches riders using `WHERE full_name ILIKE '%sharma%'`. Standard B-trees cannot search strings starting with a wildcard (`%`). A GIN index using the `pg_trgm` extension breaks strings into 3-character slices ("tri-grams"), enabling fast index lookups for arbitrary substring and regex searches.

#### Q60: If your professor asks: "What is your main takeaway from Checkpoint 2?", what should you say?
**Answer:** 
> *"In Checkpoint 2, we established an empirical baseline by measuring all 30 production workload queries in PostgreSQL 18.6 with three runs each. The total workload took 16.37 seconds, with query R18 alone taking 15.92 seconds (97.26% of total time) due to an unindexed correlated subquery. We proved that while Primary Key point lookups like R14 and R15 run in sub-millisecond time (0.03 ms), multi-table joins and foreign key lookups degrade severely into sequential scans because foreign keys are unindexed. This baseline gives us the exact targets we need to optimize in Checkpoint 3."*

---
*End of Viva Preparation Guide. Good luck with your examination!*
