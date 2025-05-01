from sqlalchemy import Column, BigInteger, String, Boolean, Integer, Enum, DateTime, JSON, ForeignKey, Text

from db.base import Base

#class VPNUsers(Base):
#    __tablename__ = "vpnusers"
#    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
#    tg_id = Column(BigInteger)
#    vpn_id = Column(String(64), default="")
#    test = Column(Boolean, default=False)

class CPayments(Base):
    __tablename__ = "crypto_payments"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    tg_id = Column(BigInteger)
    lang = Column(String(64))
    payment_uuid = Column(String(64))
    order_id = Column(String(64))
    chat_id = Column(BigInteger)
    callback = Column(String(64))

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