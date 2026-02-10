"""
Migration: Add applicability fields to control_points table.

New columns:
  - section        VARCHAR(100)
  - compliance_criteria  TEXT
  - applies_to     VARCHAR(50) DEFAULT 'all'
  - is_applicable  BOOLEAN DEFAULT 1
  - applicability_reason VARCHAR(255)

Usage:
  python migrate_add_applicability.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join('instance', 'qms_local.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    print("Make sure you run this from the FruitQMS project root.")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(control_points)")
existing_cols = {row[1] for row in cursor.fetchall()}

migrations = [
    ("section", "ALTER TABLE control_points ADD COLUMN section VARCHAR(100)"),
    ("compliance_criteria", "ALTER TABLE control_points ADD COLUMN compliance_criteria TEXT"),
    ("applies_to", "ALTER TABLE control_points ADD COLUMN applies_to VARCHAR(50) DEFAULT 'all'"),
    ("is_applicable", "ALTER TABLE control_points ADD COLUMN is_applicable BOOLEAN DEFAULT 1"),
    ("applicability_reason", "ALTER TABLE control_points ADD COLUMN applicability_reason VARCHAR(255)"),
]

applied = 0
for col_name, sql in migrations:
    if col_name in existing_cols:
        print(f"  [skip] Column '{col_name}' already exists.")
    else:
        cursor.execute(sql)
        print(f"  [added] Column '{col_name}'")
        applied += 1

conn.commit()
conn.close()

print(f"\nDone. {applied} column(s) added, {len(migrations) - applied} skipped (already exist).")
