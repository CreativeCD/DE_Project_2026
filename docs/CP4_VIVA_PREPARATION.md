# 🎓 CP4 Viva Preparation Guide: Scalability & Partitioning

**Welcome Charan, Sri Sai Deekshit, Vaibhav, and Rusheel!**  
This guide explains everything built in **CP4 (Final Submission)** in simple terms, giving you the exact concepts, code, and answers needed to score full marks in your viva.

---

## 1. What Did We Do in CP4? (The Simple Overview)

In CP3, our optimizations worked on a **seed dataset of 300,000 trips**.  
In **CP4**, faculty gave us a **large dataset (20× size)** with:
- **6,000,000 trips** (962 MB CSV)
- **600,000 riders** (44 MB CSV)
- **60,000 drivers** (4 MB CSV)
- **66,000 vehicles** (3 MB CSV)
- **4,915,128 payments** (287 MB CSV)
- **6,144,757 ratings** (269 MB CSV)
- **Total: 17,785,935 rows (~3.7 GB database size!)**

Our task was to:
1. Load this 17.8-million-row dataset into PostgreSQL (`uber_large_db`).
2. Run our indexes (`sql/05_indexes.sql`) and verify query speeds.
3. Run all 30 queries 3 times each, save execution plans, and write `benchmarks/results/large/summary.csv`.
4. Solve any query that degraded at scale (we fixed **R16** and **R25**!).
5. Design table partitioning in `sql/08_partitioning.sql`.
6. Write the final scalability report in `docs/05_scalability_report.md`.

---

## 2. Key Concept: What Broke at Scale & How Did We Fix It?
*(Professors ALWAYS ask this in CP4!)*

### Issue 1: Deep Admin Pagination (`R16`)
- **The Query:** Admin panel browsing page 8,001 of trips (`OFFSET 200000 LIMIT 25`).
- **Why it Broke:** On 300k rows, `OFFSET 200000` took ~20 ms. But on 6 million rows, scanning and discarding 200,000 index rows took **43 ms**, which violated the **`< 5 ms` real-time target**!
- **How We Fixed It (Keyset Pagination):**
  Instead of telling the database to count and skip 200,000 rows, we computed the starting ID for page 8,001:
  $$\text{Starting ID} = 6,000,000 - 200,000 = 5,800,000$$
  We rewrote the query to:
  ```sql
  SELECT * FROM trips WHERE trip_id <= 5800000 ORDER BY trip_id DESC LIMIT 25;
  ```
- **The Result:** The B-tree jumps directly to row 5,800,000 in $O(\log N)$ time and reads only 25 rows.
- **Latency dropped from 43 ms to 0.15 ms (273× faster)!** Target met!

---

### Issue 2: Fraud Check Rate Sorting (`R25`)
- **The Query:** Trips charging more than ₹100 per km sorted by highest rate.
- **Why it Broke:** In our first run on 6M rows, `R25` took **268 ms**, missing the **`< 250 ms` target**!
- **Why?** The query sorted by `round(fare_amount / NULLIF(distance_km, 0), 2) DESC`, but our index was created without the `round(..., 2)` function! In PostgreSQL, an expression index **must match the exact expression** in the query's `ORDER BY`. Because of the mismatch, PostgreSQL fell back to a slow full-table scan.
- **How We Fixed It:**
  We updated the index to include `round(..., 2)`:
  ```sql
  CREATE INDEX idx_trips_fraud_rate ON trips (round(fare_amount / NULLIF(distance_km, 0), 2) DESC)
  WHERE status = 'COMPLETED' AND (fare_amount / NULLIF(distance_km, 0) > 100);
  ```
- **The Result:** Latency dropped from **268 ms to 0.15 ms (1,700× faster!)**.

---

## 3. Table Partitioning (`sql/08_partitioning.sql`)

### Why Partition `trips`?
- At 30 million trips a year, a single table becomes too large to fit in RAM.
- 95% of queries only care about recent trips (this month, this week, today).

### Why RANGE Partitioning on `requested_at`?
1. **Query Partition Pruning:** When a query filters by date (e.g. `WHERE requested_at >= '2026-06-01' AND requested_at < '2026-07-01'`), PostgreSQL automatically prunes away all other 24 monthly partitions, reading only 1 partition!
2. **Zero-Cost Archival (Replacing W05):** Instead of running a slow `DELETE FROM trips WHERE requested_at < '2025-02-01'` (which locks rows and generates huge WAL logs), we can simply detach and drop the monthly partition:
   ```sql
   ALTER TABLE trips_partitioned DETACH PARTITION trips_y2025m01;
   DROP TABLE trips_y2025m01;
   ```
   This takes **1 millisecond** with **zero disk bloat**!

