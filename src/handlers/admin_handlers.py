import os
import re


from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext  
from aiogram.types import FSInputFile

from keyboards.keyboards import (
    get_admin_keyboard, get_moderation_keyboard,
    get_moderation_actions_keyboard, get_inline_back_button,
    get_delete_keyboard, get_list_keyboard, get_start_keyboard
)
from states.states import (
    ModerationStates, DeleteContactState, GetImageState,
    AddContactState
)
from utils import moderation, process_photo_with_code
from dp_manager import (
    add_user, delete_user_by_code, clear_table,
    save_img_path, get_all_codes_with_contacts,
    get_img_path_by_code, get_message_id_by_code
)
from config import ALLOWED_USER_IDS, BOT_TOKEN
import logging



router = Router()
bot = Bot(token=BOT_TOKEN)

def validate_code(code: str) -> bool:
    """Проверяет, что код состоит ровно из 4 цифр."""
    return bool(code and code.isdigit() and len(code) == 4)

@router.message(lambda message: message.text == "Меню")
async def handle_menu(message: Message):
    if message.from_user.id not in ALLOWED_USER_IDS:
        await message.answer("У вас нет прав для доступа к этому меню.")
        return
    
    menu_kb = get_admin_keyboard()
    back_button = get_inline_back_button()
    await message.answer("Панель управления:", reply_markup=menu_kb)
    await message.answer("Используйте кнопку ниже для возврата в главное меню:", reply_markup=back_button)

@router.message(lambda message: message.text == "Добавить контакты")
async def handle_add_contacts(message: Message, state: FSMContext):
    if message.from_user.id not in ALLOWED_USER_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    await state.set_state(AddContactState.waiting_for_code)
    await message.answer(
        "Введите код для нового контакта:",
        reply_markup=get_inline_back_button()
    )

