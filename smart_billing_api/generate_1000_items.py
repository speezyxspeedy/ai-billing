import sqlite3
import random

conn = sqlite3.connect("billing.db")
cursor = conn.cursor()

# GST rates
GST_RATES = {
    'essentials': 5.0,    # Food staples, vegetables, fruits
    'processed': 12.0,    # Dairy, meat, processed foods
    'luxury': 18.0        # Snacks, beverages, personal care, household
}

# Base items and their categories
CATEGORIES = {
    'fruits': {
        'items': ['Apple', 'Banana', 'Orange', 'Mango', 'Grapes', 'Pineapple', 'Watermelon', 'Papaya', 'Guava', 'Pomegranate',
                 'Kiwi', 'Strawberry', 'Blueberry', 'Cherry', 'Peach', 'Pear', 'Plum', 'Apricot', 'Fig', 'Date',
                 'Lemon', 'Lime', 'Coconut', 'Dragon Fruit', 'Passion Fruit', 'Avocado', 'Custard Apple', 'Jackfruit'],
        'gst': 'essentials',
        'weights': ['250g', '500g', '1kg', '2kg']
    },
    'vegetables': {
        'items': ['Potato', 'Onion', 'Tomato', 'Carrot', 'Cabbage', 'Cauliflower', 'Brinjal', 'Lady Finger', 'Bitter Gourd',
                 'Bottle Gourd', 'Ridge Gourd', 'Drumstick', 'Beans', 'Peas', 'Spinach', 'Fenugreek', 'Coriander',
                 'Curry Leaves', 'Green Chilli', 'Garlic', 'Ginger', 'Radish', 'Beetroot', 'Cucumber', 'Capsicum',
                 'Broccoli', 'Lettuce', 'Mushroom', 'Corn', 'Sweet Potato'],
        'gst': 'essentials',
        'weights': ['250g', '500g', '1kg', '2kg']
    },
    'grains_pulses': {
        'items': ['Rice', 'Wheat Flour', 'Maida', 'Suji', 'Besan', 'Urad Dal', 'Moong Dal', 'Chana Dal', 'Toor Dal',
                 'Masoor Dal', 'Rajma', 'Chickpeas', 'Kidney Beans', 'Black Gram', 'Horse Gram', 'Green Gram',
                 'Pigeon Peas', 'Lentils', 'Split Peas', 'Soybean'],
        'gst': 'essentials',
        'weights': ['500g', '1kg', '2kg', '5kg', '10kg', '25kg']
    },
    'spices': {
        'items': ['Turmeric', 'Red Chilli Powder', 'Coriander Powder', 'Cumin Powder', 'Garam Masala', 'Chicken Masala',
                 'Meat Masala', 'Sambar Powder', 'Rasam Powder', 'Biryani Masala', 'Chana Masala', 'Pav Bhaji Masala',
                 'Cardamom', 'Cinnamon', 'Cloves', 'Bay Leaves', 'Star Anise', 'Nutmeg', 'Mace', 'Saffron',
                 'Black Pepper', 'White Pepper', 'Mustard Seeds', 'Fenugreek Seeds', 'Cumin Seeds', 'Fennel Seeds'],
        'gst': 'essentials',
        'weights': ['50g', '100g', '200g', '500g']
    },
    'dairy': {
        'items': ['Milk', 'Curd', 'Butter', 'Ghee', 'Cheese', 'Paneer', 'Cream', 'Yogurt', 'Lassi', 'Buttermilk',
                 'Condensed Milk', 'Milk Powder', 'Cheese Slices', 'Cheese Cubes', 'Mozzarella', 'Cheddar', 'Parmesan'],
        'gst': 'processed',
        'weights': ['100g', '200g', '500g', '1L', '500ml', '1kg']
    },
    'meat_seafood': {
        'items': ['Chicken', 'Mutton', 'Beef', 'Pork', 'Fish', 'Prawns', 'Crab', 'Squid', 'Octopus', 'Salmon',
                 'Tuna', 'Sardine', 'Mackerel', 'Pomfret', 'Rohu', 'Catla', 'Hilsa', 'Basa', 'Tilapia'],
        'gst': 'processed',
        'weights': ['250g', '500g', '1kg', '2kg']
    },
    'bakery': {
        'items': ['Bread', 'Brown Bread', 'Multigrain Bread', 'White Bread', 'Baguette', 'Croissant', 'Muffin',
                 'Cake', 'Pastry', 'Cookie', 'Biscuit', 'Pav', 'Bun', 'Pizza Base', 'Naan', 'Roti', 'Paratha'],
        'gst': 'processed',
        'weights': ['200g', '400g', '500g', '1kg', '6pcs', '12pcs']
    },
    'snacks': {
        'items': ['Chips', 'Namkeen', 'Bhujia', 'Khakra', 'Mathri', 'Khakra', 'Papad', 'Murukku', 'Sev', 'Khakra',
                 'Biscuits', 'Cookies', 'Cream Biscuits', 'Marie Biscuits', 'Glucose Biscuits', 'Digestive Biscuits',
                 'Wafer', 'Chocolates', 'Candy', 'Toffee', 'Lollipop', 'Chewing Gum'],
        'gst': 'luxury',
        'weights': ['50g', '100g', '150g', '200g', '250g', '500g']
    },
    'beverages': {
        'items': ['Tea', 'Coffee', 'Green Tea', 'Herbal Tea', 'Soft Drink', 'Juice', 'Energy Drink', 'Soda',
                 'Mineral Water', 'Coconut Water', 'Fruit Drink', 'Milk Shake', 'Lassi', 'Buttermilk'],
        'gst': 'luxury',
        'weights': ['100g', '200g', '250ml', '500ml', '1L', '2L', '5L']
    },
    'personal_care': {
        'items': ['Soap', 'Shampoo', 'Conditioner', 'Body Wash', 'Face Wash', 'Toothpaste', 'Toothbrush', 'Mouthwash',
                 'Deodorant', 'Perfume', 'Talcum Powder', 'Face Powder', 'Lipstick', 'Nail Polish', 'Shaving Cream',
                 'After Shave', 'Hair Oil', 'Hair Gel', 'Sunscreen', 'Moisturizer', 'Face Cream', 'Body Lotion'],
        'gst': 'luxury',
        'weights': ['50ml', '100ml', '150ml', '200ml', '300ml', '500ml', '1L']
    },
    'household': {
        'items': ['Detergent', 'Dish Wash', 'Floor Cleaner', 'Toilet Cleaner', 'Glass Cleaner', 'Air Freshener',
                 'Insect Repellent', 'Mosquito Coil', 'Room Spray', 'Fabric Softener', 'Bleach', 'Disinfectant',
                 'Washing Powder', 'Liquid Detergent', 'Dish Soap', 'Hand Wash', 'Sanitizer'],
        'gst': 'luxury',
        'weights': ['100ml', '200ml', '500ml', '1L', '2L', '5L', '1kg', '2kg']
    },
    'baby_care': {
        'items': ['Baby Soap', 'Baby Shampoo', 'Baby Lotion', 'Baby Oil', 'Baby Powder', 'Baby Cream', 'Diapers',
                 'Baby Wipes', 'Feeding Bottle', 'Pacifier', 'Baby Food', 'Cerelac', 'Baby Cereal', 'Milk Powder'],
        'gst': 'luxury',
        'weights': ['50ml', '100ml', '200ml', '400g', '500g', '1kg', '20pcs', '40pcs']
    },
    'dry_fruits': {
        'items': ['Almonds', 'Cashews', 'Walnuts', 'Pistachios', 'Raisins', 'Dates', 'Apricots', 'Figs', 'Prunes',
                 'Peanuts', 'Groundnuts', 'Sunflower Seeds', 'Pumpkin Seeds', 'Flax Seeds', 'Chia Seeds'],
        'gst': 'essentials',
        'weights': ['100g', '200g', '250g', '500g', '1kg']
    },
    'oils_ghee': {
        'items': ['Sunflower Oil', 'Groundnut Oil', 'Coconut Oil', 'Mustard Oil', 'Olive Oil', 'Palm Oil', 'Rice Bran Oil',
                 'Sesame Oil', 'Ghee', 'Vanaspati', 'Butter', 'Margarine'],
        'gst': 'essentials',
        'weights': ['500ml', '1L', '2L', '5L', '15L']
    },
    'sweets': {
        'items': ['Sugar', 'Jaggery', 'Honey', 'Jam', 'Marmalade', 'Pickle', 'Chutney', 'Murabba', 'Halwa', 'Laddoo',
                 'Barfi', 'Rasgulla', 'Gulab Jamun', 'Jalebi', 'Ras Malai', 'Kheer'],
        'gst': 'essentials',
        'weights': ['200g', '500g', '1kg', '2kg']
    },
    'frozen_foods': {
        'items': ['Frozen Peas', 'Frozen Corn', 'Frozen Mixed Vegetables', 'Frozen Chicken', 'Frozen Fish',
                 'Frozen Prawns', 'Ice Cream', 'Frozen Yogurt', 'Frozen Paratha', 'Frozen Pizza', 'Frozen Fries'],
        'gst': 'processed',
        'weights': ['200g', '500g', '1kg', '2L']
    },
    'canned_foods': {
        'items': ['Canned Tuna', 'Canned Sardine', 'Canned Peas', 'Canned Corn', 'Canned Beans', 'Canned Soup',
                 'Canned Fruit', 'Canned Juice', 'Pickled Vegetables', 'Canned Meat', 'Canned Fish'],
        'gst': 'processed',
        'weights': ['200g', '400g', '500g', '1kg']
    }
}

