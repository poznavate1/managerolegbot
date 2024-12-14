from aiogram import Router, Bot
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.keyboards import (
    get_start_keyboard, get_inline_back_button,
    get_help_keyboard, get_list_keyboard
)
from states.states import EnterCodeState
from dp_manager import get_contacts_by_code, get_img_path_by_code
from utils import moderation
from config import ALLOWED_USER_IDS, BOT_TOKEN
import os
import logging

router = Router()
bot = Bot(token=BOT_TOKEN)

def validate_code(code: str) -> bool:
    """Проверяет, что код состоит ровно из 4 цифр."""
    return bool(code and code.isdigit() and len(code) == 4)

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = get_start_keyboard(message.from_user.id, ALLOWED_USER_IDS)
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "🔍 Для поиска информации используйте кнопку «Ввести код»\n"
        "❓ Если у вас возникли вопросы, нажмите «Помощь»",
        reply_markup=keyboard
    )

@router.message(lambda message: message.text == "Ввести код")
async def handle_enter_code(message: Message, state: FSMContext):
    # Проверяем, не в муте ли пользователь
    if moderation.is_muted(message.from_user.id):
        return

    await state.set_state(EnterCodeState.waiting_for_code)
    await message.answer(
        "🔢 Введите 4-значный код:",
        reply_markup=get_inline_back_button()
    )

@router.message(EnterCodeState.waiting_for_code)
async def process_code_input(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите код.")
        return

    # Проверяем, не в муте ли пользователь
    if moderation.is_muted(message.from_user.id):
        return

    if not validate_code(message.text):
        # Увеличиваем счетчик неудачных попыток
        should_mute, attempts_left = moderation.increment_attempts(message.from_user.id)
        
        if should_mute:
            mute_info = moderation.mute_user(message.from_user.id)
            await message.answer(
                f"🚫 Доступ временно ограничен\n\n"
                f"В связи с превышением количества неудачных попыток, "
                f"доступ к боту ограничен на {mute_info['duration_hours']} час(ов).\n\n"
                f"⏳ Ограничение будет снято: {mute_info['muted_until'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await state.clear()
            return
        else:
            await message.answer(
                f"❌ Некорректный формат кода. Код должен состоять из 4 цифр.\n"
                f"⚠️ Осталось попыток: {attempts_left}",
                reply_markup=get_inline_back_button()
            )
            return

    code = message.text
    try:
        contact_data = get_contacts_by_code(code)
        if not contact_data:
            # Увеличиваем счетчик неудачных попыток при неверном коде
            should_mute, attempts_left = moderation.increment_attempts(message.from_user.id)
            
            if should_mute:
                mute_info = moderation.mute_user(message.from_user.id)
                await message.answer(
                    f"🚫 Доступ временно ограничен\n\n"
                    f"В связи с превышением количества неудачных попыток, "
                    f"доступ к боту ограничен на {mute_info['duration_hours']} час(ов).\n\n"
                    f"⏳ Ограничение будет снято: {mute_info['muted_until'].strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await state.clear()
                return
            else:
                await message.answer(
                    f"❌ Код не найден в базе данных.\n"
                    f"⚠️ Осталось попыток: {attempts_left}",
                    reply_markup=get_inline_back_button()
                )
                return

        # Если код верный, сбрасываем счетчик попыток
        if message.from_user.id in moderation.muted_users:
            moderation.muted_users[message.from_user.id]["attempts"] = 0

        message_id, chat_id = contact_data
        # Копируем оригинальное сообщение
        await bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=chat_id,
            message_id=int(message_id),
            reply_markup=get_inline_back_button()
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error processing code {code}: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке кода. Пожалуйста, попробуйте позже.",
            reply_markup=get_inline_back_button()
        )
        await state.clear()

@router.message(lambda message: message.text == "Помощь")
async def handle_help(message: Message):
    # Проверяем, не в муте ли пользователь
    if moderation.is_muted(message.from_user.id):
        return

    help_text = """
ℹ️ Помощь по использованию бота:

1️⃣ Для поиска информации нажмите кнопку «Ввести код» и введите 4-значный код
2️⃣ После ввода кода вы получите всю доступную информацию
3️⃣ Если у вас возникли вопросы или проблемы, воспользуйтесь кнопкой связи с поддержкой 👇
"""
    await message.answer(help_text, reply_markup=get_help_keyboard())

@router.callback_query(lambda c: c.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = get_start_keyboard(callback.from_user.id, ALLOWED_USER_IDS)
    await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    await callback.answer()

@router.message()
async def handle_unknown_message(message: Message):
    # Проверяем, не в муте ли пользователь
    if moderation.is_muted(message.from_user.id):
        return

    keyboard = get_start_keyboard(message.from_user.id, ALLOWED_USER_IDS)
    await message.answer(
        "❓ Пожалуйста, используйте доступные команды из меню:",
        reply_markup=keyboard
    )