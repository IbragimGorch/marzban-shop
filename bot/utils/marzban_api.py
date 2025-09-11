import time
import aiohttp
import requests
import logging
import uuid
import json

from app.database import get_user
from db.methods import update_telegram_user_subscription
import glv

PROTOCOLS = {
    
    "vless": [
        {
            "flow": "xtls-rprx-vision"
        },
        ["VLESS TCP REALITY"]
    ],
    
}

class Marzban:
    def __init__(self, ip, login, passwd) -> None:
        self.ip = ip
        self.login = login
        self.passwd = passwd
    
    async def _send_request(self, method, path, headers=None, data=None) -> dict | list:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, self.ip + path, headers=headers, json=data) as resp:
                if 200 <= resp.status < 300:
                    body = await resp.json()
                    return body
                else:
                    raise Exception(f"Error: {resp.status}; Body: {await resp.text()}; Data: {data}")
    



    def get_token(self) -> str:
        data = {
            "username": self.login,
            "password": self.passwd
        }
        resp = requests.post(self.ip + "/api/admin/token", data=data).json()
        self.token = resp["access_token"]
        return self.token
    
    async def get_user(self, username) -> dict:
        headers = {
            'Authorization': f"Bearer {self.token}"
        }
        resp = await self._send_request("GET", f"/api/user/{username}", headers=headers)
        return resp
    
    async def get_users(self) -> dict:
        headers = {
            'Authorization': f"Bearer {self.token}"
        }
        resp = await self._send_request("GET", "/api/users", headers=headers)
        return resp
    
    async def add_user(self, data) -> dict:
        headers = {
            'Authorization': f"Bearer {self.token}"
        }
        resp = await self._send_request("POST", "/api/user", headers=headers, data=data)
        return resp
    
    async def modify_user(self, username, data) -> dict:
        headers = {
            'Authorization': f"Bearer {self.token}"
        }
        resp = await self._send_request("PUT", f"/api/user/{username}", headers=headers, data=data)
        return resp

def get_protocols() -> dict:
    proxies = {}
    inbounds = {}
    
    for proto in glv.config['PROTOCOLS']:
        l = proto.lower()
        if l not in PROTOCOLS:
            continue
        proxies[l] = PROTOCOLS[l][0]
        inbounds[l] = PROTOCOLS[l][1]
    return {
        "proxies": proxies,
        "inbounds": inbounds
    }

panel = Marzban(glv.config['PANEL_HOST'], glv.config['PANEL_USER'], glv.config['PANEL_PASS'])
mytoken = panel.get_token()
ps = get_protocols()

async def check_if_user_exists(name: str) -> bool:
    try:
        await panel.get_user(name)
        return True
    except Exception as e:
        return False

async def get_marzban_profile(tg_id: int):
    db_user = get_user(tg_id)
    if not db_user:
        return None
    vpn_id = db_user['username']
    try:
        user = await panel.get_user(vpn_id)
        return user
    except Exception:
        return None

async def generate_test_subscription(username: str):
    res = await check_if_user_exists(username)
    if res:
        user = await panel.get_user(username)
        user['status'] = 'active'
        if not user.get('expire') or user['expire'] < time.time():
            user['expire'] = get_test_subscription(glv.config['PERIOD_LIMIT'])
        else:
            user['expire'] += get_test_subscription(glv.config['PERIOD_LIMIT'], True)
        result = await panel.modify_user(username, user)
    else:
        user = {
            'username': username,
            'proxies': ps["proxies"],
            'inbounds': ps["inbounds"],
            'expire': get_test_subscription(glv.config['PERIOD_LIMIT']),
            'data_limit': 0,
            'data_limit_reset_strategy': "no_reset",
        }
        result = await panel.add_user(user)
    return result

async def generate_subscription_link(username: str) -> str:
    """
    Возвращает ПОЛНУЮ ссылку подписки (PANEL_HOST + subscription_url) без миграций/нодов.
    """
    if not hasattr(panel, "token") or not panel.token:
        panel.get_token()
    user = await panel.get_user(username)
    path = user.get("subscription_url")
    if not path:
        raise Exception("Panel response has no 'subscription_url'")
    return f"{glv.config['PANEL_HOST']}{path}"

