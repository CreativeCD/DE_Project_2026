#!/usr/bin/env python3
"""
Validation script for Checkpoint 2 (CP2 - Baseline Timings)
Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
"""
import os
import sys
import re
import csv

def validate():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "benchmarks", "results", "baseline")
    summary_path = os.path.join(results_dir, "summary.csv")
    doc_path = os.path.join(root, "docs", "03_baseline_timings.md")
    viva_path = os.path.join(root, "docs", "CP2_VIVA_PREPARATION.md")
    
    print("=" * 65)
    print("CP2 (BASELINE TIMINGS) DELIVERABLES VALIDATION CHECKLIST")
    print("=" * 65)
    
    all_passed = True
    
    # 1. Check summary.csv
    if not os.path.isfile(summary_path):
        print("❌ FAIL: summary.csv missing at benchmarks/results/baseline/summary.csv")
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

    # 2. Check 30 raw plan files and 3 runs per query
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
        print("✅ PASS: All 30 raw plan files exist in benchmarks/results/baseline/.")
    else:
        print(f"❌ FAIL: Missing raw plan files for: {missing_files}")
        all_passed = False
        
    if not invalid_runs:
        print("✅ PASS: Every query has exactly 3 recorded benchmark executions.")
    else:
        print(f"❌ FAIL: Queries with incorrect execution counts: {invalid_runs}")
        all_passed = False

    # 3. Check docs/03_baseline_timings.md
    if os.path.isfile(doc_path):
        with open(doc_path, mode="r", encoding="utf-8") as f:
            doc_content = f.read()
        missing_in_doc = [qid for qid in expected_ids if qid not in doc_content]
        if not missing_in_doc:
            print("✅ PASS: docs/03_baseline_timings.md exists and covers all 30 queries.")
        else:
            print(f"❌ FAIL: docs/03_baseline_timings.md is missing queries: {missing_in_doc}")
            all_passed = False
    else:
        print("❌ FAIL: docs/03_baseline_timings.md does not exist.")
        all_passed = False

    # 4. Check docs/CP2_VIVA_PREPARATION.md
    if os.path.isfile(viva_path):
        size = os.path.getsize(viva_path)
        if size > 5000:
            print(f"✅ PASS: docs/CP2_VIVA_PREPARATION.md exists ({size} bytes).")
        else:
            print(f"❌ FAIL: docs/CP2_VIVA_PREPARATION.md too small ({size} bytes).")
            all_passed = False
    else:
        print("❌ FAIL: docs/CP2_VIVA_PREPARATION.md does not exist.")
        all_passed = False

    print("=" * 65)
    if all_passed:
        print("🎉 ALL CHECKPOINT 2 REQUIREMENTS VERIFIED AND PASSED!")
    else:
        print("⚠️ SOME CHECKS FAILED. PLEASE REVIEW ABOVE LOGS.")
    print("=" * 65)
    return all_passed

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
