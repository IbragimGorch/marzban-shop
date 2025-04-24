import asyncio
import time
import logging
from utils import marzban_api
from utils.lang import get_i18n_string
from db.methods import get_marzban_profile_by_vpn_id
import glv
from db.methods import (
    get_marzban_profile_db,
    get_yookassa_payment,
    get_cryptomus_payment,
    delete_payment
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def notify_users_to_renew_sub():
    marzban_users_to_notify = await get_marzban_users_to_notify()
    if marzban_users_to_notify is None:
        return None
    
    try:
        list_vpn_id = [user["username"] for user in marzban_users_to_notify]
        logger.debug(f"VPN ID list to notify: {list_vpn_id}")

        for vpn_id in list_vpn_id:
            user = await get_marzban_profile_by_vpn_id(vpn_id)
            if user is None:
                logger.debug(f"User with VPN ID {vpn_id} not found.")
                continue

            chat_member = await glv.bot.get_chat_member(user.tg_id, user.tg_id)
            logger.debug(f"ID Telegram user: {user.tg_id}")
            if chat_member is None:
                logger.debug(f"tg chat with user TG ID {user.tg_id} not found.")
                continue

            message = get_i18n_string(
                "Hello, {name} 👋 \n"
                "\n"
                "Thank you for using our service ❤️\n"
                "\n"
                "Your VPN subscription expires at the end of the day tomorrow.\n"
                "\n"
                "To renew it, just go to the \"Pay 🏄🏻‍♂️\" section and make a payment.",
                chat_member.user.language_code
            ).format(name=chat_member.user.first_name)

            logger.debug(f"trying to send mes {user.tg_id} ({chat_member.user.first_name})")
            await glv.bot.send_message(user.tg_id, message)
            logger.debug(f"successfully sent to {user.tg_id}")

    except Exception as e:
        logger.error(f"? error sending {user.tg_id}: {e}", exc_info=True)

async def get_marzban_users_to_notify():
    res = await marzban_api.panel.get_users()
    if res is None:
        return None
    users = res['users']
    return list(filter(filter_users_to_notify, users))

def filter_users_to_notify(user):
    user_expire_date = user.get('expire')
    if user_expire_date is None:
        return False
    from_date = int(time.time()) + 60 * 60 * 12
    to_date = from_date + 60 * 60 * 24
    return from_date < user_expire_date < to_date

