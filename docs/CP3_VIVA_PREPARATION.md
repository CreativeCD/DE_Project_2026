# PalmPay / Uber DBMS Project: CP3 Viva Preparation Guide

**Author / Student:** Rusheel Chandra (Member 4)  
**Team Number:** T0061  
**Project:** PalmPay / Uber Ride-Hailing Database Management System  
**Course:** Database Management Systems (DBMS)  
**Target Checkpoint:** CP3 – Query Optimization & Indexing (Phase 4)  
**Target Repository:** `CreativeCD/DE_Project_2026`  

---

## Welcome: How to Ace Your CP3 Viva!

This guide is written in simple, friendly, student-level language specifically for our upcoming oral exam (Viva). You do not need to memorize complex academic jargon. 

When your examiner asks a question:
1. **Give a crisp 1–2 sentence definition.**
2. **Use a simple real-life analogy** (like a textbook index or dictionary).
3. **Anchor your answer with a direct example from our project** (e.g., *"In our `trips` table with 300,000 rows, query R18 dropped from 16 seconds to 2.8 milliseconds"*).

---

# Section 1: Core Concepts Made Simple

### 1. What is a Database Index?
* **Simple Definition:** An index is an auxiliary data structure (usually a sorted B-Tree) that the database builds on one or more columns to find rows rapidly without scanning the entire table.
* **Analogy:** Think of the index at the back of a 500-page textbook. If you want to find "B-tree", you don't read all 500 pages from page 1. You flip to the back, look up the letter "B", find "B-tree: page 342", and jump directly there.
* **In Our Project:** Without an index, finding the last 20 rides of rider `1042` (`R01`) forced PostgreSQL to read all 300,000 rows in `trips`. With our index, it jumps straight to rider `1042` in 0.05 ms.

---

### 2. What is a Sequential Scan (Seq Scan)?
* **Simple Definition:** A database scan where PostgreSQL reads every single block of a table from beginning to end to check which rows match the `WHERE` clause.
* **When is it used:** 
  1. When no suitable index exists.
  2. When the table is very small (e.g., our `cities` table with only 10 rows).
  3. When a query needs to read most of the table anyway (e.g., `R17`, which calculates city cancellation percentages across 100% of trips).

---

### 3. What is a B-Tree Index?
* **Simple Definition:** B-Tree stands for **Balanced Tree**. It is a self-balancing tree data structure that keeps data sorted and allows search, sequential access, insertions, and deletions in logarithmic time: $O(\log N)$.
* **How it works:**
  * **Root Node:** The starting point.
  * **Internal Nodes:** Branching signposts that direct PostgreSQL left or right based on whether the search key is greater or smaller.
  * **Leaf Nodes:** The bottom layer that contains the actual indexed values and pointers (TIDs - Tuple IDs) to the physical rows on disk.
* **Why it's default:** B-trees excel at both exact lookups (`col = 5`) and range lookups (`col BETWEEN 10 AND 50`).

---

### 4. What is a Composite Index (Multi-Column Index)?
* **Simple Definition:** An index built on two or more columns together.
* **Example in Our Project:** `idx_trips_rider_requested ON trips (rider_id, requested_at DESC)`.
* **The "Left-to-Right" Rule (VERY POPULAR VIVA QUESTION!):**
  * PostgreSQL sorts the index by the **first** column first, and then within identical values of the first column, it sorts by the **second** column.
  * *Golden Rule of Column Order:* **Equality columns first, Range/Sorting columns second.**
  * *Why:* In `R01`, `rider_id = 1042` is an equality filter, so it goes first. `requested_at DESC` is for sorting, so it goes second. PostgreSQL finds rider 1042, and the rows are already in descending date order, eliminating any sorting step!

---

### 5. What is a Partial Index?
* **Simple Definition:** An index that only includes rows satisfying a specific `WHERE` condition, rather than indexing every single row in the table.
* **Syntax:** `CREATE INDEX idx_name ON table (column) WHERE condition;`
* **Real Project Example (Query R05):**
  * Out of 300,000 trips, over 98% are completed or cancelled. Only ~1,500 trips are active (`REQUESTED`, `ACCEPTED`, `ONGOING`).
  * We created: `CREATE INDEX idx_trips_active_dispatch ON trips (requested_at) WHERE status IN ('REQUESTED', 'ACCEPTED', 'ONGOING');`
  * **Why it matters:** 
    1. A normal index on 300,000 rows would be ~8 MB. Our partial index is only **64 KB**!
    2. It fits entirely in CPU cache and executes in 0.07 ms.
    3. Rows with status `COMPLETED` never touch this index, so completing a trip doesn't trigger index updates.

