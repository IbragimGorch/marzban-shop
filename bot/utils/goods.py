import json
import logging
from typing import Optional, List, Dict, Any

GOODS_FILE = "goods.json"

# Старые алиасы → новые callback'и (чтобы не падало, если где-то остались m1/m2/m6)
ALIAS = {
    "m1": "Shadowpath 1",
    "m2": "Shadowpath 2",
    "m6": "Shadowpath 6",
}

def load_goods() -> List[Dict[str, Any]]:
    """
    Возвращает список товаров из goods.json.
    """
    try:
        with open(GOODS_FILE, encoding="utf-8") as file:
            data = json.load(file)
    except UnicodeDecodeError:
        with open(GOODS_FILE, encoding="cp1252") as file:
            data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("goods.json должен содержать список товаров")
    return data

def get(callback: Optional[str] = None) -> Optional[Dict[str, Any]] | List[Dict[str, Any]]:
    """
    Если callback не задан — вернуть весь список.
    Если callback задан — вернуть товар или None.
    """
    data = load_goods()
    if callback is None:
        return data

    cb = ALIAS.get(callback, callback)  # резолвим алиасы
    for v in data:
        if v.get("callback") == cb:
            return v

    logging.warning(f"[goods] Товар с callback='{callback}' (резолв '{cb}') не найден.")
    return None

def get_callbacks() -> List[str]:
    """
    Вернуть список всех callback-значений (ключей товаров).
    """
    return [str(x.get("callback")) for x in load_goods() if "callback" in x]

# Явно экспортируем функции (чтобы не было сюрпризов при импорте)
__all__ = ["load_goods", "get", "get_callbacks"]
