import time
import aiohttp
import requests
import logging
import uuid
import json

from app.database import get_user
from utils.nodes import NodeManager
from db.methods import update_telegram_user_node
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

async def generate_marzban_subscription(username: str, good, tg_id: int):
    # choose best node
    nm = NodeManager(glv.config["NODES"])
    best = await nm.choose_best_node()

    # tell panel to put user on that inbound
    await migrate_user_to_node(username, best, tg_id)

    # fetch updated user to read panel’s subscription_url
    updated = await panel.get_user(username)
    path = updated["subscription_url"]  # e.g. "/sub/…"
    full_url = f"{best['global']}{path}"

    # save into telegram_users
    await update_telegram_user_node(tg_id, best["name"], full_url)

    return {
      "subscription_url": full_url,
      "node": best["name"]
    }


    

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

async def migrate_user_to_node(username: str, new_node: dict, tg_id: int):
    panel = Marzban(
        glv.config["PANEL_HOST"],
        glv.config["PANEL_USER"],
        glv.config["PANEL_PASS"]
    )
    panel.get_token()

    user = await panel.get_user(username)

    # *** Replace user["inbounds"]["vless"] list with the chosen tag ***
    user_inbounds = user.get("inbounds", {})
    # For vless protocol:
    user_inbounds["vless"] = [ new_node["inbound_tag"] ]
    user["inbounds"] = user_inbounds

    await panel.modify_user(username, user)
    print(f"✅ {username} now uses inbound «{new_node['inbound_tag']}»")





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
