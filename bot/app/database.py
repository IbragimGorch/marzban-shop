import pymysql
import logging
from glv import config

# Подключение к базе
connection = pymysql.connect(
    host=config['DB_ADDRESS'],
    user=config['DB_USER'],
    password=config['DB_PASS'],
    database=config['DB_NAME'],
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

logging.info("✅ Connected to MySQL database!")

# Создание таблицы, если вдруг нет
def create_telegram_users_table():
    with connection.cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id BIGINT NOT NULL UNIQUE,
                username VARCHAR(34) NOT NULL,
                subscription_url VARCHAR(255)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')
    logging.info("✅ Table 'telegram_users' ready!")

# Сохранение или обновление пользователя
def save_user(telegram_id: int, username: str, subscription_url: str, email: str):
    with connection.cursor() as cursor:
        sql = """
        INSERT INTO telegram_users (telegram_id, username, subscription_url, email)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE username=VALUES(username), subscription_url=VALUES(subscription_url), email=VALUES(email)
        """
        cursor.execute(sql, (telegram_id, username, subscription_url, email))
    logging.info(f"✅ Saved user {telegram_id} with serial {username} and email {email}")

# Получение пользователя по telegram_id
def get_user(telegram_id: int):
    with connection.cursor() as cursor:
        sql = "SELECT * FROM telegram_users WHERE telegram_id = %s"
        cursor.execute(sql, (telegram_id,))
        return cursor.fetchone()

# Сброс марки, что пользователь уже получил уведомление
def reset_user_notifications(tg_id: int):
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE telegram_users
            SET notified_24h = FALSE, notified_3h = FALSE
            WHERE telegram_id = %s
        """, (tg_id,))


# Удаление пользователя (если надо)
def delete_user(telegram_id: int):
    with connection.cursor() as cursor:
        sql = "DELETE FROM telegram_users WHERE telegram_id = %s"
        cursor.execute(sql, (telegram_id,))
    logging.info(f"✅ Deleted user {telegram_id}")


def mark_user_notified(tg_id: int, field: str):
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE telegram_users SET {field} = TRUE WHERE telegram_id = %s", (tg_id,))


# Получить всех пользователей
def get_all_users():
    with connection.cursor() as cursor:
        sql = "SELECT * FROM telegram_users"
        cursor.execute(sql)
        return cursor.fetchall()

# Создаем таблицу при старте
create_telegram_users_table()

