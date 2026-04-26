print("LOADING BILLING API")
print("REGISTER ROUTE VERSION")


import os
import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import bcrypt

from ai_nlp import parse_billing_text
from ai_matcher import best_match
from ai_memory import get_alias, save_alias
from ai_price_predictor import predict_price


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend files from same server
@app.get("/")
def serve_index():
    return FileResponse("ai_billing.html")

@app.get("/style.css")
def serve_css():
    return FileResponse("style.css")

@app.get("/script.js")
def serve_js():
    return FileResponse("script.js")

@app.get("/health")
def health_check():
    return {"status": "ok"}

DB_NAME = "billing.db"


def get_conn():
    return sqlite3.connect(DB_NAME, timeout=10)


def init_db():
    conn = get_conn()
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

    cursor.execute("PRAGMA table_info(products)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'category' not in cols:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT DEFAULT 'Other'")

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            price REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE,
            used_count INTEGER DEFAULT 0,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alias_name TEXT UNIQUE,
            product_name TEXT
        )
    """)

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shop_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            config_key TEXT NOT NULL,
            config_value TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("Sugar 1kg", 45, 5, "local", "Sweets"),
            ("Rice 5kg", 320, 5, "local", "Grains & Pulses"),
            ("Oil 1L", 140, 5, "local", "Oils & Ghee"),
            ("Tea 500g", 210, 5, "local", "Beverages")
        ]
        for p in defaults:
            cursor.execute(
                "INSERT OR IGNORE INTO products (item_name, price, gst, source, category) VALUES (?, ?, ?, ?, ?)",
                p
            )

    conn.commit()
    conn.close()


init_db()


class Product(BaseModel):
    item_name: str
    price: float
    gst: float
    source: str = "local"


class BillItem(BaseModel):
    item_name: str
    quantity: int
    price: float
    gst: float


class BillRequest(BaseModel):
    items: list[BillItem]



@app.get("/products")
def get_products():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, item_name, price, gst, source, category FROM products ORDER BY category, item_name")
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "item_name": row[1],
                "price": row[2],
                "gst": row[3],
                "source": row[4],
                "category": row[5]
            }
            for row in rows
        ]
    finally:
        conn.close()


@app.post("/products")
def add_product(product: Product):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (item_name, price, gst, source)
            VALUES (?, ?, ?, ?)
        """, (product.item_name, product.price, product.gst, product.source))

        cursor.execute("""
            INSERT INTO price_history (item_name, price)
            VALUES (?, ?)
        """, (product.item_name, product.price))

        conn.commit()
        return {"message": "Product added successfully"}

    except sqlite3.IntegrityError:
        return {"message": "Product already exists"}

    except Exception as e:
        return {"message": f"Error adding product: {str(e)}"}

    finally:
        conn.close()

# ...existing code...