async def extend_user_expire(username: str, months: int) -> int:
    """
    Продлевает срок действия пользователя в панели на N месяцев (30 дней * N).
    Возвращает новое значение expire (Unix time).
    (Эту функцию можно вызывать по событию оплаты, когда захочешь.)
    """
    if not hasattr(panel, "token") or not panel.token:
        panel.get_token()
    now = int(time.time())
    add_seconds = 60 * 60 * 24 * 30 * int(months or 1)
    exists = await check_if_user_exists(username)
    if exists:
        user = await panel.get_user(username)
        current_expire = int(user.get("expire") or 0)
        base = now if current_expire < now else current_expire
        user["expire"] = base + add_seconds
        user["status"] = "active"
        user["data_limit_reset_strategy"] = user.get("data_limit_reset_strategy", "no_reset")
        await panel.modify_user(username, user)
        updated = await panel.get_user(username)
        return int(updated.get("expire") or 0)
    else:
        new_user = {
            "username": username,
            "proxies": ps["proxies"],
            "inbounds": ps["inbounds"],
            "expire": now + add_seconds,
            "data_limit": 0,
            "data_limit_reset_strategy": "no_reset",
            "status": "active",
        }
        await panel.add_user(new_user)
        created = await panel.get_user(username)
        return int(created.get("expire") or 0)

# Тонкий враппер для обратной совместимости — теперь только формирует ссылку и сохраняет её в telegram_users.
async def generate_marzban_subscription(username: str, good, tg_id: int):
    link = await generate_subscription_link(username)
    await update_telegram_user_subscription(tg_id, link)
    logging.info(f"🔗 subscription link updated for {username}: {link}")
    return {"subscription_url": link, "node": None}


    

def get_test_subscription(hours: int, additional= False) -> int:
    return (0 if additional else int(time.time())) + 60 * 60 * hours

def get_subscription_end_date(months: int, additional = False) -> int:
    return (0 if additional else int(time.time())) + 60 * 60 * 24 * 30 * months

async def find_user_by_last4(last4: str) -> dict | None:
    # Ensure we have a token
    if not hasattr(panel, "token") or not panel.token:
        panel.get_token()

    # Fetch the raw response
    try:
        raw = await panel.get_users()
    except Exception:
        logging.exception("Error fetching users from panel")
        raise

    # Unwrap the list of user entries under the "users" key
    if isinstance(raw, dict):
        users = raw.get("users", [])
    elif isinstance(raw, list):
        users = raw
    else:
        users = []

    # Iterate over each entry
    for entry in users:
        # Extract username
        if isinstance(entry, dict):
            username = entry.get("username")
        else:
            username = entry

        if not isinstance(username, str):
            continue

        # Match last 4 digits
        if username.endswith(last4):
            try:
                return await panel.get_user(username)
            except Exception:
                logging.exception(f"Error fetching user {username}")
                raise

    return None

#async def migrate_user_to_node(username: str, new_node: dict, tg_id: int):
#    panel = Marzban(
#        glv.config["PANEL_HOST"],
#        glv.config["PANEL_USER"],
#        glv.config["PANEL_PASS"]
#    )
#    panel.get_token()
#
#    user = await panel.get_user(username)
#
#    # *** Replace user["inbounds"]["vless"] list with the chosen tag ***
#    user_inbounds = user.get("inbounds", {})
#    # For vless protocol:
#    user_inbounds["vless"] = [ new_node["inbound_tag"] ]
#    user["inbounds"] = user_inbounds
#
#    await panel.modify_user(username, user)
#    print(f"✅ {username} now uses inbound «{new_node['inbound_tag']}»")





async def find_user_by_username(username: str):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {glv.config['PANEL_PASS']}",
                "Content-Type": "application/json",
            }
            url = f"{glv.config['PANEL_HOST']}/api/users"
            logging.info(f"?? ??? ????? ? ??????: {url} ? ??????? {glv.config['PANEL_PASS']}")


            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status != 200:
                
                    return None

                users = await response.json()

                for user in users:
                    if user.get("username") == username:
                        return user

                return None
