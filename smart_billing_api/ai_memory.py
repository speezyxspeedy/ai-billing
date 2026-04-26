import sqlite3

DB_NAME = "billing.db"

def get_conn():
    return sqlite3.connect(DB_NAME, timeout=10)

def save_alias(alias_name, product_name):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO aliases (alias_name, product_name)
    VALUES (?, ?)
    """, (alias_name.lower(), product_name))

    conn.commit()
    conn.close()

def get_alias(alias_name):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT product_name FROM aliases WHERE alias_name = ?
    """, (alias_name.lower(),))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def update_usage(product_name):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT used_count FROM usage_history WHERE product_name = ?
    """, (product_name,))
    row = cursor.fetchone()

    if row:
        cursor.execute("""
        UPDATE usage_history
        SET used_count = used_count + 1,
            last_used = CURRENT_TIMESTAMP
        WHERE product_name = ?
        """, (product_name,))
    else:
        cursor.execute("""
        INSERT INTO usage_history (product_name, used_count)
        VALUES (?, 1)
        """, (product_name,))

    conn.commit()
    conn.close()