@app.post("/bill")
def create_bill(bill: BillRequest):
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        grand_total = 0
        for item in bill.items:
            subtotal = item.price * item.quantity
            gst_amount = subtotal * item.gst / 100
            final = subtotal + gst_amount
            grand_total += final
        
        cursor.execute("INSERT INTO bills (grand_total) VALUES (?)", (grand_total,))
        bill_id = cursor.lastrowid
        
        for item in bill.items:
            subtotal = item.price * item.quantity
            gst_amount = subtotal * item.gst / 100
            final = subtotal + gst_amount
            
            cursor.execute("""
                INSERT INTO bill_items (bill_id, item_name, quantity, price, gst, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (bill_id, item.item_name, item.quantity, item.price, item.gst, final))
            
            cursor.execute("""
                INSERT INTO price_history (item_name, price)
                VALUES (?, ?)
            """, (item.item_name, item.price))
            
            # Update usage history
            cursor.execute("""
                SELECT used_count FROM usage_history
                WHERE product_name = ?
            """, (item.item_name,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("""
                    UPDATE usage_history
                    SET used_count = used_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE product_name = ?
                """, (item.item_name,))
            else:
                cursor.execute("""
                    INSERT INTO usage_history (product_name, used_count)
                    VALUES (?, 1)
                """, (item.item_name,))
        
        conn.commit()
        return {
            "message": "Bill saved successfully",
            "bill_id": bill_id,
            "grand_total": grand_total
        }
    except Exception as e:
        conn.rollback()
        return {"message": f"Error saving bill: {str(e)}"}
    finally:
        conn.close()


@app.get("/bills")
def get_bills():
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, bill_date, grand_total
            FROM bills
            ORDER BY bill_date DESC
        """)
        bill_rows = cursor.fetchall()
        
        bills = []
        for bill_row in bill_rows:
            bill_id, bill_date, total = bill_row
            
            cursor.execute("""
                SELECT item_name, quantity, price, gst, line_total
                FROM bill_items
                WHERE bill_id = ?
                ORDER BY item_name
            """, (bill_id,))
            item_rows = cursor.fetchall()
            
            items = []
            for item_row in item_rows:
                items.append({
                    "item_name": item_row[0],
                    "quantity": item_row[1],
                    "price": item_row[2],
                    "gst": item_row[3],
                    "line_total": item_row[4]
                })
            
            bills.append({
                "bill_id": bill_id,
                "created_at": bill_date,
                "item_count": len(items),
                "total": total,
                "items": items
            })
        
        return bills
    
    except Exception as e:
        return {"message": f"Error fetching bills: {str(e)}"}
    
    finally:
        conn.close()


@app.get("/reports")
def get_reports():
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # Today's revenue
        cursor.execute("""
            SELECT SUM(grand_total)
            FROM bills
            WHERE DATE(bill_date) = DATE('now')
        """)
        today_revenue = cursor.fetchone()[0] or 0
        
        # Bills this month
        cursor.execute("""
            SELECT COUNT(*)
            FROM bills
            WHERE strftime('%Y-%m', bill_date) = strftime('%Y-%m', 'now')
        """)
        month_bills = cursor.fetchone()[0]
        
        # Avg bill value this month
        cursor.execute("""
            SELECT AVG(grand_total)
            FROM bills
            WHERE strftime('%Y-%m', bill_date) = strftime('%Y-%m', 'now')
        """)
        avg_bill_value = cursor.fetchone()[0] or 0
        
        # Top item this month
        cursor.execute("""
            SELECT item_name, SUM(quantity) as total_qty
            FROM bill_items bi
            JOIN bills b ON bi.bill_id = b.id
            WHERE strftime('%Y-%m', b.bill_date) = strftime('%Y-%m', 'now')
            GROUP BY item_name
            ORDER BY total_qty DESC
            LIMIT 1
        """)
        top_item_row = cursor.fetchone()
        top_item = top_item_row[0] if top_item_row else "—"
        
        return {
            "today_revenue": today_revenue,
            "month_bills": month_bills,
            "avg_bill_value": avg_bill_value,
            "top_item": top_item
        }
    
    except Exception as e:
        return {"message": f"Error generating reports: {str(e)}"}
    
    finally:
        conn.close()

# ...existing code...

