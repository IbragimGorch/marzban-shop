import pymysql
import pymysql.cursors
import logging
import time

# ????????? ??????????? ? ??
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "marzban"
DB_PASS = "Gobi7890!!"
DB_NAME = "marzban_shop"

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def save_user(tg_id, serial4, user_data):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO telegram_users (tg_id, serial4, username, subscription_url)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    serial4 = VALUES(serial4),
                    username = VALUES(username),
                    subscription_url = VALUES(subscription_url)
                """
                cursor.execute(sql, (tg_id, serial4, user_data["username"], user_data["subscription_url"]))
    except Exception as e:
        logging.error(f"Error saving user: {e}")

def get_user(tg_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM telegram_users WHERE tg_id = %s"
                cursor.execute(sql, (tg_id,))
                return cursor.fetchone()
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return None

def get_users_for_notifications(time_before_expire_seconds):
    now = int(time.time())
    expire_threshold = now + time_before_expire_seconds
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM telegram_users
                JOIN vpn_users ON telegram_users.username = vpn_users.username
                WHERE vpn_users.expire <= %s AND vpn_users.expire IS NOT NULL
                """
                cursor.execute(sql, (expire_threshold,))
                return cursor.fetchall()
    except Exception as e:
        logging.error(f"Error getting users for notifications: {e}")
        return []

#def remove_expired_users():
#    now = int(time.time())
#    try:
#        with get_connection() as conn:
#            with conn.cursor() as cursor:
#                sql = """
#                DELETE telegram_users FROM telegram_users
#                JOIN vpn_users ON telegram_users.username = vpn_users.username
#                WHERE vpn_users.expire <= %s
#                """
#                cursor.execute(sql, (now,))
#    except Exception as e:
#        logging.error(f"Error removing expired users: {e}")
