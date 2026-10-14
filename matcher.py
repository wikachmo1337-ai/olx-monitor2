import re

def normalize(text: str) -> str:
    t = (text or "").lower()
    t = t.replace("ё", "е").replace("ґ", "г")
    return re.sub(r"\s+", " ", t)

# Достаточно, чтобы ЛЮБОЙ паттерн встретился ГДЕ УГОДНО в названии или описании.
GROUPS = {
    "Pixel": [
        r"pixel", r"пиксел", r"піксел",
        r"гугл\s*пикс", r"гугл\s*пікс", r"google\s*pixel",
    ],
    "iPhone": [
        r"iphone", r"i-phone", r"i\s+phone",
        r"айфон", r"аййфон",
    ],
    "Samsung S": [
        r"(samsung|galaxy|самсунг|галакси|гэлакси)[^\n]{0,20}\bs\s?-?\d{1,2}\b",
        r"(самсунг|галакси)[^\n]{0,20}\bс\s?-?\d{1,2}\b",
    ],
    "MacBook": [
        r"macbook", r"mac\s*book", r"макбук", r"мак\s*бук",
    ],
}

# Исключения проверяются ТОЛЬКО по названию объявления.
EXCLUDE = [
    "чехол", "чохол", "стекло", "скло", "копия", "копія", "реплика",
    "обмен", "обмін", "ремонт", "запчаст", "коробка", "кабель",
    "зарядк", "под заказ", "муляж",
]

_compiled = {g: [re.compile(p) for p in ps] for g, ps in GROUPS.items()}

def classify(title: str, description: str):
    text = normalize(f"{title} {description}")
    title_n = normalize(title)
    if any(w in title_n for w in EXCLUDE):
        return None
    for group, patterns in _compiled.items():
        if any(p.search(text) for p in patterns):
            return group
    return None