def generate_price(item_name, category, weight):
    """Generate realistic price based on item category and weight"""
    base_prices = {
        'fruits': {'250g': 20, '500g': 35, '1kg': 60, '2kg': 110},
        'vegetables': {'250g': 15, '500g': 25, '1kg': 40, '2kg': 70},
        'grains_pulses': {'500g': 25, '1kg': 45, '2kg': 85, '5kg': 200, '10kg': 380, '25kg': 900},
        'spices': {'50g': 15, '100g': 25, '200g': 45, '500g': 100},
        'dairy': {'100g': 20, '200g': 35, '500g': 80, '1L': 60, '500ml': 35, '1kg': 300},
        'meat_seafood': {'250g': 60, '500g': 110, '1kg': 200, '2kg': 380},
        'bakery': {'200g': 25, '400g': 45, '500g': 55, '1kg': 100, '6pcs': 30, '12pcs': 55},
        'snacks': {'50g': 10, '100g': 18, '150g': 25, '200g': 35, '250g': 40, '500g': 70},
        'beverages': {'100g': 50, '200g': 90, '250ml': 15, '500ml': 25, '1L': 45, '2L': 80, '5L': 180},
        'personal_care': {'50ml': 25, '100ml': 45, '150ml': 65, '200ml': 85, '300ml': 120, '500ml': 180, '1L': 250},
        'household': {'100ml': 30, '200ml': 50, '500ml': 100, '1L': 150, '2L': 280, '5L': 650, '1kg': 120, '2kg': 220},
        'baby_care': {'50ml': 35, '100ml': 60, '200ml': 100, '400g': 200, '500g': 250, '1kg': 450, '20pcs': 180, '40pcs': 320},
        'dry_fruits': {'100g': 80, '200g': 150, '250g': 180, '500g': 330, '1kg': 600},
        'oils_ghee': {'500ml': 70, '1L': 130, '2L': 240, '5L': 550, '15L': 1500},
        'sweets': {'200g': 40, '500g': 90, '1kg': 160, '2kg': 300},
        'frozen_foods': {'200g': 50, '500g': 100, '1kg': 180, '2L': 250},
        'canned_foods': {'200g': 45, '400g': 80, '500g': 100, '1kg': 180}
    }

    base_price = base_prices.get(category, {}).get(weight, 50)
    # Add some random variation (±20%)
    variation = random.uniform(0.8, 1.2)
    return round(base_price * variation, 2)

# Generate items
generated_items = []
target_count = 1000
items_per_category = target_count // len(CATEGORIES)

for category_name, category_data in CATEGORIES.items():
    items = category_data['items']
    weights = category_data['weights']
    gst_rate = GST_RATES[category_data['gst']]

    # Generate items for this category
    category_items = []
    for item in items:
        for weight in weights:
            item_name = f"{item} {weight}"
            price = generate_price(item, category_name, weight)
            category_items.append((item_name, price, gst_rate, "local"))

            if len(category_items) >= items_per_category:
                break
        if len(category_items) >= items_per_category:
            break

    generated_items.extend(category_items)

# Shuffle to mix categories
random.shuffle(generated_items)

# Take exactly 1000 items (or as close as possible)
generated_items = generated_items[:1000]

# Insert into database
added_count = 0
skipped_count = 0

for item in generated_items:
    try:
        cursor.execute(
            "INSERT INTO products (item_name, price, gst, source) VALUES (?, ?, ?, ?)",
            item
        )
        added_count += 1
    except sqlite3.IntegrityError:
        skipped_count += 1

conn.commit()
conn.close()

print(f"Added {added_count} new items, Skipped {skipped_count} duplicates")
print(f"Total items in database: {added_count + skipped_count}")