from utils.nodes import NodeManager
from marzban_api import migrate_user_to_node
from db.base import engine
from sqlalchemy import select
from db.models import TelegramUsers
import glv

async def rebalance_users():
    node_manager = NodeManager(glv.config["NODES"])
    best_node = await node_manager.choose_best_node()
    best_node_name = best_node["name"]

    async with engine.connect() as conn:
        result = await conn.execute(select(TelegramUsers))
        users = result.fetchall()

    for user in users:
        if user.node != best_node_name:
            try:
                await migrate_user_to_node(user.username, best_node)
                print(f"✅ {user.username} => {best_node_name}")
            except Exception as e:
                print(f"❌ {user.username} not migrated: {e}")
