import datetime
import json
import logging
import os
import re

import requests
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from Handlers.GPTService import GPTService
from Services.FlowerService import FlowerService

class BouquetOrderStates(StatesGroup):
    waiting_for_bouquet_choice = State()  # Стан очікування вибору букета
    waiting_for_purchase_confirmation = State()
    waiting_for_custom_bouquet = State()  #

logger = logging.getLogger(__name__)

class FlowerCatalogHandler:
    def __init__(self):
        self.flower_service = FlowerService()
        self.gpt_service = GPTService()

    async def show_flower_catalog(self, message: types.Message, page: int = 1):
        """
        Відправляє каталог квітів з підтримкою пагінації.
        """
        per_page = 5
        flowers_response = await self.flower_service.fetch_all_flowers(page, per_page)

        if not flowers_response:
            await message.answer("Вибачте, наразі у нас немає квітів у наявності. 🌸")
            return

        flowers = self.flower_service.flowers
        total_pages = self.flower_service.get_total_pages(per_page)

        text = "🌼 Ось каталог квітів, що у нас є! 🌻🌼💛\nОберіть квітку для отримання детальної інформації:"

        builder = InlineKeyboardBuilder()
        for flower in flowers:
            builder.row(InlineKeyboardButton(text=flower['name'], callback_data=f"flower_info_{flower['id']}"))

        if page > 1:
            builder.row(InlineKeyboardButton(text="⬅️ Попередня", callback_data=f"flowers_page_{page - 1}"))
        if page < total_pages:
            builder.row(InlineKeyboardButton(text="Наступна ➡️", callback_data=f"flowers_page_{page + 1}"))

        await message.answer(text, reply_markup=builder.as_markup())



    async def check_flower_availability(self, flower_name: str, message: types.Message):
        """
        Перевіряє наявність квіток за запитом користувача та відповідає інформацією про кожну з них.
        """
        # Отримуємо всі імена квіток
        flower_names = await self.flower_service.fetch_flower_names()

        logger.info(flower_names)

        # Формуємо промпт для GPT
        prompt = (
            f"Користувач запитує про квітку '{flower_name}'. "
            f"Вибери всі квітки зі списку: {', '.join(flower_names)}, які на твою думку підходять під цей запит. "
            "Поверни лише список відповідних квіток через кому у вигляді рядка. "
            "Якщо жодна квітка не підходить, поверни порожній рядок."
        )

        # Відправка промпту до GPT
        gpt_response = await self.gpt_service.send_to_gpt(prompt)

        # Перевіряємо, чи є відповідь від GPT
        if gpt_response:
            # Парсимо відповідь GPT, припускаємо, що відповідь – це рядок із назвами квіток через кому
            flower_list = gpt_response.split(", ") if gpt_response else []

            if flower_list:
                # Якщо є відповідні квітки, надсилаємо повідомлення з підтвердженням
                await message.answer(f"🌼 Так, у нас є квіти, які ви хочете! 🌼\n"
                                     f"Ось список квітів, що підходять під ваш запит: 🌻🌼💛")

                # Проходимося по кожній квітці з отриманого списку
                for flower in flower_list:
                    flower_data = await self.flower_service.get_flower_by_name(flower)
                    relative_path = f"../back/media/flowers/{flower_data['photo']}"
                    photo_path = os.path.abspath(relative_path)
                    photo = FSInputFile(photo_path)

                    if flower_data:
                        # Відправляємо інформацію про квітку
                        await message.answer_photo(
                            photo,
                            caption=f"{flower_data['name']} - {flower_data['price']} грн 🌻\n"
                                    f"Кількість: {flower_data['quantity']} 📦\n"
                                    f"Опис: {flower_data['description']} 📜"
                        )
                    else:
                        await message.answer(f"Квітка '{flower}' не знайдена в базі.")
            else:
                # Якщо квіток не знайдено, надсилаємо повідомлення
                await message.answer(f"😔 На жаль, ми не знайшли жодних квіток за запитом '{flower_name}'.\n"
                                     "🌼 Але ви можете ознайомитися з нашим асортиментом і знайти інші чудові квіти 💐💛!")
        else:
            await message.answer("На жаль, ми не отримали відповіді від сервера. Спробуйте пізніше.")

    async def show_flower_details(self, flower_id: int, callback_query: types.CallbackQuery):
        """
        Показує детальну інформацію про квітку.
        """
        flower = await self.flower_service.get_flower_by_id(flower_id)
        if flower:
            relative_path = f"../back/media/flowers/{flower['photo']}"
            photo_path = os.path.abspath(relative_path)
            photo = FSInputFile(photo_path)

            await callback_query.message.answer_photo(
                photo,
                caption=f"{flower['name']} - {flower['price']} грн 🌹\nКількість: {flower['quantity']} 📦\nОпис: {flower['description']} 📜"
            )
        else:
            await callback_query.message.answer("На жаль, ми не маємо такої квітки в наявності. 🌸")

    async def paginate_flowers(self, callback_query: types.CallbackQuery, state):
        """
        Обробляє зміну сторінок у каталозі.
        """
        page = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()
        await self.show_flower_catalog(callback_query.message, page)

    async def flower_info_handler(self, callback_query: types.CallbackQuery):
        """
        Обробляє запит на детальну інформацію про квітку.
        """
        flower_id = int(callback_query.data.split("_")[-1])
        await self.show_flower_details(flower_id, callback_query)

    async def suggest_bouquet_options(self, message: types.Message, state: FSMContext):
        """
        Пропонує варіанти букетів на основі наявних квітів і переходить до стану очікування вибору.
        """
        available_flowers = await self.flower_service.fetch_flower_names()

        if not available_flowers:
            await message.answer("Наразі у нас немає квітів для складання букета. Вибачте за незручності. 🌸")
            return

        prompt = (
            f"Ось список доступних квітів: {', '.join(available_flowers)}. "
            "Запропонуй кілька варіантів букетів, вказуючи кількість квіток кожного виду. "
            "Наприклад: Букет 1: 3 троянди, 2 ромашки, 1 лілія."
            f"Уникай форматування GPT, тобто не роби списки з ** і додай кілька емоджі для покращення взаємодії."

        )
        logger.info(prompt)

        gpt_response = await self.gpt_service.send_to_gpt(prompt)

        if gpt_response:
            await message.answer(f"Ось кілька варіантів букетів, які ви можете замовити:\n\n{gpt_response} 💐")

            # Зберігаємо запропоновані варіанти у FSM
            await state.update_data(bouquet_options=gpt_response)

            # Переходимо до стану очікування вибору
            await state.set_state(BouquetOrderStates.waiting_for_bouquet_choice)
        else:
            await message.answer("На жаль, не вдалося отримати варіанти букетів. Спробуйте пізніше.")

    import json

    async def handle_bouquet_choice(self, message: types.Message, state: FSMContext):
        """
        Обробляє вибір користувача щодо букета і запитує підтвердження покупки разом з вартістю.
        """
        # Отримуємо дані із стану
        user_data = await state.get_data()
        bouquet_options = user_data.get("bouquet_options")

        chosen_bouquet = message.text.strip()

        # Формуємо промпт для GPT, щоб визначити, який букет вибрав користувач
        prompt = (
            f"Користувач вибрав варіант букета: '{chosen_bouquet}'. "
            "Який букет з наступних варіантів найбільш схожий на вибір користувача? "
            f"Ось варіанти: {bouquet_options}. Поверни назву вибраного букета."
        )

        # Надсилаємо запит до GPT
        gpt_response = await self.gpt_service.send_to_gpt(prompt)

        # Перевіряємо, чи GPT повернув відповідний варіант
        if gpt_response:
            chosen_bouquet = gpt_response.strip()
        else:
            await message.answer("Будь ласка, оберіть один із запропонованих варіантів букетів.")
            return

        # Зберігаємо вибір користувача
        await state.update_data(chosen_bouquet=chosen_bouquet)
        pattern = r'"назва":\s*"([^"]+)",\s*"кількість":\s*(\d+)'

        # Створюємо промпт для отримання кількості квітів для вибраного букета
        flowers_prompt = (
            f"Назва букета: {chosen_bouquet}. Поверни список квітів та кількість кожної квітки в цьому букеті у форматі JSON. "
            f"Обов'язково!Перше слово з великої букви, друге з маленької, наприклад Червона троянда"
            f"Назви квітів повертай в однині. І якщо в назві є колір він повинен залишитися в назві.Обов'язково треба щоб воно розпарсилось таким виразом {pattern}"
        )

        # Надсилаємо запит до GPT для отримання інформації про склад букета
        bouquet_flowers_response = await self.gpt_service.send_to_gpt(flowers_prompt)

        # Лог для налагодження
        logger.info(f"Raw response from GPT: '{bouquet_flowers_response}'")

        # Регулярний вираз для витягнення квітів і кількості
        matches = re.findall(pattern, bouquet_flowers_response)

        if not matches:
            await message.answer("Не вдалося знайти інформацію про квіти. Спробуйте ще раз.")
            return

        # Формуємо словник квітів
        bouquet_flowers = {name: int(quantity) for name, quantity in matches}

        # Зберігаємо склад букета в стані
        await state.update_data(bouquet_flowers=bouquet_flowers)

        # Розрахунок вартості букета через FlowerService
        flower_service = FlowerService()
        price_response = await flower_service.calculate_flower_price(bouquet_flowers)

        # Отримуємо загальну вартість з відповіді API
        total_price = price_response.get('total_price')
        if not total_price:
            await message.answer("Сталася помилка при розрахунку вартості. Спробуйте ще раз.")
            return

        # Формуємо інформацію для підтвердження покупки
        bouquet_details = ', '.join([f"{flower}: {quantity}" for flower, quantity in bouquet_flowers.items()])
        await message.answer(f"Ви обрали букет: {bouquet_details}. Загальна вартість: {total_price} грн. "
                             f"Ви впевнені, що хочете купити цей букет? (так/ні) 🌹")

        # Переходимо до стану очікування підтвердження покупки
        await state.set_state(BouquetOrderStates.waiting_for_purchase_confirmation)

    # Оновлена функція для отримання погоди
    async def get_weather(self):
        api_key = ""
        location = "Kyiv"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&lang=ua&units=metric"
        response = requests.get(url)

        if response.status_code == 200:  # Перевірка на успішний статус запиту
            weather_data = response.json()
            if "weather" in weather_data:
                logger.info(f'Weather API response: {weather_data}')
                return weather_data
            else:
                logger.error(f'Weather data does not contain "weather" key: {weather_data}')
                return None
        else:
            logger.error(f'Error fetching weather data: {response.status_code}, {response.text}')
            return None

    # Оновлена функція confirm_purchase з перевіркою на наявність погоди
    async def confirm_purchase(self, message: types.Message, state: FSMContext):
        user_response = message.text.lower()

        if user_response == "так":
            user_data = await state.get_data()
            chosen_bouquet = user_data.get("chosen_bouquet")
            bouquet_flowers = user_data.get("bouquet_flowers")

            # Запит погоди
            weather_data = await self.get_weather()
            logger.info(weather_data)
            if weather_data and "weather" in weather_data:
                current_weather = weather_data["weather"][0]["description"]

                # Перевірка погодних умов
                if "clear" in current_weather or "clouds" in current_weather:
                    delivery_cost = 50  # Вартість доставки при гарній погоді
                    delivery_time = datetime.datetime.now() + datetime.timedelta(hours=1)  # Час доставки через годину
                else:
                    delivery_cost = 100  # Вартість доставки при поганій погоді
                    delivery_time = datetime.datetime.now() + datetime.timedelta(hours=1.5)  # Час доставки через 1.5 години
            else:
                # Якщо погода не доступна, встановлюємо стандартні значення
                delivery_cost = 70  # Стандартна вартість доставки
                delivery_time = datetime.datetime.now() + datetime.timedelta(hours=1.25)  # Стандартний час доставки

            # Розрахунок загальної вартості
            flower_service = FlowerService()
            price_response = await flower_service.calculate_flower_price(bouquet_flowers)
            total_price = price_response.get('total_price', 0)
            total_cost = total_price + delivery_cost

            bouquet_details = ', '.join([f"{flower}: {quantity}" for flower, quantity in bouquet_flowers.items()])
            delivery_time_str = delivery_time.strftime("%H:%M")

            await message.answer(
                f"Ви обрали букет: {bouquet_details}. Загальна вартість: {total_price} грн. "
                f"Вартість доставки: {delivery_cost} грн. Погода: {weather_data['weather'][0]['description']} \nЗагальна сума: {total_cost} грн.\n"
                f"Час доставки: {delivery_time_str}.\n"
                f"Ви впевнені, що хочете купити цей букет? (так/ні) 🌹"
            )

            await state.set_state(BouquetOrderStates.waiting_for_purchase_confirmation)

        elif user_response == "ні":
            await message.answer("Ваше замовлення скасовано.")
            await state.clear()
        else:
            await message.answer("Будь ласка, відповідайте лише 'так' або 'ні'.")

    # Хендлер, який користувач може запускати повторно
    async def custom_bouquet_creation(self, message: types.Message, state: FSMContext):
        """
        Пропонує користувачеві список доступних квітів для самостійного складання букета.
        """
        available_flowers = await self.flower_service.fetch_flower_names()

        if not available_flowers:
            await message.answer("Наразі у нас немає квітів для складання букета. Вибачте за незручності. 🌸")
            return

        # Формуємо повідомлення з переліком квітів
        flowers_list = '🌹 ' + '\n🌸 '.join(available_flowers)  # Додаємо смайлики перед кожною квіткою
        prompt_text = (
            f"Ось список доступних квітів:\n\n{flowers_list} 🌼\n\n"
            "Напишіть, які квіти та в якій кількості ви хочете додати до свого букета.\n"
            "Наприклад: '3 🌹 троянди, 2 🌸 ромашки, 1 🌼 лілія'. 💐"
        )

        # Надсилаємо користувачу список для вибору
        await message.answer(prompt_text)

        # Переходимо до стану очікування вибору квітів
        await state.set_state(BouquetOrderStates.waiting_for_custom_bouquet)

    async def handle_custom_bouquet_choice(self, message: types.Message, state: FSMContext):
        """
        Обробляє вибір користувача щодо кастомного букета і запитує підтвердження покупки.
        """
        # Отримуємо текстовий ввід користувача (вибір квітів)
        chosen_bouquet = message.text.strip()

        # Формуємо промпт для GPT для визначення кількості і типу квітів
        pattern = r'"назва":\s*"([^"]+)",\s*"кількість":\s*(\d+)' # Регулярний вираз для отримання кількості та назви квіток
        prompt = (
            f"Назва букета: {chosen_bouquet}. Поверни список квітів та кількість кожної квітки в цьому букеті у форматі JSON. "
            f"Обов'язково!Перше слово з великої букви, друге з маленької, наприклад Червона троянда"
            f"Назви квітів повертай в однині. І якщо в назві є колір він повинен залишитися в назві.Обов'язково потрібно Щоб воно розпарсилось таким виразом {pattern}"
        )

        # Надсилаємо запит до GPT
        gpt_response = await self.gpt_service.send_to_gpt(prompt)

        # Лог для відслідковування відповіді GPT
        logger.info(f"Raw response from GPT: '{gpt_response}'")

        # Використовуємо регулярний вираз для витягнення інформації про квіти і кількість
        matches = re.findall(pattern, gpt_response)

        if not matches:
            await message.answer("Не вдалося знайти інформацію про квіти. Спробуйте ще раз.")
            return

        # Формуємо словник квітів
        bouquet_flowers = {name: int(quantity) for name, quantity in matches}
        # Зберігаємо склад букета в стані
        await state.update_data(bouquet_flowers=bouquet_flowers)

        flower_service = FlowerService()
        price_response = await flower_service.calculate_flower_price(bouquet_flowers)

        # Отримуємо загальну вартість з відповіді API
        total_price = price_response.get('total_price')
        if not total_price:
            await message.answer("Сталася помилка при розрахунку вартості. Спробуйте ще раз.")
            return

        # Створюємо рядок для виведення користувачеві
        bouquet_details = ', '.join([f"{flower}: {quantity}" for flower, quantity in bouquet_flowers.items()])

        # Виводимо запит на підтвердження покупки
        await message.answer(f"Ви обрали кастомний букет: {bouquet_details}. Загальна вартість: {total_price} грн. "
                             f"Ви впевнені, що хочете купити цей букет? (так/ні) 🌹")

        # Переходимо до стану очікування підтвердження покупки
        await state.set_state(BouquetOrderStates.waiting_for_purchase_confirmation)