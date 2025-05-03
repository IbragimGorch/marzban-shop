from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import insert, select, delete, update
from db.base import async_session_maker
from db.models import TelegramUsers

from db.models import YPayments, Users
import glv

# ??????????? ? ??
engine = create_async_engine(glv.config['DB_URL'])

# === ???????? ?????? ? ????????? ===

async def add_yookassa_payment(tg_id: int, callback: str, chat_id: int, lang_code: str, payment_id) -> dict:
    async with engine.connect() as conn:
        sql_q = insert(YPayments).values(
            tg_id=tg_id,
            payment_id=payment_id,
            chat_id=chat_id,
            callback=callback,
            lang=lang_code
        )
        await conn.execute(sql_q)
        await conn.commit()


async def get_yookassa_payment(payment_id) -> YPayments:
    async with engine.connect() as conn:
        sql_q = select(YPayments).where(YPayments.payment_id == payment_id)
        payment: YPayments = (await conn.execute(sql_q)).fetchone()
    return payment

async def delete_payment(payment_id):
    async with engine.connect() as conn:
        sql_q = delete(YPayments).where(YPayments.payment_id == payment_id)
        await conn.execute(sql_q)
        await conn.commit()

# получить запись по telegram_id
async def get_telegram_user(tg_id: int):
    async with engine.connect() as conn:
        res = await conn.execute(select(TelegramUsers)
                                 .where(TelegramUsers.telegram_id == tg_id))
        return res.fetchone()

# обновить ноду и ссылку
async def update_telegram_user_node(tg_id: int, node_name: str, sub_url: str):
    sql = (
      update(TelegramUsers)
      .where(TelegramUsers.telegram_id == tg_id)
      .values(node=node_name, subscription_url=sub_url)
    )
    await conn.execute(sql)
    await conn.commit()

        
async def get_vpn_user_by_username(username: str) -> Users | None:
    async with async_session_maker() as session:
        result = await session.execute(select(Users).where(Users.username == username))
        return result.scalar_one_or_none()