from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests
import requests.packages.urllib3
import base64
from config import BOT_TOKEN, ADMIN_ID
from keyboards import get_user_kb, get_orders_keyboard, get_admin_kb
from balance_api import get_balance
from database import Database

requests.packages.urllib3.disable_warnings()

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
db = Database()

class OrderStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_count = State()

class BroadcastState(StatesGroup):
    waiting_for_message = State()

def encode_url_to_base64(url):
    return base64.b64encode(url.encode()).decode()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    if message.from_user.id in ADMIN_ID:
        await message.reply("Добро пожаловать в админ-панель!", reply_markup=get_admin_kb())
    else:
        await message.reply("Добро пожаловать!", reply_markup=get_user_kb())

@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        return
    users_count = await db.get_users_count()
    await callback.message.answer(f"Всего пользователей: {users_count}")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_balance")
async def admin_balance_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        return
    api_token = "hh6j:AZVmDZUiAAjvLnIpvUynblC"
    balance = await get_balance(api_token)
    await callback.message.answer(balance)
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_ID:
        return
    await BroadcastState.waiting_for_message.set()
    await callback.message.answer("Введите сообщение для рассылки:")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "create_order")
async def create_order_callback(callback: types.CallbackQuery):
    if callback.from_user.id in ADMIN_ID:
        return
    can_create = await db.can_create_order(callback.from_user.id)
    if not can_create:
        await callback.message.answer("Вы уже сделали заказ ранее. Ожидайте")
        return
    await OrderStates.waiting_for_url.set()
    await callback.message.answer("Отправьте ссылку на видео TikTok:")
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "my_orders")
async def show_orders_callback(callback: types.CallbackQuery):
    if callback.from_user.id in ADMIN_ID:
        return
    orders = await db.get_user_orders(callback.from_user.id)
    if not orders:
        await callback.message.answer("У вас пока нет заказов")
        return

    await callback.message.answer(
        "Ваши заказы:",
        reply_markup=get_orders_keyboard(orders)
    )
    await callback.answer()

@dp.message_handler(state=BroadcastState.waiting_for_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_ID:
        return

    users = await db.get_all_users()
    success_count = 0

    for user_id in users:
        try:
            await bot.send_message(user_id, message.text)
            success_count += 1
        except Exception:
            continue

    await message.answer(f"Рассылка завершена!\nДоставлено: {success_count} из {len(users)}")
    await state.finish()

@dp.message_handler(state=OrderStates.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_ID:
        return
    async with state.proxy() as data:
        data['url'] = message.text
    await OrderStates.waiting_for_count.set()
    await message.reply("Укажите количество просмотров (минимум 10, максимум 100):")

@dp.message_handler(state=OrderStates.waiting_for_count)
async def process_count(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_ID:
        return
    try:
        count = int(message.text)
        if count > 100:
            await message.reply("Вы превысили лимит просмотров для накрутки. Минимальное и максимальное количество 100.")
            return
        if count < 10:
            await message.reply("Количество просмотров должно быть не менее 10!")
            return

        async with state.proxy() as data:
            url = data['url']
            encoded_url = encode_url_to_base64(url)

            api_token = "hh6j:AZVmDZUiAAjvLnIpvUynblC"
            post_data = {
                "action": "mytasks-add",
                "platform": "tiktok",
                "type": "view",
                "href": encoded_url,
                "count": count,
                "coin": 1,
                "token": api_token
            }

            headers = {
                "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.00; Windows NT 5.0)",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(
                "https://api.clifl.com/",
                data=post_data,
                headers=headers,
                verify=False
            )

            result = response.json()
            if result['status'] == 'success':
                order_id = result['id']
                await db.add_order(message.from_user.id, order_id, url)
                await message.reply(f"Заказ создан успешно!\n\nАйди заказа: {order_id}")
            else:
                await message.reply("Ошибка при создании заказа")

    except ValueError:
        await message.reply("Пожалуйста, введите корректное число!")
    except Exception as e:
        await message.reply("Произошла ошибка при создании заказа.")
    finally:
        await state.finish()

@dp.callback_query_handler(lambda c: c.data == "my_limit")
async def check_limit_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in ADMIN_ID:
        return
    can_create = await db.can_create_order(callback_query.from_user.id)
    if can_create:
        await callback_query.message.answer("Вам доступен 1 заказ на данный момент")
    else:
        await callback_query.message.answer("Вам не доступны заказы на данный момент")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('orders_offset_'))
async def process_orders_offset(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in ADMIN_ID:
        return
    offset = int(callback_query.data.split('_')[2])
    orders = await db.get_user_orders(callback_query.from_user.id, offset)
    await callback_query.message.edit_reply_markup(
        reply_markup=get_orders_keyboard(orders, offset)
    )

if __name__ == '__main__':
    from aiogram import executor
    async def on_startup(dp):
        await db.create_tables()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
