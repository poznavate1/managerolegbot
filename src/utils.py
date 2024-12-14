from PIL import Image, ImageDraw, ImageFont
import os
from config import IMAGES_PATH, TEMP_IMAGES_PATH

# Путь к стандартному шрифту, если нужно использовать пользовательский
DEFAULT_FONT_PATH = "arial.ttf"

def add_code_to_image(code, background_path, output_path):
    """
    Добавляет текстовый код на фоновое изображение и сохраняет результат.

    :param code: Код для отображения на изображении.
    :param background_path: Путь к фоновому изображению.
    :param output_path: Путь для сохранения нового изображения.
    :return: Путь к сохранённому изображению.
    """
    try:
        # Загружаем фоновое изображение
        background = Image.open(background_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Фоновое изображение не найдено по пути: {background_path}")
    except IOError as e:
        raise IOError(f"Ошибка при открытии фонового изображения: {e}")

    # Получаем размеры изображения
    width, height = background.size

    # Загружаем шрифт (используем стандартный шрифт, если пользовательский не найден)
    try:
        font_size = 500  # Размер шрифта для текста (измените этот параметр для изменения размера текста)
        font = ImageFont.truetype(DEFAULT_FONT_PATH, size=font_size)
    except IOError:
        print(f"Пользовательский шрифт не найден. Используется стандартный шрифт.")
        font = ImageFont.load_default()

    # Создаем объект для рисования текста
    draw = ImageDraw.Draw(background)

    # Размер текста
    text_bbox = draw.textbbox((0, 0), code, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    # Координаты для размещения текста по центру
    position = ((width - text_width) // 2, (height - text_height) // 2)

    # Добавляем текст
    draw.text(position, code, fill=(255, 255, 255), font=font)

    # Убедимся, что директория для сохранения существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Сохраняем изображение
    try:
        background.save(output_path)
        print(f"Изображение с кодом сохранено в: {output_path}")
    except IOError as e:
        print(f"Ошибка при сохранении изображения: {e}")
        return None

    return output_path

def process_photo_with_code(code):
    """
    Генерирует изображение с текстовым кодом.

    :param code: Код для добавления на изображение.
    :return: Путь к сгенерированному изображению.
    """
    # Пути к файлам в папке temp
    background_path = os.path.join(TEMP_IMAGES_PATH, "user_images", "stock_image.png")
    output_path = os.path.join(TEMP_IMAGES_PATH, "user_images", f"stock_image_with_code_{code}.png")

    # Преобразуем пути в абсолютные
    background_path = os.path.abspath(background_path)
    output_path = os.path.abspath(output_path)

    # Генерируем изображение с кодом
    return add_code_to_image(code, background_path, output_path)


from datetime import datetime, timedelta

# Система модерации
class ModerationSystem:
    def __init__(self):
        self.muted_users = {}  # user_id: {attempts: int, muted_until: datetime, mute_count: int}
        self.MAX_ATTEMPTS = 5

    def increment_attempts(self, user_id: int) -> tuple[bool, int]:
        """Увеличивает счетчик неудачных попыток и возвращает (нужно_ли_мутить, осталось_попыток)"""
        if user_id not in self.muted_users:
            self.muted_users[user_id] = {"attempts": 1, "muted_until": None, "mute_count": 0}
            return False, self.MAX_ATTEMPTS - 1
        
        if not self.is_muted(user_id):
            self.muted_users[user_id]["attempts"] += 1
            attempts = self.muted_users[user_id]["attempts"]
            
            if attempts >= self.MAX_ATTEMPTS:
                return True, 0
            return False, self.MAX_ATTEMPTS - attempts
        return True, 0

    def mute_user(self, user_id: int) -> dict:
        """Мутит пользователя и возвращает информацию о муте"""
        user_data = self.muted_users.get(user_id, {"mute_count": 0})
        user_data["mute_count"] += 1
        
        # Рассчитываем длительность мута (1 час * 10^(количество мутов - 1))
        duration_hours = 1 * (10 ** (user_data["mute_count"] - 1))
        muted_until = datetime.now() + timedelta(hours=duration_hours)
        
        self.muted_users[user_id] = {
            "attempts": 0,
            "muted_until": muted_until,
            "mute_count": user_data["mute_count"]
        }
        
        return {
            "duration_hours": duration_hours,
            "muted_until": muted_until,
            "mute_count": user_data["mute_count"]
        }

    def is_muted(self, user_id: int) -> bool:
        """Проверяет, находится ли пользователь в муте"""
        if user_id not in self.muted_users:
            return False
            
        muted_until = self.muted_users[user_id]["muted_until"]
        if not muted_until:
            return False
            
        if datetime.now() >= muted_until:
            self.muted_users[user_id]["muted_until"] = None
            self.muted_users[user_id]["attempts"] = 0
            return False
        return True

    def unmute_user(self, user_id: int) -> bool:
        """Размучивает пользователя"""
        if user_id in self.muted_users and self.is_muted(user_id):
            self.muted_users[user_id]["muted_until"] = None
            self.muted_users[user_id]["attempts"] = 0
            return True
        return False

    def get_muted_users(self) -> list:
        """Возвращает список замученных пользователей"""
        current_time = datetime.now()
        muted_list = []
        
        for user_id, data in self.muted_users.items():
            if not data["muted_until"] or current_time >= data["muted_until"]:
                continue
                
            time_left = data["muted_until"] - current_time
            hours_left = round(time_left.total_seconds() / 3600, 1)
            
            muted_list.append({
                "user_id": user_id,
                "muted_until": data["muted_until"].strftime("%Y-%m-%d %H:%M:%S"),
                "hours_left": hours_left,
                "mute_count": data["mute_count"]
            })
        
        return muted_list

# Создаем глобальный экземпляр системы модерации
moderation = ModerationSystem()