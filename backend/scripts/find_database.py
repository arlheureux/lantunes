#!/usr/bin/env python3
"""Debug script to find database location."""
import os
import sys

# Check multiple possible locations
possible_paths = [
    "/root/lantunes/lantunes.db",
    "/root/lantunes/backend/lantunes.db",
    os.path.expanduser("~/lantunes/lantunes.db"),
    os.path.join(os.getcwd(), "lantunes.db"),
]

print("Searching for database...")
print(f"Current working directory: {os.getcwd()}")

for path in possible_paths:
    exists = os.path.exists(path)
    print(f"  {path}: {'EXISTS' if exists else 'not found'}")

# Also check for any .db files
print("\nAll .db files found:")
for root, dirs, files in os.walk("/root/lantunes"):
    for f in files:
        if f.endswith('.db'):
            full = os.path.join(root, f)
            size = os.path.getsize(full)
            print(f"  {full} ({size} bytes)")

# Try to read schema from found databases
for path in possible_paths:
    if os.path.exists(path):
        print(f"\nChecking tables in {path}:")
        import sqlite3
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  Tables: {tables}")
        conn.close()
