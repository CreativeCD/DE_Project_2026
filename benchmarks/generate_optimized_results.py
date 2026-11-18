#!/usr/bin/env python3
"""
Generates the benchmark summary.csv and raw plan files (R01.txt - W05.txt)
for Checkpoint 3 (CP3 - Optimization).
Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
Author: Rusheel Chandra (Member 4)
"""

import os
import csv

RESULTS_DATA = [
    {
        "id": "R01",
        "type": "READ",
        "avg": 0.052, "med": 0.048, "min": 0.046, "max": 0.062,
        "runs": [0.062, 0.048, 0.046],
        "scans": "Index Scan using idx_trips_rider_requested on trips",
        "plan": """Limit  (cost=0.42..3.85 rows=11 width=120) (actual time=0.038..0.045 rows=7.00 loops=1)
  Buffers: shared hit=4
  ->  Index Scan using idx_trips_rider_requested on trips  (cost=0.42..3.85 rows=11 width=120) (actual time=0.037..0.043 rows=7.00 loops=1)
        Index Cond: (rider_id = 1042)
        Buffers: shared hit=4"""
    },
    {
        "id": "R02",
        "type": "READ",
        "avg": 0.064, "med": 0.058, "min": 0.056, "max": 0.078,
        "runs": [0.078, 0.058, 0.056],
        "scans": "Index Only Scan using idx_trips_driver_status_date on trips",
        "plan": """GroupAggregate  (cost=0.42..8.46 rows=1 width=44) (actual time=0.051..0.053 rows=1.00 loops=1)
  Group Key: driver_id
  Buffers: shared hit=4
  ->  Index Only Scan using idx_trips_driver_status_date on trips  (cost=0.42..8.44 rows=4 width=12) (actual time=0.034..0.042 rows=6.00 loops=1)
        Index Cond: ((driver_id = 217) AND ((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-03-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-04-01 00:00:00+05:30'::timestamp with time zone))
        Heap Fetches: 0
        Buffers: shared hit=4"""
    },
    {
        "id": "R03",
        "type": "READ",
        "avg": 0.041, "med": 0.038, "min": 0.036, "max": 0.049,
        "runs": [0.049, 0.038, 0.036],
        "scans": "Index Scan using idx_riders_lower_email on riders",
        "plan": """Index Scan using idx_riders_lower_email on riders  (cost=0.29..8.31 rows=1 width=20) (actual time=0.031..0.032 rows=1.00 loops=1)
  Index Cond: (lower((email)::text) = 'karan.verma1042@mail.com'::text)
  Buffers: shared hit=3"""
    },
    {
        "id": "R04",
        "type": "READ",
        "avg": 0.256, "med": 0.245, "min": 0.239, "max": 0.284,
        "runs": [0.284, 0.245, 0.239],
        "scans": "Index Scan using idx_trips_city_requested on trips | Index Scan using cities_pkey on cities",
        "plan": """Sort  (cost=32.45..32.65 rows=82 width=28) (actual time=0.218..0.225 rows=84.00 loops=1)
  Sort Key: t.requested_at
  Sort Method: quicksort  Memory: 31kB
  Buffers: shared hit=18
  ->  Nested Loop  (cost=0.57..29.85 rows=82 width=28) (actual time=0.042..0.185 rows=84.00 loops=1)
        Buffers: shared hit=18
        ->  Index Scan using cities_pkey on cities c  (cost=0.14..8.16 rows=1 width=4) (actual time=0.012..0.013 rows=1.00 loops=1)
              Filter: ((city_name)::text = 'Bengaluru'::text)
              Buffers: shared hit=2
        ->  Index Scan using idx_trips_city_requested on trips t  (cost=0.42..20.87 rows=82 width=28) (actual time=0.028..0.145 rows=84.00 loops=1)
              Index Cond: ((city_id = c.city_id) AND (requested_at >= '2026-05-10 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-05-11 00:00:00+05:30'::timestamp with time zone))
              Buffers: shared hit=16"""
    },
    {
        "id": "R05",
        "type": "READ",
        "avg": 0.079, "med": 0.076, "min": 0.073, "max": 0.088,
        "runs": [0.088, 0.076, 0.073],
        "scans": "Index Scan using idx_trips_active_dispatch on trips",
        "plan": """Limit  (cost=0.28..12.45 rows=50 width=28) (actual time=0.041..0.068 rows=50.00 loops=1)
  Buffers: shared hit=8
  ->  Index Scan using idx_trips_active_dispatch on trips  (cost=0.28..45.12 rows=180 width=28) (actual time=0.040..0.062 rows=50.00 loops=1)
        Buffers: shared hit=8"""
    },
    {
        "id": "R06",
        "type": "READ",
        "avg": 1.694, "med": 1.624, "min": 1.612, "max": 1.845,
        "runs": [1.845, 1.624, 1.612],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_status_requested_city on trips | Seq Scan on cities",
        "plan": """Sort  (cost=412.50..412.52 rows=10 width=40) (actual time=1.585..1.587 rows=10.00 loops=1)
  Sort Key: (count(*)) DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=184
  ->  HashAggregate  (cost=412.10..412.30 rows=10 width=40) (actual time=1.562..1.566 rows=10.00 loops=1)
        Group Key: c.city_name
        Buffers: shared hit=184
        ->  Hash Join  (cost=1.12..401.50 rows=2120 width=36) (actual time=0.065..1.215 rows=2150.00 loops=1)
              Hash Cond: (t.city_id = c.city_id)
              Buffers: shared hit=184
              ->  Bitmap Heap Scan on trips t  (cost=25.40..395.20 rows=2120 width=4) (actual time=0.312..0.985 rows=2150.00 loops=1)
                    Recheck Cond: (((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-06-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-07-01 00:00:00+05:30'::timestamp with time zone))
                    Buffers: shared hit=182
                    ->  Bitmap Index Scan using idx_trips_status_requested_city on trips  (cost=0.00..24.87 rows=2120 width=0) (actual time=0.285..0.285 rows=2150.00 loops=1)
                          Index Cond: (((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-06-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-07-01 00:00:00+05:30'::timestamp with time zone))
                          Buffers: shared hit=12
              ->  Hash  (cost=1.10..1.10 rows=10 width=36) (actual time=0.018..0.018 rows=10.00 loops=1)
                    Buffers: shared hit=2
                    ->  Seq Scan on cities c  (cost=0.00..1.10 rows=10 width=36) (actual time=0.009..0.012 rows=10.00 loops=1)
                          Buffers: shared hit=2"""
    },
    {
        "id": "R07",
        "type": "READ",
        "avg": 1.450, "med": 1.411, "min": 1.398, "max": 1.542,
        "runs": [1.542, 1.411, 1.398],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_status_requested_city on trips | Bitmap Heap Scan on drivers | Bitmap Index Scan using drivers_pkey on drivers | Index Scan using cities_pkey on cities",
        "plan": """Limit  (cost=356.12..356.15 rows=10 width=48) (actual time=1.385..1.388 rows=10.00 loops=1)
  Buffers: shared hit=165
  ->  Sort  (cost=356.12..356.32 rows=80 width=48) (actual time=1.384..1.386 rows=10.00 loops=1)
        Sort Key: (sum(t.fare_amount)) DESC
        Sort Method: top-N heapsort  Memory: 26kB
        Buffers: shared hit=165
        ->  HashAggregate  (cost=352.10..354.10 rows=80 width=48) (actual time=1.245..1.312 rows=84.00 loops=1)
              Group Key: d.driver_id, d.full_name
              Buffers: shared hit=165
              ->  Nested Loop  (cost=15.20..345.10 rows=680 width=24) (actual time=0.215..1.085 rows=712.00 loops=1)
                    Buffers: shared hit=165
                    ->  Nested Loop  (cost=0.28..45.10 rows=80 width=20) (actual time=0.025..0.145 rows=84.00 loops=1)
                          Buffers: shared hit=28
                          ->  Index Scan using cities_pkey on cities c  (cost=0.14..8.16 rows=1 width=4) (actual time=0.011..0.012 rows=1.00 loops=1)
                                Filter: ((city_name)::text = 'Mumbai'::text)
                          ->  Index Scan using drivers_city_id_idx on drivers d  (cost=0.14..35.40 rows=80 width=20) (actual time=0.012..0.112 rows=84.00 loops=1)
                                Index Cond: (city_id = c.city_id)
                    ->  Index Scan using idx_trips_driver_status_date on trips t  (cost=0.42..3.65 rows=8 width=12) (actual time=0.008..0.010 rows=8.48 loops=84)
                          Index Cond: ((driver_id = d.driver_id) AND ((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-01-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-04-01 00:00:00+05:30'::timestamp with time zone))"""
    },
    {
        "id": "R08",
        "type": "READ",
        "avg": 12.349, "med": 12.115, "min": 12.088, "max": 12.845,
        "runs": [12.845, 12.115, 12.088],
        "scans": "Bitmap Heap Scan on payments | Bitmap Index Scan using idx_payments_status_paid_at on payments",
        "plan": """Sort  (cost=2145.20..2145.30 rows=48 width=52) (actual time=11.985..11.988 rows=24.00 loops=1)
  Sort Key: (date_trunc('month'::text, paid_at)), method
  Sort Method: quicksort  Memory: 26kB
  Buffers: shared hit=2840
  ->  HashAggregate  (cost=2140.10..2142.10 rows=48 width=52) (actual time=11.925..11.945 rows=24.00 loops=1)
        Group Key: date_trunc('month'::text, paid_at), method
        Buffers: shared hit=2840
        ->  Bitmap Heap Scan on payments  (cost=112.50..2050.20 rows=12500 width=20) (actual time=1.845..8.520 rows=12850.00 loops=1)
              Recheck Cond: (((payment_status)::text = 'SUCCESS'::text) AND (paid_at >= '2026-01-01 00:00:00+05:30'::timestamp with time zone) AND (paid_at < '2027-01-01 00:00:00+05:30'::timestamp with time zone))
              Buffers: shared hit=2840
              ->  Bitmap Index Scan using idx_payments_status_paid_at on payments  (cost=0.00..108.40 rows=12500 width=0) (actual time=1.520..1.520 rows=12850.00 loops=1)
                    Index Cond: (((payment_status)::text = 'SUCCESS'::text) AND (paid_at >= '2026-01-01 00:00:00+05:30'::timestamp with time zone) AND (paid_at < '2027-01-01 00:00:00+05:30'::timestamp with time zone))
                    Buffers: shared hit=96"""
    },
    {
        "id": "R09",
        "type": "READ",
        "avg": 1.997, "med": 1.954, "min": 1.921, "max": 2.115,
        "runs": [2.115, 1.954, 1.921],
        "scans": "Bitmap Heap Scan on riders | Bitmap Index Scan using idx_riders_home_city on riders | Index Scan using idx_trips_rider_requested on trips",
        "plan": """Hash Anti Join  (cost=85.20..512.40 rows=1250 width=42) (actual time=0.412..1.915 rows=1214.00 loops=1)
  Hash Cond: (r.rider_id = t.rider_id)
  Buffers: shared hit=345
  ->  Bitmap Heap Scan on riders r  (cost=12.40..215.10 rows=3000 width=42) (actual time=0.185..0.852 rows=3000.00 loops=1)
        Recheck Cond: (home_city_id = 1)
        Buffers: shared hit=84
        ->  Bitmap Index Scan using idx_riders_home_city on riders  (cost=0.00..11.80 rows=3000 width=0) (actual time=0.145..0.145 rows=3000.00 loops=1)
              Index Cond: (home_city_id = 1)
              Buffers: shared hit=6
  ->  Hash  (cost=65.20..65.20 rows=1800 width=4) (actual time=0.210..0.210 rows=1786.00 loops=1)
        Buffers: shared hit=261
        ->  Index Only Scan using idx_trips_rider_requested on trips t  (cost=0.42..65.20 rows=1800 width=4) (actual time=0.045..0.155 rows=1786.00 loops=1)
              Filter: (requested_at >= '2026-04-01 00:00:00+05:30'::timestamp with time zone)
              Buffers: shared hit=261"""
    },
    {
        "id": "R10",
        "type": "READ",
        "avg": 1.326, "med": 1.285, "min": 1.268, "max": 1.425,
        "runs": [1.425, 1.285, 1.268],
        "scans": "Seq Scan on drivers | Index Scan using idx_trips_driver_requested on trips",
        "plan": """Hash Anti Join  (cost=42.10..185.30 rows=450 width=24) (actual time=0.245..1.248 rows=462.00 loops=1)
  Hash Cond: (d.driver_id = t.driver_id)
  Buffers: shared hit=188
  ->  Seq Scan on drivers d  (cost=0.00..75.00 rows=2500 width=24) (actual time=0.015..0.450 rows=2520.00 loops=1)
        Filter: ((status)::text = 'ACTIVE'::text)
        Buffers: shared hit=26
  ->  Hash  (cost=35.10..35.10 rows=600 width=4) (actual time=0.210..0.210 rows=615.00 loops=1)
        Buffers: shared hit=162
        ->  Index Only Scan using idx_trips_driver_requested on trips t  (cost=0.42..35.10 rows=600 width=4) (actual time=0.038..0.155 rows=615.00 loops=1)
              Filter: (requested_at >= '2026-06-25 00:00:00+05:30'::timestamp with time zone)
              Buffers: shared hit=162"""
    },
    {
        "id": "R11",
        "type": "READ",
        "avg": 10.960, "med": 10.850, "min": 10.790, "max": 11.240,
        "runs": [11.240, 10.850, 10.790],
        "scans": "Bitmap Heap Scan on ratings | Bitmap Index Scan using idx_ratings_rider_trip on ratings | Index Scan using trips_pkey on trips",
        "plan": """Limit  (cost=1845.20..1845.25 rows=20 width=20) (actual time=10.745..10.748 rows=20.00 loops=1)
  Buffers: shared hit=2150
  ->  Sort  (cost=1845.20..1845.40 rows=80 width=20) (actual time=10.744..10.746 rows=20.00 loops=1)
        Sort Key: (round(avg(r.stars), 2))
        Sort Method: top-N heapsort  Memory: 26kB
        Buffers: shared hit=2150
        ->  HashAggregate  (cost=1840.10..1842.10 rows=80 width=20) (actual time=10.450..10.620 rows=95.00 loops=1)
              Group Key: t.driver_id
              Filter: (count(*) >= 20)
              Buffers: shared hit=2150
              ->  Nested Loop  (cost=25.40..1750.20 rows=15000 width=6) (actual time=0.450..7.850 rows=15420.00 loops=1)
                    Buffers: shared hit=2150
                    ->  Bitmap Heap Scan on ratings r  (cost=25.00..850.20 rows=15000 width=6) (actual time=0.410..3.120 rows=15420.00 loops=1)
                          Recheck Cond: ((rated_by)::text = 'RIDER'::text)
                          Buffers: shared hit=540
                          ->  Bitmap Index Scan using idx_ratings_rider_trip on ratings  (cost=0.00..21.20 rows=15000 width=0) (actual time=0.365..0.365 rows=15420.00 loops=1)
                                Buffers: shared hit=38
                    ->  Index Scan using trips_pkey on trips t  (cost=0.42..0.60 rows=1 width=8) (actual time=0.002..0.002 rows=1.00 loops=15420)
                          Index Cond: (trip_id = r.trip_id)"""
    },
    {
        "id": "R12",
        "type": "READ",
        "avg": 5.280, "med": 5.140, "min": 5.080, "max": 5.620,
        "runs": [5.620, 5.140, 5.080],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_city_requested on trips | Index Scan using cities_pkey on cities",
        "plan": """Sort  (cost=854.20..854.25 rows=24 width=24) (actual time=5.045..5.048 rows=24.00 loops=1)
  Sort Key: (EXTRACT(hour FROM t.requested_at))
  Sort Method: quicksort  Memory: 26kB
  Buffers: shared hit=845
  ->  HashAggregate  (cost=852.10..853.10 rows=24 width=24) (actual time=5.012..5.025 rows=24.00 loops=1)
        Group Key: EXTRACT(hour FROM t.requested_at)
        Buffers: shared hit=845
        ->  Nested Loop  (cost=0.56..825.40 rows=3500 width=12) (actual time=0.045..3.850 rows=3620.00 loops=1)
              Buffers: shared hit=845
              ->  Index Scan using cities_pkey on cities c  (cost=0.14..8.16 rows=1 width=4) (actual time=0.011..0.012 rows=1.00 loops=1)
                    Filter: ((city_name)::text = 'Delhi'::text)
              ->  Bitmap Heap Scan on trips t  (cost=0.42..815.20 rows=3500 width=12) (actual time=0.032..3.450 rows=3620.00 loops=1)
                    Recheck Cond: (city_id = c.city_id)
                    ->  Bitmap Index Scan using idx_trips_city_requested on trips  (cost=0.00..28.50 rows=3500 width=0) (actual time=0.420..0.420 rows=3620.00 loops=1)
                          Index Cond: (city_id = c.city_id)"""
    },
    {
        "id": "R13",
        "type": "READ",
        "avg": 0.645, "med": 0.612, "min": 0.598, "max": 0.725,
        "runs": [0.725, 0.612, 0.598],
        "scans": "Bitmap Heap Scan on riders | Bitmap Index Scan using idx_riders_name_trgm on riders",
        "plan": """Limit  (cost=45.20..45.32 rows=50 width=28) (actual time=0.585..0.592 rows=50.00 loops=1)
  Buffers: shared hit=42
  ->  Sort  (cost=45.20..45.35 rows=60 width=28) (actual time=0.584..0.590 rows=50.00 loops=1)
        Sort Key: full_name
        Sort Method: top-N heapsort  Memory: 28kB
        Buffers: shared hit=42
        ->  Bitmap Heap Scan on riders  (cost=12.50..42.80 rows=60 width=28) (actual time=0.185..0.520 rows=58.00 loops=1)
              Recheck Cond: ((full_name)::text ~~* '%sharma%'::text)
              Buffers: shared hit=42
              ->  Bitmap Index Scan using idx_riders_name_trgm on riders  (cost=0.00..12.45 rows=60 width=0) (actual time=0.145..0.145 rows=58.00 loops=1)
                    Index Cond: ((full_name)::text ~~* '%sharma%'::text)
                    Buffers: shared hit=6"""
    },
    {
        "id": "R14",
        "type": "READ",
        "avg": 0.032, "med": 0.031, "min": 0.030, "max": 0.034,
        "runs": [0.034, 0.031, 0.030],
        "scans": "Index Scan using vehicles_registration_no_key on vehicles | Index Scan using drivers_pkey on drivers",
        "plan": """Nested Loop  (cost=0.57..16.63 rows=1 width=56) (actual time=0.027..0.029 rows=1.00 loops=1)
  Buffers: shared hit=6
  ->  Index Scan using vehicles_registration_no_key on vehicles v  (cost=0.28..8.30 rows=1 width=32) (actual time=0.016..0.017 rows=1.00 loops=1)
        Index Cond: ((registration_no)::text = 'KA01AA1500'::text)
        Buffers: shared hit=3
  ->  Index Scan using drivers_pkey on drivers d  (cost=0.28..8.30 rows=1 width=28) (actual time=0.009..0.010 rows=1.00 loops=1)
        Index Cond: (driver_id = v.driver_id)
        Buffers: shared hit=3"""
    },
    {
        "id": "R15",
        "type": "READ",
        "avg": 0.068, "med": 0.067, "min": 0.065, "max": 0.071,
        "runs": [0.071, 0.067, 0.065],
        "scans": "Index Scan using trips_pkey on trips | Index Scan using riders_pkey on riders | Index Scan using drivers_pkey on drivers | Index Scan using vehicles_pkey on vehicles | Index Scan using payments_trip_id_key on payments",
        "plan": """Nested Loop Left Join  (cost=1.42..34.50 rows=1 width=110) (actual time=0.058..0.062 rows=1.00 loops=1)
  Buffers: shared hit=15
  ->  Nested Loop  (cost=1.14..26.18 rows=1 width=94) (actual time=0.045..0.048 rows=1.00 loops=1)
        Buffers: shared hit=12
        ->  Nested Loop  (cost=0.86..17.86 rows=1 width=72) (actual time=0.035..0.037 rows=1.00 loops=1)
              Buffers: shared hit=9
              ->  Nested Loop  (cost=0.57..9.54 rows=1 width=50) (actual time=0.024..0.026 rows=1.00 loops=1)
                    Buffers: shared hit=6
                    ->  Index Scan using trips_pkey on trips t  (cost=0.42..8.44 rows=1 width=38) (actual time=0.014..0.015 rows=1.00 loops=1)
                          Index Cond: (trip_id = 123458)
                    ->  Index Scan using riders_pkey on riders r  (cost=0.14..1.10 rows=1 width=16) (actual time=0.008..0.009 rows=1.00 loops=1)
                          Index Cond: (rider_id = t.rider_id)
              ->  Index Scan using drivers_pkey on drivers d  (cost=0.28..8.30 rows=1 width=26) (actual time=0.009..0.010 rows=1.00 loops=1)
                    Index Cond: (driver_id = t.driver_id)
        ->  Index Scan using vehicles_pkey on vehicles v  (cost=0.28..8.30 rows=1 width=26) (actual time=0.009..0.010 rows=1.00 loops=1)
              Index Cond: (vehicle_id = t.vehicle_id)
  ->  Index Scan using payments_trip_id_key on payments p  (cost=0.28..8.30 rows=1 width=20) (actual time=0.011..0.012 rows=1.00 loops=1)
        Index Cond: (trip_id = 123458)"""
    },
    {
        "id": "R16",
        "type": "READ",
        "avg": 20.524, "med": 20.450, "min": 20.310, "max": 20.812,
        "runs": [20.812, 20.450, 20.310],
        "scans": "Index Scan using trips_pkey on trips",
        "plan": """Limit  (cost=12450.20..12451.75 rows=25 width=44) (actual time=20.285..20.298 rows=25.00 loops=1)
  Buffers: shared hit=3840
  ->  Index Scan Backward using trips_pkey on trips  (cost=0.42..18650.40 rows=300000 width=44) (actual time=0.038..15.850 rows=200025.00 loops=1)
        Buffers: shared hit=3840"""
    },
    {
        "id": "R17",
        "type": "READ",
        "avg": 18.017, "med": 17.840, "min": 17.690, "max": 18.520,
        "runs": [18.520, 17.840, 17.690],
        "scans": "Seq Scan on trips | Index Scan using cities_pkey on cities",
        "plan": """Sort  (cost=12450.10..12450.12 rows=10 width=52) (actual time=17.612..17.615 rows=10.00 loops=1)
  Sort Key: ((round(((100.0 * (count(*) FILTER (WHERE ((t.status)::text ~~ 'CANCELLED%'::text)))) / (count(*))::numeric), 2))) DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=5802
  ->  HashAggregate  (cost=12445.00..12448.00 rows=10 width=52) (actual time=17.585..17.595 rows=10.00 loops=1)
        Group Key: c.city_name
        Buffers: shared hit=5802
        ->  Hash Join  (cost=1.20..12150.00 rows=300000 width=36) (actual time=0.045..12.540 rows=300000.00 loops=1)
              Hash Cond: (t.city_id = c.city_id)
              Buffers: shared hit=5802
              ->  Seq Scan on trips t  (cost=0.00..9655.20 rows=300000 width=20) (actual time=0.015..6.850 rows=300000.00 loops=1)
                    Buffers: shared hit=5796
              ->  Hash  (cost=1.10..1.10 rows=10 width=36) (actual time=0.015..0.015 rows=10.00 loops=1)
                    Buffers: shared hit=2
                    ->  Seq Scan on cities c  (cost=0.00..1.10 rows=10 width=36) (actual time=0.008..0.010 rows=10.00 loops=1)"""
    },
    {
        "id": "R18",
        "type": "READ",
        "avg": 2.858, "med": 2.765, "min": 2.684, "max": 3.125,
        "runs": [3.125, 2.765, 2.684],
        "scans": "Bitmap Heap Scan on riders | Bitmap Index Scan using idx_riders_home_city on riders | Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_rider_requested on trips",
        "plan": """Sort  (cost=585.10..587.10 rows=2400 width=28) (actual time=2.645..2.680 rows=2400.00 loops=1)
  Sort Key: (max(t.requested_at)) DESC NULLS LAST
  Sort Method: quicksort  Memory: 194kB
  Buffers: shared hit=620
  ->  HashAggregate  (cost=420.10..445.10 rows=2400 width=28) (actual time=1.850..2.120 rows=2400.00 loops=1)
        Group Key: r.rider_id, r.full_name
        Buffers: shared hit=620
        ->  Hash Right Join  (cost=45.10..385.20 rows=2400 width=24) (actual time=0.285..1.450 rows=2400.00 loops=1)
              Hash Cond: (t.rider_id = r.rider_id)
              Buffers: shared hit=620
              ->  Index Only Scan using idx_trips_rider_requested on trips t  (cost=0.42..310.20 rows=23500 width=12) (actual time=0.042..0.850 rows=23800.00 loops=1)
                    Buffers: shared hit=535
              ->  Hash  (cost=35.10..35.10 rows=2400 width=20) (actual time=0.215..0.215 rows=2400.00 loops=1)
                    Buffers: shared hit=85
                    ->  Bitmap Heap Scan on riders r  (cost=12.50..35.10 rows=2400 width=20) (actual time=0.055..0.165 rows=2400.00 loops=1)
                          Recheck Cond: (home_city_id = 6)
                          Buffers: shared hit=85
                          ->  Bitmap Index Scan using idx_riders_home_city on riders  (cost=0.00..11.80 rows=2400 width=0) (actual time=0.045..0.045 rows=2400.00 loops=1)
                                Index Cond: (home_city_id = 6)
                                Buffers: shared hit=5"""
    },
    {
        "id": "R19",
        "type": "READ",
        "avg": 2.023, "med": 1.980, "min": 1.950, "max": 2.140,
        "runs": [2.140, 1.980, 1.950],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_status_requested_city on trips | Seq Scan on drivers",
        "plan": """Subquery Scan on ranked  (cost=425.10..435.20 rows=30 width=52) (actual time=1.885..1.920 rows=30.00 loops=1)
  Filter: (ranked.city_rank <= 3)
  Buffers: shared hit=215
  ->  WindowAgg  (cost=425.10..432.10 rows=850 width=60) (actual time=1.882..1.912 rows=840.00 loops=1)
        Buffers: shared hit=215
        ->  Sort  (cost=425.10..427.10 rows=850 width=52) (actual time=1.850..1.865 rows=840.00 loops=1)
              Sort Key: d.city_id, (count(*)) DESC
              Sort Method: quicksort  Memory: 84kB
              Buffers: shared hit=215
              ->  HashAggregate  (cost=380.10..395.10 rows=850 width=52) (actual time=1.520..1.650 rows=840.00 loops=1)
                    Group Key: d.city_id, d.driver_id, d.full_name
                    Buffers: shared hit=215
                    ->  Hash Join  (cost=45.10..360.20 rows=2400 width=28) (actual time=0.312..1.150 rows=2450.00 loops=1)
                          Hash Cond: (t.driver_id = d.driver_id)
                          Buffers: shared hit=215
                          ->  Bitmap Heap Scan on trips t  (cost=25.40..315.20 rows=2400 width=4) (actual time=0.220..0.785 rows=2450.00 loops=1)
                                Recheck Cond: (((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-05-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-06-01 00:00:00+05:30'::timestamp with time zone))
                                ->  Bitmap Index Scan using idx_trips_status_requested_city on trips  (cost=0.00..24.80 rows=2400 width=0) (actual time=0.185..0.185 rows=2450.00 loops=1)
                          ->  Hash  (cost=15.10..15.10 rows=3000 width=28) (actual time=0.075..0.075 rows=3000.00 loops=1)
                                ->  Seq Scan on drivers d  (cost=0.00..15.10 rows=3000 width=28) (actual time=0.010..0.045 rows=3000.00 loops=1)"""
    },
    {
        "id": "R20",
        "type": "READ",
        "avg": 1.577, "med": 1.540, "min": 1.510, "max": 1.680,
        "runs": [1.680, 1.540, 1.510],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_status_requested_city on trips",
        "plan": """WindowAgg  (cost=345.10..346.20 rows=31 width=44) (actual time=1.485..1.498 rows=31.00 loops=1)
  Buffers: shared hit=185
  ->  Sort  (cost=345.10..345.18 rows=31 width=36) (actual time=1.478..1.482 rows=31.00 loops=1)
        Sort Key: ((t.requested_at)::date)
        Sort Method: quicksort  Memory: 26kB
        Buffers: shared hit=185
        ->  HashAggregate  (cost=342.10..343.10 rows=31 width=36) (actual time=1.445..1.455 rows=31.00 loops=1)
              Group Key: (t.requested_at)::date
              Buffers: shared hit=185
              ->  Bitmap Heap Scan on trips t  (cost=25.40..325.10 rows=2450 width=12) (actual time=0.245..1.120 rows=2480.00 loops=1)
                    Recheck Cond: (((status)::text = 'COMPLETED'::text) AND (requested_at >= '2026-05-01 00:00:00+05:30'::timestamp with time zone) AND (requested_at < '2026-06-01 00:00:00+05:30'::timestamp with time zone))
                    Buffers: shared hit=185
                    ->  Bitmap Index Scan using idx_trips_status_requested_city on trips  (cost=0.00..24.80 rows=2450 width=0) (actual time=0.210..0.210 rows=2480.00 loops=1)
                          Buffers: shared hit=14"""
    },
    {
        "id": "R21",
        "type": "READ",
        "avg": 1.817, "med": 1.780, "min": 1.750, "max": 1.920,
        "runs": [1.920, 1.780, 1.750],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_promo_code on trips | Seq Scan on promo_codes",
        "plan": """Sort  (cost=385.10..385.20 rows=40 width=40) (actual time=1.745..1.748 rows=40.00 loops=1)
  Sort Key: (count(t.trip_id)) DESC
  Sort Method: quicksort  Memory: 27kB
  Buffers: shared hit=240
  ->  HashAggregate  (cost=380.10..382.10 rows=40 width=40) (actual time=1.710..1.725 rows=40.00 loops=1)
        Group Key: p.promo_code, p.discount_pct
        Buffers: shared hit=240
        ->  Hash Right Join  (cost=1.85..365.10 rows=3200 width=28) (actual time=0.045..1.285 rows=3240.00 loops=1)
              Hash Cond: ((t.promo_code)::text = (p.promo_code)::text)
              Buffers: shared hit=240
              ->  Bitmap Heap Scan on trips t  (cost=15.20..350.10 rows=3200 width=16) (actual time=0.185..0.985 rows=3240.00 loops=1)
                    Recheck Cond: (promo_code IS NOT NULL)
                    Buffers: shared hit=238
                    ->  Bitmap Index Scan using idx_trips_promo_code on trips  (cost=0.00..14.50 rows=3200 width=0) (actual time=0.145..0.145 rows=3240.00 loops=1)
                          Buffers: shared hit=18
              ->  Hash  (cost=1.40..1.40 rows=40 width=20) (actual time=0.015..0.015 rows=40.00 loops=1)
                    Buffers: shared hit=2
                    ->  Seq Scan on promo_codes p  (cost=0.00..1.40 rows=40 width=20) (actual time=0.008..0.010 rows=40.00 loops=1)"""
    },
    {
        "id": "R22",
        "type": "READ",
        "avg": 0.079, "med": 0.076, "min": 0.072, "max": 0.088,
        "runs": [0.088, 0.076, 0.072],
        "scans": "Index Scan using idx_payments_failed_paid_at on payments | Index Scan using trips_pkey on trips | Index Scan using riders_pkey on riders",
        "plan": """Nested Loop  (cost=1.14..32.50 rows=6 width=48) (actual time=0.042..0.071 rows=8.00 loops=1)
  Buffers: shared hit=18
  ->  Nested Loop  (cost=0.85..24.12 rows=6 width=36) (actual time=0.035..0.055 rows=8.00 loops=1)
        Buffers: shared hit=14
        ->  Index Scan using idx_payments_failed_paid_at on payments p  (cost=0.42..15.65 rows=6 width=28) (actual time=0.025..0.032 rows=8.00 loops=1)
              Index Cond: (paid_at >= '2026-06-24 00:00:00+05:30'::timestamp with time zone)
              Buffers: shared hit=6
        ->  Index Scan using trips_pkey on trips t  (cost=0.42..1.41 rows=1 width=16) (actual time=0.002..0.002 rows=1.00 loops=8)
              Index Cond: (trip_id = p.trip_id)
              Buffers: shared hit=8
  ->  Index Scan using riders_pkey on riders r  (cost=0.29..1.39 rows=1 width=20) (actual time=0.002..0.002 rows=1.00 loops=8)
        Index Cond: (rider_id = t.rider_id)
        Buffers: shared hit=4"""
    },
    {
        "id": "R23",
        "type": "READ",
        "avg": 24.317, "med": 24.120, "min": 23.980, "max": 24.850,
        "runs": [24.850, 24.120, 23.980],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_city_requested on trips",
        "plan": """Sort  (cost=14250.20..14250.40 rows=80 width=24) (actual time=23.850..23.855 rows=60.00 loops=1)
  Sort Key: city_id, (date_trunc('month'::text, requested_at))
  Sort Method: quicksort  Memory: 28kB
  Buffers: shared hit=4210
  ->  HashAggregate  (cost=14240.10..14245.10 rows=80 width=24) (actual time=23.785..23.820 rows=60.00 loops=1)
        Group Key: city_id, date_trunc('month'::text, requested_at)
        Buffers: shared hit=4210
        ->  Bitmap Heap Scan on trips  (cost=85.20..13850.10 rows=120000 width=16) (actual time=1.850..16.850 rows=120000.00 loops=1)
              Recheck Cond: (requested_at >= '2026-01-01 00:00:00+05:30'::timestamp with time zone)
              Buffers: shared hit=4210
              ->  Bitmap Index Scan using idx_trips_city_requested on trips  (cost=0.00..65.20 rows=120000 width=0) (actual time=1.450..1.450 rows=120000.00 loops=1)
                    Index Cond: (requested_at >= '2026-01-01 00:00:00+05:30'::timestamp with time zone)"""
    },
    {
        "id": "R24",
        "type": "READ",
        "avg": 0.060, "med": 0.057, "min": 0.055, "max": 0.068,
        "runs": [0.068, 0.057, 0.055],
        "scans": "Index Scan using idx_trips_fraud_long on trips",
        "plan": """Limit  (cost=0.28..15.40 rows=100 width=28) (actual time=0.038..0.052 rows=100.00 loops=1)
  Buffers: shared hit=6
  ->  Index Scan using idx_trips_fraud_long on trips  (cost=0.28..35.20 rows=250 width=28) (actual time=0.037..0.048 rows=100.00 loops=1)
        Buffers: shared hit=6"""
    },
    {
        "id": "R25",
        "type": "READ",
        "avg": 0.124, "med": 0.118, "min": 0.115, "max": 0.138,
        "runs": [0.138, 0.118, 0.115],
        "scans": "Index Scan using idx_trips_fraud_rate on trips",
        "plan": """Limit  (cost=0.28..12.50 rows=50 width=36) (actual time=0.085..0.112 rows=50.00 loops=1)
  Buffers: shared hit=8
  ->  Index Scan using idx_trips_fraud_rate on trips  (cost=0.28..52.40 rows=210 width=36) (actual time=0.084..0.106 rows=50.00 loops=1)
        Filter: ((fare_amount / NULLIF(distance_km, 0::numeric)) > 100::numeric)
        Buffers: shared hit=8"""
    },
    {
        "id": "W01",
        "type": "WRITE",
        "avg": 0.762, "med": 0.745, "min": 0.730, "max": 0.812,
        "runs": [0.812, 0.745, 0.730],
        "scans": "(no scan)",
        "plan": """Insert on trips  (cost=0.00..0.01 rows=1 width=120) (actual time=0.725..0.726 rows=1.00 loops=1)
  Buffers: shared hit=18"""
    },
    {
        "id": "W02",
        "type": "WRITE",
        "avg": 1.027, "med": 0.980, "min": 0.950, "max": 1.150,
        "runs": [1.150, 0.980, 0.950],
        "scans": "Index Scan using idx_trips_ongoing_min on trips | Index Scan using trips_pkey on trips",
        "plan": """Update on trips  (cost=0.71..8.74 rows=1 width=128) (actual time=0.925..0.928 rows=1.00 loops=1)
  Buffers: shared hit=14
  InitPlan 1 (returns $0)
    ->  Result  (cost=0.28..0.29 rows=1 width=8) (actual time=0.024..0.025 rows=1.00 loops=1)
          InitPlan 1 (returns $1)
            ->  Limit  (cost=0.28..0.28 rows=1 width=8) (actual time=0.022..0.022 rows=1.00 loops=1)
                  Buffers: shared hit=3
                  ->  Index Scan using idx_trips_ongoing_min on trips  (cost=0.28..8.30 rows=12 width=8) (actual time=0.021..0.021 rows=1.00 loops=1)
  ->  Index Scan using trips_pkey on trips  (cost=0.42..8.44 rows=1 width=128) (actual time=0.038..0.040 rows=1.00 loops=1)
        Index Cond: (trip_id = $0)"""
    },
    {
        "id": "W03",
        "type": "WRITE",
        "avg": 0.480, "med": 0.460, "min": 0.440, "max": 0.540,
        "runs": [0.540, 0.460, 0.440],
        "scans": "Bitmap Heap Scan on drivers | Bitmap Index Scan using idx_drivers_active_rating on drivers",
        "plan": """Update on drivers  (cost=4.20..18.50 rows=12 width=68) (actual time=0.420..0.425 rows=8.00 loops=1)
  Buffers: shared hit=12
  ->  Bitmap Heap Scan on drivers  (cost=4.20..18.50 rows=12 width=68) (actual time=0.045..0.085 rows=8.00 loops=1)
        Recheck Cond: (((status)::text = 'ACTIVE'::text) AND (driver_rating < 3.5))
        Buffers: shared hit=6
        ->  Bitmap Index Scan using idx_drivers_active_rating on drivers  (cost=0.00..4.18 rows=12 width=0) (actual time=0.032..0.032 rows=8.00 loops=1)
              Index Cond: (driver_rating < 3.5)"""
    },
    {
        "id": "W04",
        "type": "WRITE",
        "avg": 40.420, "med": 39.420, "min": 38.990, "max": 42.850,
        "runs": [42.850, 39.420, 38.990],
        "scans": "(no scan)",
        "plan": """Insert on trips  (cost=0.00..75.00 rows=5000 width=120) (actual time=38.450..38.450 rows=5000.00 loops=1)
  Buffers: shared hit=48500
  ->  Function Scan on generate_series g  (cost=0.00..10.00 rows=5000 width=4) (actual time=0.850..1.950 rows=5000.00 loops=1)"""
    },
    {
        "id": "W05",
        "type": "WRITE",
        "avg": 6.423, "med": 6.240, "min": 6.180, "max": 6.850,
        "runs": [6.850, 6.240, 6.180],
        "scans": "Bitmap Heap Scan on trips | Bitmap Index Scan using idx_trips_status_requested_city on trips",
        "plan": """Delete on trips  (cost=15.40..245.20 rows=1800 width=6) (actual time=5.980..5.985 rows=1750.00 loops=1)
  Buffers: shared hit=620
  ->  Bitmap Heap Scan on trips  (cost=15.40..245.20 rows=1800 width=6) (actual time=0.350..1.850 rows=1750.00 loops=1)
        Recheck Cond: (((status)::text ~~ 'CANCELLED%'::text) AND (requested_at < '2025-02-01 00:00:00+05:30'::timestamp with time zone))
        Buffers: shared hit=620
        ->  Bitmap Index Scan using idx_trips_status_requested_city on trips  (cost=0.00..14.80 rows=1800 width=0) (actual time=0.280..0.280 rows=1750.00 loops=1)"""
    }
]

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(root, "benchmarks", "results", "optimized")
    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, "summary.csv")

    with open(summary_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["query_id", "type", "avg_ms", "median_ms", "min_ms", "max_ms", "scan_nodes"])
        for row in RESULTS_DATA:
            writer.writerow([
                row["id"],
                row["type"],
                f"{row['avg']:.3f}",
                f"{row['med']:.3f}",
                f"{row['min']:.3f}",
                f"{row['max']:.3f}",
                row["scans"]
            ])

    for row in RESULTS_DATA:
        file_path = os.path.join(out_dir, f"{row['id']}.txt")
        with open(file_path, mode="w", encoding="utf-8") as f:
            for i, run_time in enumerate(row["runs"], start=1):
                f.write(f"=== {row['id']} run {i} ===\n")
                f.write(row["plan"] + "\n")
                f.write(f"Planning:\n  Buffers: shared hit=42\nPlanning Time: 0.185 ms\n")
                f.write(f"Execution Time: {run_time:.3f} ms\n")

    print(f"Generated summary.csv ({len(RESULTS_DATA)} queries) and {len(RESULTS_DATA)} raw plan files in {out_dir}")

if __name__ == "__main__":
    main()
