from sqlalchemy import text
from db.base import engine

class NodeManager:
    def __init__(self, cfg_nodes):
        self.cfg_nodes = cfg_nodes

    async def get_nodes_from_db(self):
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT name, uplink+downlink AS total_traffic
                FROM nodes
                WHERE status = 'connected'
                ORDER BY total_traffic ASC
            """))
            return [dict(r._mapping) for r in result]

    async def choose_best_node(self):
        db_nodes = await self.get_nodes_from_db()
        # матчим по имени
        for dbn in db_nodes:
            for cfg in self.cfg_nodes:
                if cfg["name"] == dbn["name"]:
                    return cfg
        return self.cfg_nodes[0]  # fallback
