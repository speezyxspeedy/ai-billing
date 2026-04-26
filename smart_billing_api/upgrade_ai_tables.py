import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

# Alias memory
cursor.execute("""
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_name TEXT UNIQUE,
    product_name TEXT
)
""")

# Usage memory / recommendation
cursor.execute("""
CREATE TABLE IF NOT EXISTS usage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT UNIQUE,
    used_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Price history / prediction
cursor.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT,
    price REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Existing products ka current price history me daal do
cursor.execute("SELECT item_name, price FROM products")
rows = cursor.fetchall()

for item_name, price in rows:
    cursor.execute("""
        INSERT INTO price_history (item_name, price)
        SELECT ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM price_history
            WHERE item_name = ? AND price = ?
        )
    """, (item_name, price, item_name, price))

conn.commit()
conn.close()

print("AI tables added successfully.")