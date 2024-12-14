from dotenv import load_dotenv
import os

load_dotenv()

# Абсолютный путь к корневой директории проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Путь к базе данных
DATABASE_PATH = os.path.join(BASE_DIR, 'db', 'data.sqlite3')

# Папка для хранения изображений
IMAGES_PATH = os.path.join(BASE_DIR, 'images', 'user_images')
if not os.path.exists(IMAGES_PATH):
    os.makedirs(IMAGES_PATH)  # Создаем директорию, если она не существует

# Папка для хранения временных изображений
TEMP_IMAGES_PATH = os.path.join(BASE_DIR, 'images', 'temp')
if not os.path.exists(TEMP_IMAGES_PATH):
    os.makedirs(TEMP_IMAGES_PATH)  # Создаем директорию для временных изображений

# Токен для Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список разрешенных ID пользователей
ALLOWED_USER_IDS = [5762200816, 7179744401, 905319412, 1629696900]

# Другие настройки
DEBUG_MODE = True