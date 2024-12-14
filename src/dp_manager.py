import os
import sys
import sqlite3
import logging
from config import DATABASE_PATH  # Путь к базе данных

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константа для исключения stock_image.png
EXCLUDED_IMAGE = "stock_image.png"

def check_and_create_db_folder():
    """Проверка и создание папки для базы данных, если она не существует."""
    db_folder = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_folder):
        try:
            os.makedirs(db_folder)
            logging.info(f"Создана папка для базы данных: {db_folder}")
        except Exception as e:
            logging.error(f"Ошибка при создании папки для базы данных: {e}")
            sys.exit(1)

def create_database_and_table():
    """Создаёт базу данных и таблицу users, если они не существуют."""
    check_and_create_db_folder()
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем существование старой таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Создаем временную таблицу с новой структурой
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users_new (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE,
                        contact_text TEXT,
                        chat_id INTEGER,
                        img TEXT
                    )
                ''')
                
                # Копируем данные из старой таблицы, преобразуя message_id в contact_text
                try:
                    cursor.execute("SELECT code, message_id, chat_id, img FROM users")
                    old_data = cursor.fetchall()
                    for row in old_data:
                        code, message_id, chat_id, img = row
                        # Здесь можно добавить логику преобразования message_id в contact_text
                        cursor.execute(
                            "INSERT INTO users_new (code, contact_text, chat_id, img) VALUES (?, ?, ?, ?)",
                            (code, str(message_id), chat_id, img)
                        )
                except sqlite3.Error as e:
                    logging.error(f"Ошибка при миграции данных: {e}")
                
                # Удаляем старую таблицу и переименовываем новую
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")
            else:
                # Если таблица не существует, создаем новую
                cursor.execute('''
                    CREATE TABLE users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE,
                        contact_text TEXT,
                        chat_id INTEGER,
                        img TEXT
                    )
                ''')
            
            conn.commit()
            logging.info("База данных успешно обновлена или создана.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при создании/обновлении базы данных: {e}")

def check_code_exists(code: str) -> bool:
    """Проверяет существование кода в базе данных."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE code = ?", (code,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке кода: {e}")
        return False

def add_user(code: str, contact_text: str, chat_id: int) -> str:
    """Добавляет пользователя в таблицу, если код не занят."""
    if check_code_exists(code):
        return "Данный код занят, введите другой."

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (code, contact_text, chat_id) 
                VALUES (?, ?, ?)
            ''', (code, contact_text, chat_id))
            conn.commit()
            logging.info(f"Запись с кодом {code} добавлена.")
            return "Данные успешно сохранены."
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении пользователя: {e}")
        return "Произошла ошибка при добавлении данных."

def delete_user_by_code(code: str) -> str:
    """Удаляет пользователя по коду, а также фотографию, если она прикреплена."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT img FROM users WHERE code = ?", (code,))
            result = cursor.fetchone()

            if result:
                img_path = result[0]
                # Удаляем изображение, если это не stock_image.png
                if img_path and img_path != EXCLUDED_IMAGE:
                    delete_image(img_path)

            cursor.execute("DELETE FROM users WHERE code = ?", (code,))
            conn.commit()

            if cursor.rowcount > 0:
                logging.info(f"Запись с кодом {code} удалена.")
                return f"Запись с кодом {code} и изображение (если было) удалены."
            else:
                logging.info(f"Запись с кодом {code} не найдена.")
                return f"Запись с кодом {code} не найдена."
    except sqlite3.Error as e:
        logging.error(f"Ошибка при удалении пользователя: {e}")
        return "Произошла ошибка при удалении данных."

def get_contacts_by_code(code: str):
    """Получает contact_text и chat_id по коду."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT contact_text, chat_id FROM users WHERE code = ?",
                (code,)
            )
            result = cursor.fetchone()
            return result if result else None
    except Exception as e:
        logging.error(f"Ошибка при получении контактов: {e}")
        return None

def save_img_path(code: str, img_path: str) -> str:
    """Сохраняет путь к изображению в базе данных для указанного кода."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET img = ? WHERE code = ?", (img_path, code))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"Путь к изображению для кода {code} обновлён.")
                return "Изображение успешно обработано."
            else:
                logging.warning(f"Код {code} не найден.")
                return f"Код {code} не найден в базе данных."
    except sqlite3.Error as e:
        logging.error(f"Ошибка при сохранении пути к изображению: {e}")
        return "Произошла ошибка при сохранении изображения."

def clear_table() -> str:
    """Очищает таблицу users и удаляет все фотографии (кроме stock_image.png)."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT img FROM users")
            rows = cursor.fetchall()

            # Удаляем все фотографии, кроме stock_image.png
            for row in rows:
                img_path = row[0]
                if img_path and img_path != EXCLUDED_IMAGE:
                    delete_image(img_path)

            cursor.execute("DELETE FROM users")
            conn.commit()
            logging.info("Таблица users очищена, все фотографии (кроме stock_image.png) удалены.")
            return "Таблица users очищена, все фотографии (кроме stock_image.png) удалены."
    except sqlite3.Error as e:
        logging.error(f"Ошибка при очистке таблицы: {e}")
        return "Произошла ошибка при очистке таблицы."
    
def get_img_path_by_code(code: str) -> str:
    """Получает путь к изображению по коду."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT img FROM users WHERE code = ?", (code,))
            result = cursor.fetchone()
            if result:
                logging.info(f"Путь к изображению для кода {code} найден: {result[0]}")
            else:
                logging.info(f"Код {code} не найден в базе данных.")
            return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении пути к изображению: {e}")
        return None

def delete_image(img_path: str) -> str:
    """Удаляет изображение по указанному пути."""
    try:
        if os.path.exists(img_path):
            os.remove(img_path)
            logging.info(f"Изображение {img_path} успешно удалено.")
            return f"Изображение {img_path} успешно удалено."
        else:
            logging.warning(f"Изображение {img_path} не найдено.")
            return f"Изображение {img_path} не найдено."
    except Exception as e:
        logging.error(f"Ошибка при удалении изображения: {e}")
        return f"Произошла ошибка при удалении изображения: {e}"

def get_all_codes_with_contacts():
    """Получает все коды и контактную информацию."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code, contact_text, chat_id FROM users")
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении всех контактов: {e}")
        return []


        
def get_message_id_by_code(code: str):
    """Получает contact_text по коду."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT contact_text FROM users WHERE code = ?",
                (code,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logging.error(f"Ошибка при получении contact_text: {e}")
        return None




if __name__ == "__main__":
    create_database_and_table()