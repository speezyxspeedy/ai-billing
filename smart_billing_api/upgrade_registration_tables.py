import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS shops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    dob TEXT,
    mobile TEXT,
    email TEXT UNIQUE,
    password TEXT NOT NULL,
    business_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("PRAGMA table_info(shops)")
columns = [row[1] for row in cursor.fetchall()]
if 'dob' not in columns:
    cursor.execute("ALTER TABLE shops ADD COLUMN dob TEXT")

cursor.execute("""
CREATE TABLE IF NOT EXISTS shop_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id INTEGER NOT NULL,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    FOREIGN KEY (shop_id) REFERENCES shops(id)
)
""")

conn.commit()
conn.close()

print("Registration tables created successfully.")