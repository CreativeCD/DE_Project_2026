#!/usr/bin/env python3
"""
Validation script for Checkpoint 3 (CP3 - Optimization)
Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
Author: Rusheel Chandra (Member 4)
"""
import os
import sys
import re
import csv

def validate():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "benchmarks", "results", "optimized")
    summary_path = os.path.join(results_dir, "summary.csv")
    doc_path = os.path.join(root, "docs", "04_optimization_report.md")
    indexes_sql_path = os.path.join(root, "sql", "05_indexes.sql")
    opt_queries_path = os.path.join(root, "sql", "06_optimized_queries.sql")
    
    print("=" * 65)
    print("CP3 (OPTIMIZATION) DELIVERABLES VALIDATION CHECKLIST")
    print("=" * 65)
    
    all_passed = True
    
    # 1. Check sql/05_indexes.sql
    if not os.path.isfile(indexes_sql_path):
        print("❌ FAIL: sql/05_indexes.sql is missing.")
        all_passed = False
    else:
        with open(indexes_sql_path, "r", encoding="utf-8") as f:
            idx_content = f.read()
        idx_count = len(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX", idx_content, re.IGNORECASE))
        if idx_count >= 10:
            print(f"✅ PASS: sql/05_indexes.sql exists with {idx_count} indexes.")
        else:
            print(f"⚠️ WARNING: sql/05_indexes.sql has only {idx_count} indexes.")

    # 2. Check sql/06_optimized_queries.sql
    if not os.path.isfile(opt_queries_path):
        print("❌ FAIL: sql/06_optimized_queries.sql is missing.")
        all_passed = False
    else:
        with open(opt_queries_path, "r", encoding="utf-8") as f:
            q_content = f.read()
        markers = re.findall(r"^--\s*@(R\d+|W\d+)\s*$", q_content, re.MULTILINE)
        if len(markers) == 30:
            print(f"✅ PASS: sql/06_optimized_queries.sql has all 30 markers (R01-W05).")
        else:
            print(f"❌ FAIL: sql/06_optimized_queries.sql has {len(markers)} markers, expected 30.")
            all_passed = False

    # 3. Check summary.csv
    if not os.path.isfile(summary_path):
        print("❌ FAIL: summary.csv missing at benchmarks/results/optimized/summary.csv")
        all_passed = False
    else:
        with open(summary_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if len(rows) == 30:
            print(f"✅ PASS: summary.csv exists and contains exactly 30 query rows.")
        else:
            print(f"❌ FAIL: summary.csv has {len(rows)} rows, expected 30.")
            all_passed = False

    # 4. Check 30 raw plan files and 3 runs per query
    expected_ids = [f"R{i:02d}" for i in range(1, 26)] + [f"W{i:02d}" for i in range(1, 6)]
    missing_files = []
    invalid_runs = []
    
    for qid in expected_ids:
        raw_file = os.path.join(results_dir, f"{qid}.txt")
        if not os.path.isfile(raw_file):
            missing_files.append(qid)
            continue
        with open(raw_file, mode="r", encoding="utf-8") as f:
            content = f.read()
        runs = re.findall(r"Execution Time:\s+([0-9.]+)\s+ms", content)
        if len(runs) != 3:
            invalid_runs.append((qid, len(runs)))
            
    if not missing_files:
        print("✅ PASS: All 30 raw plan files exist in benchmarks/results/optimized/.")
    else:
        print(f"❌ FAIL: Missing raw plan files for: {missing_files}")
        all_passed = False
        
    if not invalid_runs:
        print("✅ PASS: All 30 raw plan files contain exactly 3 benchmark runs.")
    else:
        print(f"❌ FAIL: Incorrect run counts for: {invalid_runs}")
        all_passed = False

    # 5. Check docs/04_optimization_report.md
    if not os.path.isfile(doc_path):
        print("⏳ PENDING: docs/04_optimization_report.md not yet created.")
    else:
        with open(doc_path, mode="r", encoding="utf-8") as f:
            doc_content = f.read()
        all_ids_in_doc = all(qid in doc_content for qid in expected_ids)
        if all_ids_in_doc:
            print("✅ PASS: docs/04_optimization_report.md exists and documents all 30 queries.")
        else:
            print("⚠️ WARNING: docs/04_optimization_report.md is missing documentation for some queries.")

    print("=" * 65)
    return all_passed

if __name__ == "__main__":
    passed = validate()
    sys.exit(0 if passed else 1)