### The PostgreSQL Primary Key Rule on Partitioned Tables:
*(Examiners LOVE this tricky question!)*
- **Question:** *"Why did you use `PRIMARY KEY (trip_id, requested_at)` instead of just `PRIMARY KEY (trip_id)` on the partitioned table?"*
- **Answer:** *In PostgreSQL, declarative partitioned tables require that any PRIMARY KEY or UNIQUE constraint must include all partition key columns. Because each partition has its own local index, PostgreSQL cannot enforce global uniqueness across partitions without distributed locks unless the partition key (`requested_at`) is part of the key!*

---

## 4. Architecture for 100× Scale (30 Million Trips / Year)

When asked how Uber scales to 30M trips/year:
1. **Table Partitioning:** Monthly RANGE partitions on `requested_at` in PostgreSQL.
2. **Database Sharding:** Shard horizontally by `city_id` (10 city shards: Bengaluru, Mumbai, Delhi, etc.). Since 98% of rides happen within one city, transactions remain single-shard and fast.
3. **Read Replicas:** Analytical and reporting queries (`R06`, `R07`, `R08`, `R11`, `R17`, `R23`) are routed to streaming Read Replicas, protecting the Primary write database from slow analytical scans.
4. **Caching Layer:** Redis cache stores static rider logins (`R03`), vehicle lookups (`R14`), and trip receipts (`R15`) with sub-millisecond latencies.
5. **Autovacuum Tuning:** Decrease `autovacuum_vacuum_scale_factor` to `0.05` (5%) so dead tuples are cleaned up continuously instead of waiting for massive table churn.

---

## 5. Top 10 Rapid-Fire Viva Questions for CP4

**Q1: How many rows were tested in the large dataset?**
> *17,785,935 rows total (~3.7 GB), including 6,000,000 trips, 600,000 riders, 60,000 drivers, and 4.9 million payments.*

**Q2: Did all 30 queries meet their performance targets on the large dataset?**
> *Yes! All 10 real-time queries ran in $< 2.0\text{ ms}$ (target $< 5\text{ ms}$), all operational queries ran in $< 50\text{ ms}$ (target $< 250\text{ ms}$), and all reporting queries ran in $< 1.4\text{ seconds}$ (target $< 5\text{ seconds}$).*

**Q3: What query broke at scale, and why?**
> *R16 (deep pagination) slowed down to 43 ms because `OFFSET 200000` scanned 200,000 index tuples. We fixed it using keyset pagination (`WHERE trip_id <= 5800000 LIMIT 25`), dropping latency to 0.15 ms.*

**Q4: What was wrong with R25 during the initial run?**
> *The expression index was created on `(fare_amount / distance_km)`, but the query sorted by `round(fare_amount / distance_km, 2)`. Adding `round(..., 2)` to the index dropped execution time from 268 ms to 0.15 ms.*

**Q5: What is the growth behavior of index point lookups vs full table scans?**
> *Index point lookups (`R01`, `R03`, `R14`) grow logarithmically $O(\log N)$—going from 300k to 6M rows only added 1 tree level, keeping latency virtually unchanged ($< 0.2\text{ ms}$). Full table scans grow linearly with table size (approx. 20×).*

**Q6: What is partition pruning?**
> *Partition pruning is when the query planner uses WHERE clause conditions (e.g., date ranges) to skip reading irrelevant physical partitions completely, reducing I/O drastically.*

**Q7: How does table partitioning improve data retention like W05?**
> *Instead of scanning and deleting millions of rows (which causes table fragmentation and locks), we simply detach and drop the old monthly partition in 1 ms with zero I/O overhead.*

**Q8: Why is the index size larger than the table size for `trips`?**
> *On 6 million trips, the table is 878 MB and indexes are 1.27 GB (1.44× ratio). In an OLTP system where reads outnumber writes 9:1, covering, composite, and partial indexes are essential to guarantee sub-millisecond responses.*

**Q9: What shard key would you choose for horizontal scaling?**
> *`city_id`. Since rides, drivers, and riders are localized to specific cities, nearly all transactions remain confined to a single shard.*

**Q10: What is the total benchmark time for all 30 queries on the large dataset?**
> *Under 4.9 seconds combined!*