@router.message(AddContactState.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите код.")
        return

    if not validate_code(message.text):
        await message.answer(
            "❌ Некорректный формат кода. Код должен состоять из 4 цифр.",
            reply_markup=get_inline_back_button()
        )
        return

    await state.update_data(code=message.text)
    await state.set_state(AddContactState.waiting_for_contact_info)
    await message.answer("Теперь отправьте контактную информацию:")

@router.message(AddContactState.waiting_for_contact_info)
async def process_contact_info(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте контактную информацию.")
        return

    try:
        data = await state.get_data()
        code = data.get('code')

        # Сохраняем ID сообщения вместо текста
        result = add_user(code, str(message.message_id), message.chat.id)
        if "успешно" not in result.lower():
            await message.answer(result, reply_markup=get_inline_back_button())
            await state.clear()
            return

        # Создаем изображение с кодом
        try:
            photo_path = process_photo_with_code(code)
            if photo_path and os.path.isfile(photo_path):
                # Сохраняем путь к изображению в базе данных
                save_result = save_img_path(code, photo_path)
                if "успешно" in save_result.lower():
                    # Отправляем изображение
                    photo = FSInputFile(photo_path)
                    await message.answer_photo(
                        photo=photo,
                        caption=f"✅ Контакт успешно добавлен!\nКод: {code}",
                        reply_markup=get_inline_back_button()
                    )
                else:
                    await message.answer(
                        f"✅ Контакт добавлен, но произошла ошибка при сохранении пути к изображению: {save_result}",
                        reply_markup=get_inline_back_button()
                    )
            else:
                await message.answer(
                    "✅ Контакт добавлен, но произошла ошибка при создании изображения.",
                    reply_markup=get_inline_back_button()
                )
        except Exception as img_error:
            logging.error(f"Ошибка при создании/сохранении изображения: {img_error}")
            await message.answer(
                "✅ Контакт добавлен, но произошла ошибка при работе с изображением.",
                reply_markup=get_inline_back_button()
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке контактной информации: {e}")
        await message.answer(
            "Произошла ошибка при сохранении контакта.",
            reply_markup=get_inline_back_button()
        )

    await state.clear()

    
@router.message(lambda message: message.text == "Удалить контакты")
async def handle_delete_contacts(message: Message):
    if message.from_user.id not in ALLOWED_USER_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    
    await message.answer(
        "Выберите действие:",
        reply_markup=get_delete_keyboard()
    )

@router.callback_query(lambda c: c.data == "delete_by_code")
async def handle_delete_by_code(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteContactState.waiting_for_code)
    await callback_query.message.answer("Введите код для удаления:")
    await callback_query.answer()

@router.callback_query(lambda c: c.data == "clear_database")
async def handle_clear_database(callback_query: CallbackQuery):
    if callback_query.from_user.id not in ALLOWED_USER_IDS:
        await callback_query.answer("У вас нет прав для выполнения этой команды.")
        return
    
    clear_table()
    await callback_query.message.answer("База данных очищена.")
    await callback_query.answer()

@router.message(DeleteContactState.waiting_for_code)
async def process_delete_customer(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите код.")
        return

    if not validate_code(message.text):
        await message.answer(
            "❌ Некорректный формат кода. Код должен состоять из 4 цифр.",
            reply_markup=get_inline_back_button()
        )
        return

    result = delete_user_by_code(message.text)
    await message.answer(result, reply_markup=get_inline_back_button())
    await state.clear()

@router.message(lambda message: message.text == "Список")
async def handle_list(message: Message):
    try:
        contacts = get_all_codes_with_contacts()
        if not contacts:
            await message.answer(
                "Список контактов пуст.",
                reply_markup=get_inline_back_button()
            )
            return

        # Формируем список контактов
        response = "📋 Список всех контактов:\n\n"
        for code, contact_text, chat_id in contacts:
            response += f"🔹 Код: {code}\n"
            # Проверяем текст на наличие ссылок
            text = contact_text
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            if urls:
                # Удаляем ссылки из текста и добавляем их отдельно
                for url in urls:
                    text = text.replace(url, '')
                response += f"📝 Контакт: {text.strip()}\n"
                for url in urls:
                    response += f"🔗 Ссылка: {url}\n"
            else:
                response += f"📝 Контакт: {text}\n"
            response += "\n"

        await message.answer(
            response,
            reply_markup=get_list_keyboard()
        )

    except Exception as e:
        logging.error(f"Ошибка при получении списка: {e}")
        await message.answer(
            f"Ошибка при получении списка: {str(e)}",
            reply_markup=get_inline_back_button()
        )

@router.callback_query(lambda c: c.data == "get_image")
async def process_get_image(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код изображения (4 цифры):")
    await state.set_state(GetImageState.waiting_for_code)
    await callback.answer()

@router.message(GetImageState.waiting_for_code)
async def process_image_code(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите код.")
        return

    if not validate_code(message.text):
        await message.answer(
            "❌ Некорректный формат кода. Код должен состоять из 4 цифр.",
            reply_markup=get_inline_back_button()
        )
        return

    code = message.text
    try:
        # Получаем путь к изображению по коду
        img_path = get_img_path_by_code(code)
        if img_path and os.path.isfile(img_path):
            # Отправляем только изображение
            photo = FSInputFile(img_path)
            await message.answer_photo(
                photo=photo,
                caption=f"🎯 Изображение для кода: {code}",
                reply_markup=get_inline_back_button()
            )
        else:
            await message.answer(
                "⚠️ Изображение для указанного кода не найдено.",
                reply_markup=get_inline_back_button()
            )
    except Exception as e:
        logging.error(f"Ошибка при получении изображения: {e}")
        await message.answer(
            "Произошла ошибка при получении изображения.",
            reply_markup=get_inline_back_button()
        )

    await state.clear()



@router.message(lambda message: message.photo)
async def handle_photo(message: Message, state: FSMContext):
    if message.from_user.id not in ALLOWED_USER_IDS:
        return
    
    state_data = await state.get_data()
    code = state_data.get('code')
    
    if not code:
        await message.answer("Сначала добавьте контакт, а затем отправьте фотографию.")
        return
    
    try:
        photo = message.photo[-1]
        file_id = photo.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path
        
        downloaded_file = await message.bot.download_file(file_path)
        img_path = None
        save_img_path(code, img_path)
        
        await message.answer("✅ Фотография успешно сохранена!")
        await state.clear()
    
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении фотографии: {str(e)}")
        await state.clear()

@router.callback_query(lambda c: c.data == "back_to_main")
async def process_back_to_main(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.message is None:
        return
    await state.clear()
    keyboard = get_start_keyboard(callback_query.from_user.id, ALLOWED_USER_IDS)
    await callback_query.message.answer("Выберите действие:", reply_markup=keyboard)
    await callback_query.message.delete()
    await callback_query.answer()




# Обработчики для модерации
@router.message(lambda message: message.text == "👮‍♂️ Модерация" and message.from_user.id in ALLOWED_USER_IDS)
async def handle_moderation_menu(message: Message):
    await message.answer(
        "👮‍♂️ Панель модерации\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=get_moderation_actions_keyboard()
    )

@router.callback_query(lambda c: c.data == "unmute_by_id")
async def handle_unmute_request(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🆔 Введите ID пользователя для снятия ограничений:",
        reply_markup=get_inline_back_button()
    )
    await state.set_state(ModerationStates.waiting_for_user_id)
    await callback.answer()

@router.message(ModerationStates.waiting_for_user_id)
async def process_unmute_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        if moderation.unmute_user(user_id):
            await message.answer(
                f"✅ Ограничения для пользователя с ID {user_id} успешно сняты",
                reply_markup=get_moderation_actions_keyboard()
            )
        else:
            await message.answer(
                f"ℹ️ Пользователь с ID {user_id} не имеет активных ограничений",
                reply_markup=get_moderation_actions_keyboard()
            )
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректный ID пользователя (только цифры)",
            reply_markup=get_inline_back_button()
        )
        return
    await state.clear()

@router.callback_query(lambda c: c.data == "muted_list")
async def handle_muted_list(callback: CallbackQuery):
    muted_users = moderation.get_muted_users()
    
    if not muted_users:
        await callback.message.answer(
            "📋 Список пользователей с ограничениями пуст",
            reply_markup=get_moderation_actions_keyboard()
        )
        await callback.answer()
        return

    message_text = "📋 Список пользователей с ограничениями:\n\n"
    for user in muted_users:
        message_text += (
            f"👤 ID: {user['user_id']}\n"
            f"⏳ Осталось: {user['hours_left']} часов\n"
            f"🕒 Дата окончания: {user['muted_until']}\n"
            f"🔄 Количество ограничений: {user['mute_count']}\n"
            f"{'='*30}\n"
        )

    await callback.message.answer(
        message_text,
        reply_markup=get_moderation_actions_keyboard()
    )
    await callback.answer()

# Существующие обработчики админ-панели
@router.message(lambda message: message.text == "Меню" and message.from_user.id in ALLOWED_USER_IDS)
async def admin_menu(message: Message):
    await message.answer(
        "Панель администратора.\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )

@router.callback_query(lambda c: c.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()