import logging
from aiohttp import ClientSession
from configuration import API_URLS

logger = logging.getLogger(__name__)

class FlowerService:
    """Клас для отримання квіток з API, обробки відповідей та бізнес-логіки"""

    def __init__(self):
        self.flowers = []
        self.total_count = 0

    async def fetch_all_flowers(self, page: int, per_page: int) -> dict:
        """Отримання всіх квіток з API з пагінацією"""
        params = {'page': page, 'per_page': per_page}

        async with ClientSession() as session:
            async with session.get(API_URLS['all_flowers'], json=params) as response:
                response_text = await response.text()  # Отримуємо текстову відповідь від сервера
                if response.status == 200:
                    logger.info(f"Successfully fetched flowers on page {page}. Response: {response_text}")
                    result = await response.json()  # Повертаємо результат у форматі JSON
                    self.flowers = result.get('flowers', [])
                    self.total_count = result.get('total_flowers', 0)
                    return result
                else:
                    logger.error(f"Failed to fetch flowers on page {page}. Status: {response.status}. Response: {response_text}")
                    return {}

    async def get_flower_by_id(self, flower_id: int) -> dict:
        """
        Отримує квітку за її ID через API.
        :param flower_id: ID квітки
        :return: Квітка або None, якщо не знайдено
        """
        try:
            async with ClientSession() as session:
                async with session.get(API_URLS['flower_by_id'], json={'id': flower_id}) as response:
                    if response.status == 200:
                        logger.info(f"Successfully fetched flower with ID '{flower_id}'")
                        return await response.json()  # Повертаємо результат у форматі JSON
                    else:
                        logger.warning(f"Failed to fetch flower with ID '{flower_id}'. Status: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"An error occurred while fetching flower by ID: {e}")
            return None

    async def get_total_pages(self, per_page: int) -> int:
        """Розрахунок кількості сторінок для пагінації"""
        if per_page <= 0:
            return 0
        return (self.total_count + per_page - 1) // per_page

    async def fetch_flower_names(self) -> list:
        """Отримання лише імен всіх квіток"""
        try:
            async with ClientSession() as session:
                async with session.get(API_URLS['flower_names']) as response:
                    if response.status == 200:
                        logger.info("Successfully fetched flower names")
                        result = await response.json()
                        flowers = result.get('flower_names', [])
                        flower_names = [name for name in flowers]
                        return flower_names
                    else:
                        logger.warning(f"Failed to fetch flower names. Status: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"An error occurred while fetching flower names: {e}")
            return []

    async def get_flower_by_name(self, name: str) -> dict:
        """
        Отримує квітку за назвою через API.
        :param name: Назва квітки
        :return: Квітка або None, якщо не знайдено
        """
        try:
            async with ClientSession() as session:
                async with session.get(API_URLS['flower_by_name'], json={'name': name}) as response:
                    if response.status == 200:
                        logger.info(f"Successfully fetched flower with name '{name}'")
                        return await response.json()  # Повертаємо результат у форматі JSON
                    else:
                        logger.warning(f"Failed to fetch flower with name '{name}'. Status: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"An error occurred while fetching flower by name: {e}")
            return None

    def get_total_pages(self, per_page: int) -> int:
        """Розрахунок кількості сторінок для пагінації"""
        if per_page <= 0:
            return 0
        return (self.total_count + per_page - 1) // per_page

    async def calculate_flower_price(self, flowers: dict) -> dict:
        """
        Отримує розрахунок загальної вартості квітів за їх кількістю через API.
        :param flowers: Словник, де ключ - назва квітки, значення - кількість.
        :return: Відповідь з загальною вартістю або повідомлення про помилку.
        """
        try:
            async with ClientSession() as session:
                async with session.get(API_URLS['flower_parse_calculator'], json={'flowers': flowers}) as response:
                    if response.status == 200:
                        logger.info("Successfully calculated flower price")
                        return await response.json()  # Повертаємо результат у форматі JSON
                    else:
                        logger.warning(f"Failed to calculate flower price. Status: {response.status}")
                        return {'error': f"Failed to calculate flower price. Status: {response.status}"}
        except Exception as e:
            logger.error(f"An error occurred while calculating flower price: {e}")
            return {'error': 'An error occurred while processing the request'}