---

### 6. What is a Covering Index and an Index-Only Scan (`INCLUDE`)?
* **Simple Definition:** A covering index contains all the columns a query needs—both the filter columns in `WHERE` and the payload columns in `SELECT`/`GROUP BY`.
* **What is an Index-Only Scan:**
  * Normally, an index scan finds the row location in the B-tree, and then PostgreSQL must visit the table on disk (the "Heap") to read other columns. This is called a Heap Fetch.
  * In an **Index-Only Scan**, PostgreSQL finds **all required data directly inside the index leaf nodes**. It never touches the table heap at all! (`Heap Fetches: 0`).
* **In Our Project (Query R02):**
  ```sql
  CREATE INDEX idx_trips_driver_status_date 
  ON trips (driver_id, status, requested_at) 
  INCLUDE (fare_amount);
  ```
  `fare_amount` is stored in the leaf nodes. The driver earnings calculation runs entirely in-memory from the index!

---

### 7. What is an Expression (Functional) Index?
* **Simple Definition:** An index created on the result of a function or expression applied to a column, rather than the raw column itself.
* **Why do we need it (Query R03)?**
  * When a user logs in, the query runs: `WHERE LOWER(email) = 'user@mail.com'`.
  * Even though `email` has a UNIQUE index, PostgreSQL **cannot** use it because `LOWER(email)` is a function. The B-tree only contains uppercase/lowercase as originally typed.
  * Solution: `CREATE INDEX idx_riders_lower_email ON riders (LOWER(email));`
  * PostgreSQL pre-evaluates `LOWER(email)` and stores the lowercase value in the index, dropping runtime from 6.6 ms to 0.04 ms!

---

### 8. What is a GIN Trigram Index?
* **Simple Definition:** 
  * **GIN:** Generalized Inverted Index.
  * **Trigram (`pg_trgm`):** Slices text into 3-character consecutive chunks (e.g. `'sharma'` $\rightarrow$ `['sha', 'har', 'arm', 'rma']`).
* **Why B-Tree fails on wildcard searches (Query R13):**
  * B-Tree can search prefixes like `WHERE name LIKE 'sharma%'` because values are sorted alphabetically.
  * B-Tree **cannot** search leading wildcards like `WHERE name ILIKE '%sharma%'` because the word could start with anything.
  * GIN with trigrams indexes the 3-letter fragments. When you search `%sharma%`, it looks up the trigrams and finds the matching rows in 0.6 ms!

---

### 9. What is "Sargability" (Search Argument Able)?
* **Simple Definition:** A query predicate is **sargable** if the database engine can take advantage of an index to perform a range or equality search.
* **What makes a query non-sargable?** Wrapping the indexed column inside a function or type-cast on the left side of an operator!
  * ❌ *Non-sargable:* `WHERE DATE(requested_at) BETWEEN '2026-03-01' AND '2026-03-31'`
  * ❌ *Non-sargable:* `WHERE requested_at::date >= '2026-05-01'`
  * ❌ *Non-sargable:* `WHERE EXTRACT(YEAR FROM paid_at) = 2026`
* **How to make it sargable (Our CP3 Rewrites):** Keep the column completely bare and compare it against literal timestamp ranges!
  * ✅ *Sargable:* `WHERE requested_at >= '2026-03-01 00:00:00+05:30' AND requested_at < '2026-04-01 00:00:00+05:30'`
  * Now the query planner can use the B-tree index directly!

---

### 10. Why was Query R18 taking 16 seconds (The CP2 Bottleneck)?
* **The Original Query:**
  ```sql
  SELECT r.rider_id, r.full_name,
         (SELECT max(t.requested_at) FROM trips t WHERE t.rider_id = r.rider_id) AS last_trip_at
  FROM riders r
  WHERE r.home_city_id = 6;
  ```
* **The Root Cause:**
  * It used a **correlated scalar subquery**.
  * Pune (`home_city_id = 6`) has 2,400 riders.
  * For **every single one** of those 2,400 riders, PostgreSQL ran the subquery separately.
  * Each subquery scanned the entire 300,000-row `trips` table.
  * Total rows checked = $2,400 \times 300,000 = \mathbf{720,000,000\text{ rows}}$!
  * That caused 13.9 million buffer hits and took **15.9 seconds**!
