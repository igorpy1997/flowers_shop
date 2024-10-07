import json
import logging
from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from .FlowerCatalogHandler import FlowerCatalogHandler, BouquetOrderStates
from .GPTService import GPTService

logger = logging.getLogger(__name__)


class IntentClassifyHandler:
    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.router = Router()
        self.dp.include_router(self.router)

        # Ініціалізація сервісів
        self.flower_catalog_handler = FlowerCatalogHandler()
        self.gpt_service = GPTService()

        # Реєстрація хендлерів
        self.router.message.register(self.intent_classify_handler, F.text)
        self.router.callback_query.register(self.flower_catalog_handler.paginate_flowers,
                                            F.data.startswith("flowers_page_"))
        self.router.callback_query.register(self.flower_catalog_handler.flower_info_handler,
                                            F.data.startswith("flower_info_"))

    async def intent_classify_handler(self, message: types.Message, state: FSMContext):
        """
        Обробник для текстових повідомлень, що використовує GPT для класифікації та відповіді.
        """
        user_message = message.text
        logger.info(f"User {message.from_user.id} sent message: {user_message}")

        # Отримання поточного стану FSM
        current_state = await state.get_state()

        # Якщо користувач знаходиться в стані вибору букета
        if current_state == BouquetOrderStates.waiting_for_bouquet_choice.state:
            # Виклик функції для обробки вибору букета
            await self.flower_catalog_handler.handle_bouquet_choice(message, state)
            return

        # Якщо користувач знаходиться в стані кастомного букета
        if current_state == BouquetOrderStates.waiting_for_custom_bouquet.state:
            # Виклик функції для обробки вибору кастомного букета
            await self.flower_catalog_handler.handle_custom_bouquet_choice(message, state)
            return

        # Якщо користувач знаходиться в стані підтвердження покупки
        if current_state == BouquetOrderStates.waiting_for_purchase_confirmation.state:
            # Виклик функції для підтвердження покупки
            await self.flower_catalog_handler.confirm_purchase(message, state)
            return

        # Якщо користувач не знаходиться в специфічному стані - продовжуємо з GPT
        dialog_data = await state.get_data()
        stage = dialog_data.get('dialog_stage', 'initial')

        # Класифікація повідомлення через GPT
        response = await self.gpt_service.gpt_classify_intent(user_message, stage)
        response_dict = json.loads(response)

        classification = str(response_dict.get('classification'))
        additional_info = response_dict.get('additional_info')
        logger.info(f"Message classified as: {classification}")

        # Обробка запитів, пов'язаних з квітами
        if classification == "9":  # Запит на асортимент
            await self.flower_catalog_handler.show_flower_catalog(message, page=1)
        elif classification == "8":  # Запит на наявність квітки
            await self.flower_catalog_handler.check_flower_availability(additional_info, message)
        elif classification in ["3", "4"]:  # Запит на допомогу або конкретний запит
            await self.flower_catalog_handler.show_flower_catalog(message, page=1)
        elif classification == "13":  # Користувач просить допомогти з підбором букета
            await self.flower_catalog_handler.suggest_bouquet_options(message, state)
        elif classification == "14":  # Користувач хоче сам зібрати букет
            await self.flower_catalog_handler.custom_bouquet_creation(message, state)
        else:
            # Генерація відповіді через GPT
            response = await self.gpt_service.gpt_generate_reply(user_message, classification, stage)
            await message.answer(response)

        # Оновлюємо стан для наступного етапу
        await state.update_data(
            last_message=user_message,
            classification=classification,
            dialog_stage="bouquet_processing" if classification == "12" else "continued"
        )