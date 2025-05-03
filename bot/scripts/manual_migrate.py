#!/usr/bin/env python3
import sys, os, asyncio

# прокидываем корень проекта
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

import glv
from utils.marzban_api import migrate_user_to_node

USAGE = """
Usage:
  manual_migrate.py <username> <telegram_id> [node_name]

  username        — логин в Marzban (например, F4Q409514)
  telegram_id     — твой telegram_id из таблицы telegram_users
  node_name       — опционально, имя ноды из glv.config["NODES"]
                    (по умолчанию первая нода из конфига)
"""

async def main():
    if len(sys.argv) < 3:
        print(USAGE)
        return

    username  = sys.argv[1]
    try:
        tg_id   = int(sys.argv[2])
    except ValueError:
        print("❌ telegram_id должен быть числом")
        print(USAGE)
        return

    # выбираем имя ноды
    names = [n["name"] for n in glv.config["NODES"]]
    node_name = sys.argv[3] if len(sys.argv) >= 4 else names[0]
    if node_name not in names:
        print(f"❌ Ноды с именем «{node_name}» нет, доступны: {names}")
        return

    cfg_node = next(n for n in glv.config["NODES"] if n["name"] == node_name)

    try:
        # теперь передаём tg_id третьим аргументом
        await migrate_user_to_node(username, cfg_node, tg_id)
        print(f"✅ {username} (tg_id={tg_id}) теперь на ноде «{node_name}»")
    except Exception as e:
        print("❌ Ошибка миграции:", e)

if __name__ == "__main__":
    asyncio.run(main())
