#!/usr/bin/env python3
"""
Validation script for Checkpoint 4 (CP4 - Scalability & Final Submission)
Team: T0061 (PalmPay / Uber Ride-Hailing DBMS Project)
Author: Sri Sai Deekshit Thitla (Member 2)
"""
import os
import sys
import re
import csv

def validate():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "benchmarks", "results", "large")
    summary_path = os.path.join(results_dir, "summary.csv")
    doc_path = os.path.join(root, "docs", "05_scalability_report.md")
    viva_path = os.path.join(root, "docs", "CP4_VIVA_PREPARATION.md")
    part_sql_path = os.path.join(root, "sql", "08_partitioning.sql")
    
    print("=" * 70)
    print("CP4 (SCALABILITY & LARGE-SCALE BENCHMARK) VALIDATION CHECKLIST")
    print("=" * 70)
    
    all_passed = True
    
    # 1. Check sql/08_partitioning.sql
    if os.path.isfile(part_sql_path):
        size = os.path.getsize(part_sql_path)
        with open(part_sql_path, "r", encoding="utf-8") as f:
            content = f.read()
        has_range = "PARTITION BY RANGE" in content
        has_months = "trips_y2025m01" in content and "trips_y2026m12" in content
        if has_range and has_months:
            print(f"✅ PASS: sql/08_partitioning.sql exists ({size} bytes) with monthly RANGE partitions.")
        else:
            print("❌ FAIL: sql/08_partitioning.sql missing expected RANGE partition definitions.")
            all_passed = False
    else:
        print("❌ FAIL: sql/08_partitioning.sql does not exist.")
        all_passed = False

    # 2. Check benchmarks/results/large/summary.csv
    if not os.path.isfile(summary_path):
        print("❌ FAIL: summary.csv missing at benchmarks/results/large/summary.csv")
        all_passed = False
    else:
        with open(summary_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if len(rows) == 30:
            print(f"✅ PASS: benchmarks/results/large/summary.csv contains all 30 queries.")
        else:
            print(f"❌ FAIL: summary.csv has {len(rows)} rows, expected 30.")
            all_passed = False

    # 3. Check 30 raw plan files and 3 runs per query on large data
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
        print("✅ PASS: All 30 raw plan files exist in benchmarks/results/large/.")
    else:
        print(f"❌ FAIL: Missing raw plan files for: {missing_files}")
        all_passed = False
        
    if not invalid_runs:
        print("✅ PASS: Every query on large dataset has exactly 3 benchmark runs.")
    else:
        print(f"❌ FAIL: Queries with incorrect run counts: {invalid_runs}")
        all_passed = False

    # 4. Check SLA Targets on Large Dataset
    # Real-Time: R01-R05, R14-R16, W01, W02 < 5 ms
    # Interactive Ops: R13, R22, R24, R25, W03 < 250 ms
    # Analytics: R06-R12, R17-R21, R23 < 5000 ms
    # Batch writes: W04, W05 < 1000 ms
    sla_violations = []
    if os.path.isfile(summary_path):
        with open(summary_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = row["query_id"]
                avg = float(row["avg_ms"])
                if qid in ["R01", "R02", "R03", "R04", "R05", "R14", "R15", "R16", "W01", "W02"]:
                    if avg >= 5.0:
                        sla_violations.append((qid, avg, "< 5 ms"))
                elif qid in ["R13", "R22", "R24", "R25", "W03"]:
                    if avg >= 250.0:
                        sla_violations.append((qid, avg, "< 250 ms"))
                elif qid in ["W04", "W05"]:
                    if avg >= 1000.0:
                        sla_violations.append((qid, avg, "< 1000 ms"))
                else:
                    if avg >= 5000.0:
                        sla_violations.append((qid, avg, "< 5000 ms"))

        if not sla_violations:
            print("✅ PASS: 100% of the 30 workload queries meet their strict large-scale SLAs!")
        else:
            print(f"❌ FAIL: Queries violating SLAs: {sla_violations}")
            all_passed = False

    # 5. Check docs/05_scalability_report.md
    if os.path.isfile(doc_path):
        with open(doc_path, mode="r", encoding="utf-8") as f:
            doc_content = f.read()
        missing_in_doc = [qid for qid in expected_ids if qid not in doc_content]
        if not missing_in_doc and "Partitioning" in doc_content and "Growth" in doc_content:
            print("✅ PASS: docs/05_scalability_report.md exists, covers all 30 queries & architecture.")
        else:
            print(f"❌ FAIL: docs/05_scalability_report.md incomplete or missing queries: {missing_in_doc}")
            all_passed = False
    else:
        print("❌ FAIL: docs/05_scalability_report.md does not exist.")
        all_passed = False

    # 6. Check docs/CP4_VIVA_PREPARATION.md
    if os.path.isfile(viva_path):
        size = os.path.getsize(viva_path)
        if size > 3000:
            print(f"✅ PASS: docs/CP4_VIVA_PREPARATION.md exists ({size} bytes).")
        else:
            print(f"❌ FAIL: docs/CP4_VIVA_PREPARATION.md too small ({size} bytes).")
            all_passed = False
    else:
        print("❌ FAIL: docs/CP4_VIVA_PREPARATION.md does not exist.")
        all_passed = False

    print("=" * 70)
    if all_passed:
        print("🎉 ALL CHECKPOINT 4 (FINAL SUBMISSION) REQUIREMENTS VERIFIED AND PASSED!")
    else:
        print("⚠️ SOME CHECKS FAILED. PLEASE REVIEW LOGS ABOVE.")
    print("=" * 70)
    return all_passed

if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
