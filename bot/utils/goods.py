import json

def load_goods() -> list:
    try:
        with open("goods.json", encoding="utf-8") as file:
            return json.load(file)
    except UnicodeDecodeError:
        with open("goods.json", encoding="cp1252") as file:
            return json.load(file)

def get(callback=None) -> list | dict:
    data = load_goods()
    if callback is None:
        return data
    for v in data:
        if v['callback'] == callback:
            return v
    return dict()

def get_callbacks() -> list:
    data = load_goods()
    return [x['callback'] for x in data]
