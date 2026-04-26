from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3


from ai_nlp import parse_billing_text
from ai_matcher import best_match
from ai_memory import get_alias, save_alias
from ai_price_predictor import predict_price
from fastapi.middleware.cors import CORSMiddleware


print("REGISTER VERSION LOADED")
print("LOADING CLEAN BILLING API")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "billing.db"


def get_conn():
    return sqlite3.connect(DB_NAME, timeout=10)


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


@app.get("/")
def home():
    return {"message": "Smart Billing AI API Running"}


@app.get("/products")
def get_products():
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, item_name, price, gst, source FROM products")
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "item_name": row[1],
                "price": row[2],
                "gst": row[3],
                "source": row[4]
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
        cursor.execute("""
            INSERT INTO shops
            (shop_name, owner_name, mobile, email, password, business_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.shop_name,
            data.owner_name,
            data.mobile,
            data.email,
            data.password,
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
            SELECT id, shop_name, owner_name, email, business_type
            FROM shops
            WHERE email = ? AND password = ?
        """, (data.email, data.password))

        shop = cursor.fetchone()

        if not shop:
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