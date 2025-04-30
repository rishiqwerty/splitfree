from rapidfuzz import fuzz
from utils.gemini_api_call import generate_content

ICON_MAP = {
    "transport": ["uber", "taxi", "cab", "ola", "ride"],
    "flight": ["flight", "airport", "airfare"],
    "food": [
        "pizza",
        "food",
        "dinner",
        "lunch",
        "snack",
        "breakfast",
        "colddrink",
        "meal",
        "burger",
        "restaurant",
        "biryani",
        "cafe",
    ],
    "drinks": [
        "drink",
        "beverage",
        "alcohol",
        "beer",
        "whiskey",
        "juice",
        "wine",
        "coke",
        "pepsi",
        "soft drink",
        "cold drink",
        "soda",
        "juice",
        "water",
    ],
    "entertainment": ["entertainment", "movie", "cinema", "netflix", "hulu", "disney"],
    "rent": [
        "rent",
        "apartment",
        "flat",
        "lease",
        "cook",
        "cleaning",
        "maid",
        "housekeeping",
        "cleaner",
        "household",
    ],
    "groceries": [
        "grocery",
        "groceries",
        "supermarket",
        "shopping",
        "milk",
        "bread",
        "vegetable",
        "fruit",
        "meat",
        "egg",
        "fish",
        "chicken",
        "rice",
        "pasta",
        "cereal",
    ],
    "snacks": [
        "snack",
        "chips",
        "crisps",
        "popcorn",
        "biscuit",
        "cookie",
        "candy",
        "chocolate",
    ],
    "gym": ["gym", "fitness", "workout"],
    "cafe": ["cafe", "coffee", "tea"],
    "utilities": ["utilities", "electricity", "water", "internet"],
    "petrol": ["petrol", "gas", "fuel", "diesel"],
    "self-care": [
        "self-care",
        "spa",
        "massage",
        "salon",
        "haircut",
        "beauty",
        "nail",
        "facial",
    ],
    "shopping": [
        "shopping",
        "clothes",
        "clothing",
        "fashion",
        "accessories",
        "jewelry",
        "shoes",
        "footwear",
        "toothpaste",
        "toothbrush",
        "soap",
        "shampoo",
        "conditioner",
        "lotion",
        "cream",
    ],
    "party": [
        "party",
        "celebration",
        "event",
        "gathering",
        "get-together",
        "bash",
        "shindig",
    ],
    "vacation": ["vacation", "holiday", "trip", "travel", "tour"],
}

ICON_EMOJIS = {
    "transport": "🚖",
    "flight": "✈️",
    "food": "🍕",
    "entertainment": "🎥",
    "rent": "🏠",
    "default": "💸",
    "groceries": "🛒",
    "gym": "🏋️",
    "cafe": "☕",
    "utilities": "💡",
    "petrol": "⛽",
    "drinks": "🍺",
    "snacks": "🍿",
    "self-care": "💆‍♀️",
    "shopping": "🛍️",
    "party": "🎉",
    "vacation": "🏖️",
}


def get_expense_icon(title, description=None):
    text_priority = (title or "") + " " + (description or "")
    text_priority = text_priority.lower()
    best_score = 0
    best_match = None
    for category, keywords in ICON_MAP.items():
        if any(word in text_priority for word in keywords):
            return ICON_EMOJIS[category]
        else:
            for keyword in keywords:
                score = fuzz.partial_ratio(keyword, text_priority)
                if score > best_score:
                    best_score = score
                    best_match = category
    if best_score > 80:
        return ICON_EMOJIS[best_match]

    generated_icon = generate_content(
        f"Suggest one emoji based on this text, suggest only single emoji no text: {text_priority}"
    ).strip()

    if generated_icon:
        return generated_icon
    return "💸"
