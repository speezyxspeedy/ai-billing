import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

print("\n=== BILLS TABLE ===")
cursor.execute("SELECT * FROM bills")
bills = cursor.fetchall()

if not bills:
    print("No bills found")
else:
    for row in bills:
        print(row)

print("\n=== BILL ITEMS TABLE ===")
cursor.execute("SELECT * FROM bill_items")
items = cursor.fetchall()

if not items:
    print("No bill items found")
else:
    for row in items:
        print(row)

conn.close()
import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

print("\n=== BILLS TABLE ===")
cursor.execute("SELECT * FROM bills")
for row in cursor.fetchall():
    print(row)

print("\n=== BILL ITEMS TABLE ===")
cursor.execute("SELECT * FROM bill_items")
for row in cursor.fetchall():
    print(row)

print("\n=== USAGE HISTORY TABLE ===")
cursor.execute("SELECT * FROM usage_history")
for row in cursor.fetchall():
    print(row)

print("\n=== PRICE HISTORY TABLE ===")
cursor.execute("SELECT * FROM price_history")
for row in cursor.fetchall():
    print(row)

conn.close()