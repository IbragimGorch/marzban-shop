from sqlalchemy import Column, BigInteger, String, Integer, Enum, DateTime, Boolean

from db.base import Base


class YPayments(Base):
    __tablename__ = "yookassa_payments"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    lang = Column(String(64))
    payment_id = Column(String(64))
    chat_id = Column(BigInteger)
    callback = Column(String(64))

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(34), unique=True)
    status = Column(Enum('on_hold', 'active', 'limited', 'expired', 'disabled'))
    used_traffic = Column(BigInteger)
    data_limit = Column(BigInteger)
    expire = Column(Integer)
    created_at = Column(DateTime)
    admin_id = Column(Integer)
    data_limit_reset_strategy = Column(Enum('no_reset', 'day', 'week', 'month', 'year'), default='no_reset')
    sub_revoked_at = Column(DateTime)
    note = Column(String(500))
    sub_updated_at = Column(DateTime)
    sub_last_user_agent = Column(String(512))
    online_at = Column(DateTime)
    edit_at = Column(DateTime)
    on_hold_timeout = Column(DateTime)
    on_hold_expire_duration = Column(BigInteger)
    auto_delete_in_days = Column(Integer)
    last_status_change = Column(DateTime)

class TelegramUsers(Base):
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(34), nullable=False)
    subscription_url = Column(String(255))
    email = Column(String(255))
    notified_24h = Column(Boolean, default=False)
    notified_3h = Column(Boolean, default=False)
    node = Column(String(64))  