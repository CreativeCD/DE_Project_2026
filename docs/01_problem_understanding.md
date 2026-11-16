# Phase 1: Problem Understanding & Workload Classification

## 1. Executive Summary

Uber India operates a high-volume on-demand ride-hailing platform across **10 metropolitan cities**: Bengaluru, Mumbai, Delhi, Hyderabad, Chennai, Pune, Kolkata, Ahmedabad, Jaipur, and Lucknow. The system orchestrates dynamic ride matching, real-time dispatch, geospatial tracking, automated pricing, payment reconciliation, and mutual ratings between riders and driver partners.

The platform's existing database layer suffers from degraded responsiveness, unindexed queries, and lack of documented constraints. With business operations projecting a **10–20× increase in ride volume** over the coming year (scaling from 300,000 trips to over 6,000,000 trips), this engineering initiative evaluates nine critical pain points (P1–P9) across product, operations, trust, and executive teams, establishing rigorous performance targets and operational boundaries.

---

## 2. Problem Statements Analysis (P1 – P9)

| # | Business Problem & Operational Impact | Stakeholder Affected | Related Queries | Workload Classification | Target Latency (Scale) |
|---|---------------------------------------|----------------------|-----------------|-------------------------|------------------------|
| **P1** | **Rider Trip History Latency:** Frequent riders experience severe lag when opening the "Your Trips" screen. The system executes full table scans to filter and sort historical trips for a single rider, causing high app drop-offs. | Rider, Rider App Engineering | `R01`, `R15` | **Customer-Facing / Real-Time** | **< 5 ms** |
| **P2** | **Driver Earnings Dashboard Delays:** Drivers check earnings balances multiple times per shift. Aggregating monthly completed trip fares on demand scans the entire trips table, causing UI stalls and eroding driver partner trust. | Driver Partners, Driver Operations | `R02`, `R07`, `R19` | **Customer-Facing / Real-Time** | **< 5 ms** |
| **P3** | **Case-Insensitive Authentication Failure:** Riders entering mixed-case email addresses experienced login failures. Wrapping `LOWER(email)` without functional indexing bypasses existing B-tree indexes, making authentication sluggish. | Riders, Identity & Auth Team | `R03` | **Customer-Facing / Real-Time** | **< 5 ms** |
| **P4** | **Live Fleet Dispatch Refresh Lag:** City operations consoles require refreshing live supply and active demand every 3 seconds. Unindexed queries scanning hundreds of thousands of historical trips to locate ~300 active trips exceed the 3-second cycle. | City Operations (Dispatchers, Fleet Ops) | `R04`, `R05`, `W01`, `W02` | **Customer-Facing / Operational Real-Time** | **< 5 ms** |
| **P5** | **Financial Reporting Timeouts:** End-of-month financial reconciliation reports (aggregating gross booking values by payment gateway, method, and transaction failure rates) time out due to unbounded sequential scans. | Finance, Accounting, Compliance | `R08`, `R20`, `R22` | **Reporting / Analytics** (`R22`: Interactive Ops) | **< 5,000 ms** (`R22`: < 250 ms) |
| **P6** | **Marketing Segmentation Anomalies:** CRM win-back campaigns targeting inactive riders and dormant drivers return erratic or empty datasets due to `NOT IN` subqueries encountering three-valued SQL logic (`NULL` pitfalls). | Marketing, Growth, CRM Ops | `R09`, `R10`, `R18` | **Reporting / Analytics** | **< 5,000 ms** |
| **P7** | **Trust & Safety Fraud Scan Bottlenecks:** Compliance algorithms flagging GPS spoofing, suspiciously long routes (> 43 km / > 150 min), or extreme surge/distance rates (> ₹100/km) scan the entire table on every execution. | Trust & Safety, Risk Ops | `R24`, `R25` | **Interactive Search & Operations** | **< 250 ms** |
| **P8** | **Deep Pagination Stalls in Admin Console:** Customer support and ops personnel navigating historical trips in internal portals face exponential slowdowns at high page offsets (`OFFSET 200000 LIMIT 25`). | Platform Administrators, Support Staff | `R16` | **Customer-Facing / Operational Real-Time** | **< 5 ms** |
| **P9** | **Executive Analytics Scalability Deficit:** City performance benchmarks, cancellation tracking, surge analyses, and rating distributions suffer high latency, threatening complete analytical failure under projected 10–20× scale. | Executive Leadership, City GMs, Analytics | `R06`, `R11`, `R12`, `R17`, `R21`, `R23` | **Reporting / Analytics** | **< 5,000 ms** |

