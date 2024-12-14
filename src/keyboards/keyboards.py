from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_start_keyboard(user_id: int, allowed_user_ids: list) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Ввести код")],
        [KeyboardButton(text="Помощь")]
    ]
    if user_id in allowed_user_ids:
        kb.extend([
            [KeyboardButton(text="Меню")],
            [KeyboardButton(text="👮‍♂️ Модерация")]
        ])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_inline_back_button() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ]
    )
    return keyboard

def get_list_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Получить изображение по коду", callback_data="get_image")],
            [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
        ]
    )
    return keyboard

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить контакты")],
            [KeyboardButton(text="Удалить контакты")],
            [KeyboardButton(text="Список")],
            [KeyboardButton(text="👮‍♂️ Модерация")]
        ],
        resize_keyboard=True
    )

def get_delete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить по коду", callback_data="delete_by_code")],
        [InlineKeyboardButton(text="🧹 Очистить базу данных", callback_data="clear_database")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])

def get_help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛟 Связаться со службой поддержки",
            url="https://t.me/videoprod_anchor"
        )]
    ])

def get_moderation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👮‍♂️ Модерация")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_moderation_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔓 Размутить по ID", callback_data="unmute_by_id")],
        [InlineKeyboardButton(text="📋 Список замученных", callback_data="muted_list")],
        [InlineKeyboardButton(text="🔙 Вернуться в главное меню", callback_data="back_to_main")]
    ])