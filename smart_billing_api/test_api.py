import requests

r = requests.get('http://127.0.0.1:8001/products')
data = r.json()
print(f'Total products: {len(data)}')
if data:
    print('Sample products with categories:')
    for i, p in enumerate(data[:5]):
        print(f'  {p["item_name"]} - {p["category"]}')