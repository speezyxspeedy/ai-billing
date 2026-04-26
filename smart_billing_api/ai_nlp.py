import re

def parse_billing_text(text: str):
    text = text.strip().lower()
    parts = re.split(r",|\n", text)
    results = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        match = re.match(r"(\d+)\s+(.+)", part)
        if match:
            qty = int(match.group(1))
            item_name = match.group(2).strip()
        else:
            qty = 1
            item_name = part

        results.append({
            "item_name": item_name,
            "quantity": qty
        })

    return results