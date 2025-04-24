import aioschedule
import asyncio
import logging


from .update_token import update_token
from .notify_renew_subscription import notify_users_day_before, notify_users_3_hours_before


import glv

async def register():
    aioschedule.every(5).minutes.do(update_token)
    aioschedule.every().day.at("13:10").do(notify_users_day_before)
    aioschedule.every().day.at("18:10").do(notify_users_3_hours_before)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)