* **How We Fixed It (5,569× speedup):**
  * We rewrote the correlated subquery into a set-oriented **`LEFT JOIN`** with **`GROUP BY`**:
    ```sql
    SELECT r.rider_id, r.full_name, max(t.requested_at) AS last_trip_at
    FROM riders r
    LEFT JOIN trips t ON t.rider_id = r.rider_id
    WHERE r.home_city_id = 6
    GROUP BY r.rider_id, r.full_name
    ORDER BY last_trip_at DESC NULLS LAST;
    ```
  * Combined with our index `idx_trips_rider_requested`, PostgreSQL did a single Hash Left Join and Hash Aggregate in **2.8 milliseconds**!

---

### 11. 🔎 The Subtle Bug in Query R10 (The NULL Trap in SQL)
* **What the Query Did:** Marketing wanted a list of active drivers who hadn't taken any trips since 25 June 2026.
* **The Baseline Query:**
  ```sql
  SELECT d.driver_id, d.full_name, d.city_id
  FROM drivers d
  WHERE d.status = 'ACTIVE'
    AND d.driver_id NOT IN (
        SELECT t.driver_id FROM trips t WHERE t.requested_at >= '2026-06-25'
    );
  ```
* **Why it returned ZERO rows (The 3-Valued Logic Bug):**
  * In the `trips` table, `driver_id` can be `NULL` (when a ride is requested but not yet accepted by a driver).
  * If the subquery contains even **one** `NULL`, SQL evaluates `NOT IN` as `UNKNOWN`!
  * Here is the math:
    $$\text{driver\_id IN }(10, 20, \text{NULL}) \equiv (\text{driver\_id} = 10) \lor (\text{driver\_id} = 20) \lor (\text{driver\_id} = \text{NULL})$$
    If driver_id is not 10 or 20, it evaluates to:
    $$\text{FALSE} \lor \text{FALSE} \lor \text{UNKNOWN} \implies \text{UNKNOWN}$$
    $$\text{NOT (UNKNOWN)} \implies \mathbf{UNKNOWN}$$
  * In SQL, a `WHERE` clause only keeps rows that evaluate to **`TRUE`**. Rows evaluating to `UNKNOWN` are thrown away!
  * Result: **All 3,000 drivers were thrown away, and the query returned 0 rows!**
* **The Fix:** Rewrite using **`NOT EXISTS`**:
  ```sql
  SELECT d.driver_id, d.full_name, d.city_id
  FROM drivers d
  WHERE d.status = 'ACTIVE'
    AND NOT EXISTS (
        SELECT 1 FROM trips t
        WHERE t.driver_id = d.driver_id
          AND t.requested_at >= '2026-06-25'
    );
  ```
  `NOT EXISTS` checks whether a matching row exists. `NULL` comparisons evaluate cleanly, fixing the bug, returning the real drivers, and running in 1.3 ms!

---

### 12. What is Write Overhead and Why Can't We Just Add 100 Indexes?
* **Viva Question:** *"If indexes make queries fast, why not create an index on every single column?"*
* **Student Answer:**
  * Every index consumes disk space and memory.
  * More importantly, **every `INSERT`, `UPDATE`, and `DELETE` must update all the indexes on that table**.
  * If a table has 10 indexes, inserting 1 row means writing to 1 table heap plus 10 B-trees!
  * **In Our Project:**
    * Single insert (`W01`) went from 0.55 ms to 0.76 ms (+0.2 ms overhead).
    * Batch insert of 5,000 trips (`W04`) went from 31.5 ms to 40.4 ms (+8.8 ms overhead).
    * This overhead is very small and completely acceptable because our reads got 100× to 5,000× faster!
    * Interestingly, write queries like `W02` (complete oldest trip) actually became **24× faster** because finding the target row using `idx_trips_ongoing_min` was instantaneous!

---

# Section 2: Top 15 Quick-Fire Viva Questions & Answers

**Q1: What command did you use to measure query execution time?**  
> *"We used `EXPLAIN (ANALYZE, BUFFERS)` in PostgreSQL. `ANALYZE` actually runs the query and records real execution time in milliseconds, and `BUFFERS` shows shared buffer cache hits and disk reads."*

**Q2: What is the difference between Planning Time and Execution Time?**  
> *"Planning Time is how long PostgreSQL takes to parse the SQL, consider different join paths and indexes, and choose the cheapest execution plan. Execution Time is how long it takes the engine to physically fetch the rows and compute the result."*

