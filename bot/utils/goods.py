import json

def get(callback=None) -> list | dict:
    # goods.json is encoded in Windows-1252 (0x96 = en-dash)
    with open("goods.json", encoding="cp1252") as file:        
        data = json.load(file)
    if callback is None:
        return data
    for v in data:
        if v['callback'] == callback:
            return v
    return dict()

def get_callbacks() -> list:
    with open("goods.json") as file:
        data = json.load(file)
    res = [x['callback'] for x in data]
    return res