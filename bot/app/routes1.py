import logging
import ipaddress
from aiohttp import web
from aiohttp.web_request import Request

import glv
from utils import goods, marzban_api
from utils.lang import get_i18n_string
from keyboards.main_menu import get_main_menu_keyboard
from db.methods import get_yookassa_payment, delete_payment
from utils.marzban_api import get_marzban_profile
from app.database import get_user  # <-- ?? ????? ??????? telegram_users

YOOKASSA_IPS = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
]

async def check_yookassa_payment(request: Request):
    logging.info("YooKassa webhook received: %s", await request.text())
    client_ip = request.headers.get('CF-Connecting-IP') or request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote
    f = True
    for subnet in YOOKASSA_IPS:
        if "/" in subnet:
            if ipaddress.ip_address(client_ip) in ipaddress.ip_network(subnet):
                f = False
                break
        else:
            if client_ip == subnet:
                f = False
                break
    if f:
        return web.Response(status=403)
    data = (await request.json())['object']
    payment = await get_yookassa_payment(data['id'])
    if payment == None:
        return web.Response()
    if data['status'] == 'succeeded':
        good = goods.get(payment.callback)
        user = await get_marzban_profile(payment.tg_id)
        result = await marzban_api.generate_marzban_subscription(user['username'], good)
        text = get_i18n_string("Thank you for your choice ❤️\n️\n<a href=\"{link}\">Subscribe</a> so you don't miss any announcements ✅\n️\nYour subscription is purchased and available in \"My subscription 👤\".", payment.lang)
        await glv.bot.send_message(payment.chat_id,
            text.format(
                link=glv.config['PANEL_GLOBAL'] + result['subscription_url']
            ),
            reply_markup=get_main_menu_keyboard(payment.lang)
        )
        await delete_payment(payment.payment_id)
        return web.Response(status=200)
    if user_telegram_id:
        try:
            new_expire_date = datetime.fromtimestamp(user['expire'])
            await bot.send_message(
                user_telegram_id,
                f"✅ {bold('Подписка продлена!')}\n"
                f"Теперь активна до: {new_expire_date.strftime('%d.%m.%Y %H:%M')}"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления о продлении: {e}")