**Q3: What is the difference between a Buffer Hit and a Buffer Read?**  
> *"A Buffer Hit (`shared hit`) means the 8 kB data page was already cached in RAM memory. A Buffer Read (`shared read`) means PostgreSQL had to read the block from physical SSD/disk storage, which is much slower."*

**Q4: What was the total workload time before and after optimization?**  
> *"In CP2 baseline, the 30 queries took 16,367 ms (~16.4 seconds). In CP3 optimized, they took only 148.9 ms (~0.15 seconds). That is an overall workload improvement of 99.09% (110× faster)."*

**Q5: Which single query was your biggest bottleneck?**  
> *"Query R18 (finding the last trip date of all Pune riders). In baseline, it took 15,918 ms (almost 16 seconds), which was 97% of the entire project runtime! After rewriting the correlated subquery to a LEFT JOIN and adding an index on `trips(rider_id, requested_at DESC)`, it dropped to 2.85 ms (a 5,569× speedup)."*

**Q6: Why did you put `rider_id` before `requested_at` in `idx_trips_rider_requested`?**  
> *"Because of the composite index prefix rule: equality columns first, sorting/range columns second. The query filters on `WHERE rider_id = 1042`, so PostgreSQL navigates directly to that rider, where the entries are already pre-sorted by `requested_at DESC`. It reads the top 20 rows and stops."*

**Q7: What is a Covering Index?**  
> *"A covering index is created with the `INCLUDE` clause, like `CREATE INDEX ... (driver_id, status, requested_at) INCLUDE (fare_amount)`. The extra payload columns are stored in the leaf nodes, allowing PostgreSQL to perform an **Index Only Scan** without reading the table heap."*

**Q8: Why did you use a Partial Index for R05?**  
> *"Because R05 only cares about active trips (`REQUESTED`, `ACCEPTED`, `ONGOING`). Active trips represent less than 2% of the table. A partial index on active trips is only 64 KB, fits completely in CPU cache, and ignores completed trips."*

**Q9: What was the wrong-result query you found in the workload?**  
> *"Query R10! It used `WHERE driver_id NOT IN (SELECT driver_id FROM trips ...)`. Because `trips.driver_id` can be NULL for unassigned rides, SQL three-valued logic evaluated `NOT IN` to `UNKNOWN` for every driver, returning 0 rows. We fixed it by rewriting it to `NOT EXISTS`."*

**Q10: Why did query R03 need an expression index?**  
> *"Because R03 searched on `WHERE LOWER(email) = ...`. Standard B-tree indexes cannot index expressions on columns. An expression index `CREATE INDEX ... ON riders (LOWER(email))` stores the pre-computed lowercase values."*

**Q11: Why didn't query R16 (Admin panel page 8,001) get much faster?**  
> *"Because R16 uses `OFFSET 200000 LIMIT 25`. In SQL, `OFFSET N` forces the database to scan through 200,000 entries before returning the next 25 rows. Even with an index scan, it must traverse 200,000 index leaf entries. The true solution in production is keyset pagination (`WHERE trip_id < last_seen_id LIMIT 25`)."*

**Q12: Why didn't query R17 get 100× faster like R01?**  
> *"Query R17 calculates cancellation percentages across all 300,000 trips in the table. When a query must aggregate 100% of rows, a parallel sequential scan is optimal because reading large contiguous disk pages is faster than random index lookups."*

**Q13: How did write queries perform after adding indexes?**  
> *"Single insert `W01` took 0.76 ms (an acceptable +0.2 ms overhead). But `W02` (complete oldest trip) actually became 24× faster because our partial index `idx_trips_ongoing_min` allowed the subquery to find the oldest trip in 0.02 ms instead of scanning the table."*

**Q14: What is the purpose of `VACUUM ANALYZE`?**  
> *"`ANALYZE` updates the PostgreSQL catalog statistics so the cost-based query planner knows the distribution of values and chooses our new indexes. `VACUUM` cleans up dead tuples and updates visibility maps to enable Index Only Scans."*

**Q15: What total storage size did your indexes consume?**  
> *"Our 17 performance indexes take approximately 59.8 MB on disk, which is around 60% of total table data. Partial indexes saved huge amounts of space, taking less than 100 KB each."*

---

### Final Tip for the Exam:
Stay calm, speak clearly, smile, and remember: **you understand the real engineering trade-offs!** You know why Seq Scan happens, how B-trees fix it, how to eliminate non-sargable functions, and how SQL 3-valued logic works. You are 100% prepared!
