from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from config import ADMIN_ID

def get_menu_keyboard(user_id: int):
    if user_id in ADMIN_ID:
        return get_admin_kb()
    return get_user_kb()

def get_agreement_kb():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ Согласен с правилами", callback_data="agree_rules"))
    return keyboard

def get_admin_kb():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("💰 Баланс бота", callback_data="admin_balance"),
        InlineKeyboardButton("📨 Рассылка", callback_data="admin_broadcast")
    ]
    keyboard.add(*buttons)
    return keyboard

def get_user_kb():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("📝 Создать заказ", callback_data="create_order"),
        InlineKeyboardButton("📋 Мои заказы", callback_data="my_orders"),
        InlineKeyboardButton("⏳ Мой лимит", callback_data="my_limit"),
    ]
    keyboard.add(*buttons)
    return keyboard

def get_orders_keyboard(orders, offset=0):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for order in orders:
        date = datetime.fromisoformat(order[0]).strftime('%d.%m.%Y')
        keyboard.add(
            InlineKeyboardButton(
                f"📅 {date} - ID: {order[1]}",
                callback_data=f"order_{order[1]}"
            )
        )

    nav_buttons = []
    if offset > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"orders_offset_{offset - 10}"))
    if len(orders) == 10:
        nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"orders_offset_{offset + 10}"))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    return keyboard