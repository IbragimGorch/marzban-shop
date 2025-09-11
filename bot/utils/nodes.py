# utils/nodes.py
from typing import Optional

class NodeManager:
    """
    Заглушка. Больше не выбираем ноды из БД.
    """

    def __init__(self, default_node: Optional[str] = None):
        self.default_node = default_node

    async def get_nodes_from_db(self):
        # Раньше ходили в marzban_shop.nodes; теперь — нет
        return []

    async def choose_best_node(self) -> Optional[str]:
        # Возвращаем дефолт (если задан) или None — панель сама разберётся
        return self.default_node
