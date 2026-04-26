import sqlite3
import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT UNIQUE,
    price REAL,
    gst REAL,
    source TEXT DEFAULT 'local'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grand_total REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bill_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER,
    item_name TEXT,
    quantity INTEGER,
    price REAL,
    gst REAL,
    line_total REAL
)
""")

products = [
    ("Sugar 1kg", 45, 5, "local"),
    ("Rice 5kg", 320, 5, "local"),
    ("Oil 1L", 140, 5, "local"),
    ("Tea 500g", 210, 5, "local")
]

for p in products:
    try:
        cursor.execute(
            "INSERT INTO products (item_name, price, gst, source) VALUES (?, ?, ?, ?)",
            p
        )
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()

print("Database ready")

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT UNIQUE,
    price REAL,
    gst REAL,
    source TEXT DEFAULT 'local'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    grand_total REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bill_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER,
    item_name TEXT,
    quantity INTEGER,
    price REAL,
    gst REAL,
    line_total REAL
)
""")

products = [
    ("Sugar 1kg", 45, 5, "local"),
    ("Rice 5kg", 320, 5, "local"),
    ("Oil 1L", 140, 5, "local"),
    ("Tea 500g", 210, 5, "local")
]

for p in products:
    try:
        cursor.execute(
            "INSERT INTO products (item_name, price, gst, source) VALUES (?, ?, ?, ?)",
            p
        )
    except:
        pass

conn.commit()
conn.close()

print("Database ready")