---

## 3. Workload Classification & Performance SLAs

To balance OLTP concurrency against OLAP analytical throughput, workload queries are categorized into four distinct performance tiers:

```
+----------------------------------------------------------------------------------------------------+
|                                    WORKLOAD TAXONOMY & PERFORMANCE SLAs                            |
+----------------------------------------------------------------------------------------------------+
| 1. Real-Time / Customer-Facing (SLA: < 5 ms)                                                      |
|    - Queries: R01, R02, R03, R04, R05, R14, R15, R16, W01, W02                                    |
|    - Characteristic: High QPS, sub-second latency required, user-blocking mobile & dispatch apps. |
+----------------------------------------------------------------------------------------------------+
| 2. Interactive Search & Operations (SLA: < 250 ms)                                                |
|    - Queries: R13, R22, R24, R25, W03                                                             |
|    - Characteristic: Internal tooling, safety audit queues, pattern matching, driver suspension.   |
+----------------------------------------------------------------------------------------------------+
| 3. Reporting & Analytics (SLA: < 5,000 ms)                                                         |
|    - Queries: R06, R07, R08, R09, R10, R11, R12, R17, R18, R19, R20, R21, R23                     |
|    - Characteristic: Multi-table aggregations, window functions, month-over-month summaries.       |
+----------------------------------------------------------------------------------------------------+
| 4. Batch Ingestion & Maintenance (SLA: < 1,000 ms)                                                 |
|    - Queries: W04 (bulk 5k insertion), W05 (retention purge)                                      |
|    - Characteristic: Bulk writes, partition pruning, and transactional cleanup.                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Key Business & Technical Assumptions

1. **Geographic Scope & Timezones:** All operations occur within India across the 10 defined cities. Timestamps are stored with timezone offsets (`TIMESTAMPTZ` with `+05:30` IST standard). Latitude and longitude coordinates strictly fall within Indian territory ($12^\circ\text{N} - 29^\circ\text{N}$, $72^\circ\text{E} - 89^\circ\text{E}$).
2. **Lifecycle of a Ride:** A trip strictly follows the linear state progression:
   $$\text{REQUESTED} \longrightarrow \text{ACCEPTED} \longrightarrow \text{ONGOING} \longrightarrow \text{COMPLETED}$$
   Trips may transition to `CANCELLED_BY_RIDER` (from `REQUESTED` or `ACCEPTED`) or `CANCELLED_BY_DRIVER` (from `ACCEPTED`).
3. **Data Completeness by State:**
   - `REQUESTED`: `driver_id`, `vehicle_id`, `pickup_at`, `dropoff_at`, `distance_km`, `duration_min`, and `fare_amount` are `NULL`.
   - `ACCEPTED`: `driver_id` and `vehicle_id` are assigned; timestamps and final metrics remain `NULL`.
   - `ONGOING`: `pickup_at` is populated; `dropoff_at`, `distance_km`, and `fare_amount` remain `NULL`.
   - `COMPLETED`: All trip attributes must be strictly non-null.
4. **Financial Settlement Integrity:** Exactly one payment record corresponds to each completed trip (`trips.trip_id` is unique in `payments`). Cancelled and incomplete trips do not generate payment rows. Payment amounts match `fare_amount` exactly.
5. **Driver & Vehicle Association:** Every driver operates registered vehicles. When a trip has an assigned vehicle, that vehicle must belong to the assigned driver.
6. **Rating Rules:** Ratings are optional and allowed only post-completion. At most two ratings can exist per trip: one submitted by `RIDER` and one by `DRIVER`. Ratings are stored as integers from 1 to 5.
7. **Read vs. Write Trade-offs:** The database is read-heavy (90%+ read traffic vs. write traffic). Indexing strategy must prioritize sub-5ms customer-facing reads while maintaining sufficient write throughput for ride creation (`W01`, `W04`) and status transitions (`W02`, `W03`).
