import sqlite3

conn = sqlite3.connect('billing.db')
c = conn.cursor()

# Add category column if it doesn't exist
try:
    c.execute('ALTER TABLE products ADD COLUMN category TEXT DEFAULT "Other"')
    print('Category column added successfully')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('Category column already exists')
    else:
        print(f'Error adding column: {e}')

# Define category mappings based on keywords
categories = {
    'Fruits': ['apple', 'banana', 'orange', 'mango', 'grapes', 'pineapple', 'watermelon', 'papaya', 'guava', 'pomegranate', 'kiwi', 'strawberry', 'blueberry', 'cherry', 'peach', 'pear', 'plum', 'apricot', 'fig', 'date', 'lemon', 'lime', 'coconut', 'dragon fruit', 'passion fruit', 'avocado', 'custard apple', 'jackfruit'],
    'Vegetables': ['potato', 'onion', 'tomato', 'carrot', 'cabbage', 'cauliflower', 'brinjal', 'lady finger', 'bitter gourd', 'bottle gourd', 'ridge gourd', 'drumstick', 'beans', 'peas', 'spinach', 'fenugreek', 'coriander', 'curry leaves', 'green chilli', 'garlic', 'ginger', 'radish', 'beetroot', 'cucumber', 'capsicum', 'broccoli', 'lettuce', 'mushroom', 'corn', 'sweet potato'],
    'Grains & Pulses': ['rice', 'wheat flour', 'maida', 'suji', 'besan', 'urad dal', 'moong dal', 'chana dal', 'toor dal', 'masoor dal', 'rajma', 'chickpeas', 'kidney beans', 'black gram', 'horse gram', 'green gram', 'pigeon peas', 'lentils', 'split peas', 'soybean'],
    'Spices': ['turmeric', 'red chilli powder', 'coriander powder', 'cumin powder', 'garam masala', 'chicken masala', 'meat masala', 'sambar powder', 'rasam powder', 'biryani masala', 'chana masala', 'pav bhaji masala', 'cardamom', 'cinnamon', 'cloves', 'bay leaves', 'star anise', 'nutmeg', 'mace', 'saffron', 'black pepper', 'white pepper', 'mustard seeds', 'fenugreek seeds', 'cumin seeds', 'fennel seeds'],
    'Dairy': ['milk', 'curd', 'butter', 'ghee', 'cheese', 'paneer', 'cream', 'yogurt', 'lassi', 'buttermilk', 'condensed milk', 'milk powder', 'cheese slices', 'cheese cubes', 'mozzarella', 'cheddar', 'parmesan'],
    'Meat & Seafood': ['chicken', 'mutton', 'beef', 'pork', 'fish', 'prawns', 'crab', 'squid', 'octopus', 'salmon', 'tuna', 'sardine', 'mackerel', 'pomfret', 'rohu', 'catla', 'hilsa', 'basa', 'tilapia'],
    'Bakery': ['bread', 'brown bread', 'multigrain bread', 'white bread', 'baguette', 'croissant', 'muffin', 'cake', 'pastry', 'cookie', 'biscuit', 'pav', 'bun', 'pizza base', 'naan', 'roti', 'paratha'],
    'Snacks': ['chips', 'namkeen', 'bhujia', 'khakra', 'mathri', 'papad', 'murukku', 'sev', 'wafer', 'chocolates', 'candy', 'toffee', 'lollipop', 'chewing gum'],
    'Beverages': ['tea', 'coffee', 'green tea', 'herbal tea', 'soft drink', 'juice', 'energy drink', 'soda', 'mineral water', 'coconut water', 'fruit drink', 'milk shake'],
    'Personal Care': ['soap', 'shampoo', 'conditioner', 'body wash', 'face wash', 'toothpaste', 'toothbrush', 'mouthwash', 'deodorant', 'perfume', 'talcum powder', 'face powder', 'lipstick', 'nail polish', 'shaving cream', 'after shave', 'hair oil', 'hair gel', 'sunscreen', 'moisturizer', 'face cream', 'body lotion'],
    'Household': ['detergent', 'dish wash', 'floor cleaner', 'toilet cleaner', 'glass cleaner', 'air freshener', 'insect repellent', 'mosquito coil', 'room spray', 'fabric softener', 'bleach', 'disinfectant', 'washing powder', 'liquid detergent', 'hand wash', 'sanitizer'],
    'Baby Care': ['baby soap', 'baby shampoo', 'baby lotion', 'baby oil', 'baby powder', 'baby cream', 'diapers', 'baby wipes', 'feeding bottle', 'pacifier', 'baby food', 'cerelac', 'baby cereal'],
    'Dry Fruits': ['almonds', 'cashews', 'walnuts', 'pistachios', 'raisins', 'dates', 'apricots', 'figs', 'prunes', 'peanuts', 'groundnuts', 'sunflower seeds', 'pumpkin seeds', 'flax seeds', 'chia seeds'],
    'Oils & Ghee': ['sunflower oil', 'groundnut oil', 'coconut oil', 'mustard oil', 'olive oil', 'palm oil', 'rice bran oil', 'sesame oil', 'vanaspati', 'margarine'],
    'Sweets': ['sugar', 'jaggery', 'honey', 'jam', 'marmalade', 'pickle', 'chutney', 'murabba', 'halwa', 'laddoo', 'barfi', 'rasgulla', 'gulab jamun', 'jalebi', 'ras malai', 'kheer'],
    'Frozen Foods': ['frozen peas', 'frozen corn', 'frozen mixed vegetables', 'frozen chicken', 'frozen fish', 'frozen prawns', 'ice cream', 'frozen yogurt', 'frozen paratha', 'frozen pizza', 'frozen fries'],
    'Canned Foods': ['canned tuna', 'canned sardine', 'canned peas', 'canned corn', 'canned beans', 'canned soup', 'canned fruit', 'canned juice', 'pickled vegetables', 'canned meat', 'canned fish']
}

# Get all products
c.execute('SELECT id, item_name FROM products')
products = c.fetchall()

updated = 0
for product_id, item_name in products:
    item_lower = item_name.lower()
    assigned_category = 'Other'

    for category, keywords in categories.items():
        if any(keyword in item_lower for keyword in keywords):
            assigned_category = category
            break

    c.execute('UPDATE products SET category = ? WHERE id = ?', (assigned_category, product_id))
    updated += 1

conn.commit()
conn.close()
print(f'Updated {updated} products with categories')