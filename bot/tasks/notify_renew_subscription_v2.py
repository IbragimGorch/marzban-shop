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
    logger.debug("Checking users to notify (day before)...")
    marzban_users_day_before = await get_marzban_users_to_notify_day_before()
    logger.debug(f"Users to notify (day before): {marzban_users_day_before}")

    logger.debug("Checking users to notify (2 hours before)...")
    marzban_users_2_hours_before = await get_marzban_users_to_notify_2_hours_before()
    logger.debug(f"Users to notify (2 hours before): {marzban_users_2_hours_before}")

    if marzban_users_day_before:
        await send_notifications(marzban_users_day_before, "day")
    if marzban_users_2_hours_before:
        await send_notifications(marzban_users_2_hours_before, "2hour")
async def send_notifications(users_to_notify, mode):
    try:
        list_vpn_id = [user["username"] for user in users_to_notify]
        for vpn_id in list_vpn_id:
            user = await get_marzban_profile_by_vpn_id(vpn_id)
            if user is None:
                continue

            chat_member = await glv.bot.get_chat_member(user.tg_id, user.tg_id)
            if chat_member is None:
                continue

            if mode == "day":
                message = get_i18n_string(
                    "Hello, {name} 👋🏻\n"
                    "\n"
                    "Thank you for using our service ❤️\n️"
                    "\n"
                    "Your VPN subscription expires at the end of the day tomorrow.\n️"
                    "\n"
                    "To renew it, just go to the \"Pay 🏄🏻‍♂️\" section and make a payment.",
                    chat_member.user.language_code
                ).format(name=chat_member.user.first_name)

            elif mode == "2hour":
                message = get_i18n_string(
                    "Hello, {name} 👋 \n"
                    "\n"
                    "Just a reminder, your VPN subscription is ending very soon ⏰\n"
                    "\n"
                    "To avoid disconnection, please renew it now via the \"Pay 🏄🏻‍♂️\" section.",
                    chat_member.user.language_code
                ).format(name=chat_member.user.first_name)

            await glv.bot.send_message(user.tg_id, message)

    except Exception as e:
        logger.error(f"? error sending notification: {e}", exc_info=True)


# New time filter functions

async def get_marzban_users_to_notify_day_before():
    res = await marzban_api.panel.get_users()
    if res is None:
        return None
    users = res['users']
    for user in users:
        logger.debug(f"User: {user['username']} expires at {user.get('expire')}")
        return list(filter(filter_users_to_notify_day_before, users))
def filter_users_to_notify_day_before(user):
    user_expire_date = user.get('expire')
    if user_expire_date is None:
        return False

    current_time = int(time.time())
    from_date = current_time + 60 * 60 * 12
    to_date = from_date + 60 * 60 * 24

    in_range = from_date < user_expire_date < to_date
    logger.debug(f"[Day Filter] {user['username']} ? {user_expire_date}, in range: {in_range}")
    return in_range

async def get_marzban_users_to_notify_2_hours_before():
    res = await marzban_api.panel.get_users()
    if res is None:
        return None
    users = res['users']
    for user in users:
        logger.debug(f"User: {user['username']} expires at {user.get('expire')}")
        return list(filter(filter_users_to_notify_day_before, users))

def filter_users_to_notify_2_hours_before(user):
    user_expire_date = user.get('expire')
    if user_expire_date is None:
        return False

    current_time = int(time.time())
    in_range = current_time < user_expire_date <= current_time + 3 * 60 * 60
    logger.debug(f"[2 Hour Filter] {user['username']} ? {user_expire_date}, in range: {in_range}")
    return in_range

if __name__ == "__main__":
    current_time = int(time.time())
    logger.debug(f"Current time: {current_time}")

    import asyncio