@app.post("/ai/parse-bill")
def ai_parse_bill(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        text = payload.get("text", "").strip()

        if not text:
            return {"items": [], "message": "No text provided"}

        parsed_items = parse_billing_text(text)

        cursor.execute("SELECT item_name FROM products")
        rows = cursor.fetchall()
        product_names = [row[0] for row in rows]

        final_items = []

        for entry in parsed_items:
            user_item = entry["item_name"]
            qty = entry["quantity"]

            cursor.execute("""
                SELECT product_name
                FROM aliases
                WHERE alias_name = ?
            """, (user_item.lower(),))
            alias_row = cursor.fetchone()

            if alias_row:
                matched_item = alias_row[0]
            else:
                matched_item = best_match(user_item, product_names)
                if matched_item:
                    cursor.execute("""
                        INSERT OR REPLACE INTO aliases (alias_name, product_name)
                        VALUES (?, ?)
                    """, (user_item.lower(), matched_item))

            final_items.append({
                "input_item": user_item,
                "matched_item": matched_item,
                "quantity": qty
            })

        conn.commit()
        return {"items": final_items}

    except Exception as e:
        conn.rollback()
        return {"message": f"AI parse error: {str(e)}"}

    finally:
        conn.close()


@app.get("/ai/predict-price")
def ai_predict_price(item_name: str):
    try:
        return predict_price(item_name)
    except Exception as e:
        return {"message": f"Price prediction error: {str(e)}"}
@app.post("/ai/auto-bill")
def ai_auto_bill(payload: dict):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        text = payload.get("text", "").strip()

        if not text:
            return {"message": "No input text"}

        parsed_items = parse_billing_text(text)

        cursor.execute("SELECT item_name, price, gst FROM products")
        rows = cursor.fetchall()

        product_map = {
            row[0]: {"price": row[1], "gst": row[2]}
            for row in rows
        }
        product_names = list(product_map.keys())

        final_items = []
        grand_total = 0

        for entry in parsed_items:
            user_item = entry["item_name"]
            qty = entry["quantity"]

            cursor.execute("""
                SELECT product_name
                FROM aliases
                WHERE alias_name = ?
            """, (user_item.lower(),))
            alias_row = cursor.fetchone()

            if alias_row:
                matched_item = alias_row[0]
            else:
                matched_item = best_match(user_item, product_names)
                if matched_item:
                    cursor.execute("""
                        INSERT OR REPLACE INTO aliases (alias_name, product_name)
                        VALUES (?, ?)
                    """, (user_item.lower(), matched_item))

            if not matched_item:
                continue

            price = product_map[matched_item]["price"]
            gst = product_map[matched_item]["gst"]

            subtotal = price * qty
            gst_amount = subtotal * gst / 100
            final = subtotal + gst_amount
            grand_total += final

            final_items.append({
                "item_name": matched_item,
                "quantity": qty,
                "price": price,
                "gst": gst,
                "line_total": final
            })

            cursor.execute("""
                SELECT used_count
                FROM usage_history
                WHERE product_name = ?
            """, (matched_item,))
            usage_row = cursor.fetchone()

            if usage_row:
                cursor.execute("""
                    UPDATE usage_history
                    SET used_count = used_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    WHERE product_name = ?
                """, (matched_item,))
            else:
                cursor.execute("""
                    INSERT INTO usage_history (product_name, used_count)
                    VALUES (?, 1)
                """, (matched_item,))

            cursor.execute("""
                INSERT INTO price_history (item_name, price)
                VALUES (?, ?)
            """, (matched_item, price))

        if not final_items:
            return {
                "message": "No valid items matched",
                "items": []
            }

        cursor.execute("""
            INSERT INTO bills (grand_total)
            VALUES (?)
        """, (grand_total,))
        bill_id = cursor.lastrowid

        for item in final_items:
            cursor.execute("""
                INSERT INTO bill_items
                (bill_id, item_name, quantity, price, gst, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                bill_id,
                item["item_name"],
                item["quantity"],
                item["price"],
                item["gst"],
                item["line_total"]
            ))

        conn.commit()

        return {
            "message": "AI Bill created",
            "bill_id": bill_id,
            "grand_total": grand_total,
            "items": final_items
        }

    except Exception as e:
        conn.rollback()
        return {"message": f"API error: {str(e)}"}

    finally:
        conn.close()


class ShopRegisterRequest(BaseModel):
    shop_name: str
    owner_name: str
    dob: str | None = None
    mobile: str | None = None
    email: str
    password: str
    business_type: str
    modules: list[str] = []
    ai_enabled: bool = True
    inventory_enabled: bool = True


class ShopLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/register")
def register_shop(data: ShopRegisterRequest):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO shops
            (shop_name, owner_name, dob, mobile, email, password, business_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.shop_name,
            data.owner_name,
            data.dob,
            data.mobile,
            data.email,
            hashed_pw,
            data.business_type
        ))

        shop_id = cursor.lastrowid

        configs = {
            "business_type": data.business_type,
            "ai_enabled": str(data.ai_enabled).lower(),
            "inventory_enabled": str(data.inventory_enabled).lower(),
            "modules": ",".join(data.modules)
        }

        if data.business_type == "grocery":
            configs["pricing_mode"] = "flexible"
            configs["expiry_tracking"] = "false"
            configs["batch_tracking"] = "false"
            configs["weight_based"] = "false"

        elif data.business_type == "medical":
            configs["pricing_mode"] = "mrp"
            configs["expiry_tracking"] = "true"
            configs["batch_tracking"] = "true"
            configs["weight_based"] = "false"

        elif data.business_type == "gold":
            configs["pricing_mode"] = "live_rate"
            configs["expiry_tracking"] = "false"
            configs["batch_tracking"] = "false"
            configs["weight_based"] = "true"
            configs["making_charges"] = "true"
            configs["purity_tracking"] = "true"

        else:
            configs["pricing_mode"] = "flexible"
            configs["expiry_tracking"] = "false"
            configs["batch_tracking"] = "false"
            configs["weight_based"] = "false"

        for key, value in configs.items():
            cursor.execute("""
                INSERT INTO shop_config (shop_id, config_key, config_value)
                VALUES (?, ?, ?)
            """, (shop_id, key, value))

        conn.commit()

        return {
            "message": "Shop registered successfully",
            "shop_id": shop_id,
            "shop_name": data.shop_name,
            "business_type": data.business_type
        }

    except sqlite3.IntegrityError:
        conn.rollback()
        return {"message": "Email already registered"}

    except Exception as e:
        conn.rollback()
        return {"message": f"Registration error: {str(e)}"}

    finally:
        conn.close()


@app.post("/login")
def login_shop(data: ShopLoginRequest):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, shop_name, owner_name, email, business_type, password
            FROM shops
            WHERE email = ?
        """, (data.email,))

        shop = cursor.fetchone()

        if not shop or not bcrypt.checkpw(data.password.encode(), shop[5].encode()):
            return {"message": "Invalid email or password"}

        shop_id = shop[0]

        cursor.execute("""
            SELECT config_key, config_value
            FROM shop_config
            WHERE shop_id = ?
        """, (shop_id,))
        config_rows = cursor.fetchall()

        config = {row[0]: row[1] for row in config_rows}

        return {
            "message": "Login successful",
            "shop": {
                "id": shop[0],
                "shop_name": shop[1],
                "owner_name": shop[2],
                "email": shop[3],
                "business_type": shop[4]
            },
            "config": config
        }

    except Exception as e:
        return {"message": f"Login error: {str(e)}"}

    finally:
        conn.close()


@app.get("/shop-config/{shop_id}")
def get_shop_config(shop_id: int):
    conn = get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, shop_name, owner_name, email, business_type
            FROM shops
            WHERE id = ?
        """, (shop_id,))
        shop = cursor.fetchone()

        if not shop:
            return {"message": "Shop not found"}

        cursor.execute("""
            SELECT config_key, config_value
            FROM shop_config
            WHERE shop_id = ?
        """, (shop_id,))
        config_rows = cursor.fetchall()

        config = {row[0]: row[1] for row in config_rows}

        return {
            "shop": {
                "id": shop[0],
                "shop_name": shop[1],
                "owner_name": shop[2],
                "email": shop[3],
                "business_type": shop[4]
            },
            "config": config
        }

    except Exception as e:
        return {"message": f"Config fetch error: {str(e)}"}

    finally:
        conn.close()
        # ===== REGISTER TEST =====
@app.post("/register-test")
def register_test():
    return {"message": "register test working"}


if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
