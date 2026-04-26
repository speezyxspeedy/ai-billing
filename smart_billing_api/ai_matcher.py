from difflib import get_close_matches

def normalize(text: str):
    return text.strip().lower()

def best_match(user_text: str, product_names: list[str]):
    if not product_names:
        return None

    user_text = normalize(user_text)
    normalized_map = {normalize(name): name for name in product_names}
    normalized_names = list(normalized_map.keys())

    for name in normalized_names:
        if user_text in name or name in user_text:
            return normalized_map[name]

    matches = get_close_matches(user_text, normalized_names, n=1, cutoff=0.5)
    if matches:
        return normalized_map[matches[0]]

    return None