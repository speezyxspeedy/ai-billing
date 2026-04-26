import sqlite3
from difflib import get_close_matches

DB_NAME = "billing.db"

def get_conn():
    return sqlite3.connect(DB_NAME, timeout=10)

def normalize(text: str):
    return text.strip().lower()

def predict_price(item_name: str):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT price FROM products
        WHERE lower(item_name) = lower(?)
    """, (item_name,))
    row = cursor.fetchone()

    if row:
        conn.close()
        return {
            "item_name": item_name,
            "predicted_price": row[0],
            "method": "exact_product_price"
        }

    cursor.execute("SELECT item_name, price FROM products")
    rows = cursor.fetchall()

    normalized_map = {normalize(r[0]): r for r in rows}
    close = get_close_matches(normalize(item_name), list(normalized_map.keys()), n=3, cutoff=0.4)

    if close:
        matched_prices = [normalized_map[name][1] for name in close]
        avg_price = round(sum(matched_prices) / len(matched_prices), 2)
        matched_items = [normalized_map[name][0] for name in close]
        conn.close()
        return {
            "item_name": item_name,
            "predicted_price": avg_price,
            "method": "similar_items_average",
            "matched_items": matched_items
        }

    cursor.execute("SELECT AVG(price) FROM price_history")
    avg_row = cursor.fetchone()
    avg_price = round(avg_row[0], 2) if avg_row and avg_row[0] else 50.0

    conn.close()
    return {
        "item_name": item_name,
        "predicted_price": avg_price,
        "method": "global_average_fallback"
    }