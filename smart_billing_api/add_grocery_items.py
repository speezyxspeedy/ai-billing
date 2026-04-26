import sqlite3

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

# List of grocery items to add
grocery_items = [
    ("Bread 400g", 30.0, 5.0, "local"),
    ("Eggs 12pcs", 60.0, 5.0, "local"),
    ("Butter 100g", 45.0, 12.0, "local"),
    ("Cheese 200g", 80.0, 12.0, "local"),
    ("Chicken 1kg", 200.0, 5.0, "local"),
    ("Fish 500g", 150.0, 5.0, "local"),
    ("Potatoes 1kg", 40.0, 5.0, "local"),
    ("Onions 1kg", 50.0, 5.0, "local"),
    ("Tomatoes 1kg", 60.0, 5.0, "local"),
    ("Apples 1kg", 120.0, 5.0, "local"),
    ("Bananas 1kg", 50.0, 5.0, "local"),
    ("Flour 1kg", 40.0, 5.0, "local"),
    ("Salt 1kg", 20.0, 5.0, "local"),
    ("Turmeric 100g", 25.0, 5.0, "local"),
    ("Chili Powder 100g", 30.0, 5.0, "local"),
    ("Biscuits 200g", 25.0, 18.0, "local"),
    ("Chocolates 100g", 50.0, 18.0, "local"),
    ("Soft Drink 2L", 80.0, 18.0, "local"),
    ("Detergent 1kg", 150.0, 18.0, "local"),
    ("Soap Bar", 30.0, 18.0, "local"),
    ("Shampoo 200ml", 120.0, 18.0, "local"),
    ("Toothpaste 150g", 85.0, 18.0, "local"),
    ("Cooking Oil 1L", 140.0, 5.0, "local"),  # Already have Oil 1L, but different name
    ("Milk Powder 500g", 180.0, 5.0, "local"),
    ("Coffee Powder 200g", 150.0, 18.0, "local"),
    ("Tea Bags 100pcs", 120.0, 18.0, "local"),
    ("Sugar 5kg", 225.0, 5.0, "local"),
    ("Rice 25kg", 1125.0, 5.0, "local"),
    ("Wheat Flour 5kg", 200.0, 5.0, "local"),
    ("Lentils 1kg", 100.0, 5.0, "local"),
    ("Chickpeas 1kg", 80.0, 5.0, "local"),
    ("Peanuts 500g", 70.0, 5.0, "local"),
    ("Cashews 200g", 250.0, 5.0, "local"),
    ("Almonds 200g", 300.0, 5.0, "local"),
    ("Raisins 200g", 120.0, 5.0, "local"),
    ("Honey 500g", 200.0, 5.0, "local"),
    ("Jam 500g", 150.0, 18.0, "local"),
    ("Pickles 500g", 100.0, 18.0, "local"),
    ("Noodles 200g", 35.0, 18.0, "local"),
    ("Pasta 500g", 60.0, 18.0, "local"),
    ("Cereal 500g", 180.0, 18.0, "local"),
    ("Cornflakes 500g", 160.0, 18.0, "local"),
    ("Baby Food 400g", 250.0, 18.0, "local"),
    ("Diapers Pack", 400.0, 18.0, "local"),
    ("Sanitary Napkins", 120.0, 18.0, "local"),
    ("Shaving Cream", 95.0, 18.0, "local"),
    ("Deodorant", 150.0, 18.0, "local"),
    ("Laundry Detergent 2kg", 280.0, 18.0, "local"),
    ("Dish Soap 750ml", 85.0, 18.0, "local"),
    ("Floor Cleaner 1L", 120.0, 18.0, "local"),
    ("Air Freshener", 80.0, 18.0, "local"),
    ("Batteries AA 4pcs", 60.0, 18.0, "local"),
]

added_count = 0
skipped_count = 0

for item in grocery_items:
    try:
        cursor.execute(
            "INSERT INTO products (item_name, price, gst, source) VALUES (?, ?, ?, ?)",
            item
        )
        added_count += 1
        print(f"Added: {item[0]}")
    except sqlite3.IntegrityError:
        skipped_count += 1
        print(f"Skipped (already exists): {item[0]}")

conn.commit()
conn.close()

print(f"\nSummary: Added {added_count} items, Skipped {skipped_count} items")