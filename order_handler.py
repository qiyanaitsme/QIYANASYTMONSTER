from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import requests
import requests.packages.urllib3
import base64

requests.packages.urllib3.disable_warnings()


class OrderStates(StatesGroup):
    waiting_for_url = State()
    waiting_for_count = State()


def encode_url_to_base64(url):
    return base64.b64encode(url.encode()).decode()


async def start_order(callback: types.CallbackQuery):
    await OrderStates.waiting_for_url.set()
    await callback.message.answer("Отправьте ссылку на видео TikTok:")


async def process_url(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['url'] = message.text
    await OrderStates.waiting_for_count.set()
    await message.reply("Укажите количество просмотров (только 100):")


async def process_count(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 10:
            await message.reply("Количество просмотров должно быть только 100!")
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
            await message.reply(f"Заказ создан успешно!\nРезультат: {result}")

    except ValueError:
        await message.reply("Пожалуйста, введите корректное число!")
    except Exception as e:
        await message.reply("Произошла ошибка при создании заказа.")
    finally:
        await state.finish()


def register_order_handlers(dp):
    dp.register_callback_query_handler(start_order, text="create_order")
    dp.register_message_handler(process_url, state=OrderStates.waiting_for_url)
    dp.register_message_handler(process_count, state=OrderStates.waiting_for_count)
