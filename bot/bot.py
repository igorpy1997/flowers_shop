import asyncio
import logging

import redis.asyncio as redis  # Використовуємо redis.asyncio замість aioredis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from Handlers.IntentClassifyHandler import IntentClassifyHandler

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

Token = ''

# Ініціалізуємо Redis клієнт з hiredis для кращої продуктивності
redis_client = redis.Redis(host="localhost", decode_responses=True)

# Використовуємо RedisStorage з TTL для стейтів (600 секунд = 10 хвилин)
storage = RedisStorage(redis=redis_client, state_ttl=600, data_ttl=600)

async def start_polling(bot, dp):
    # Запуск полінгу для бота
    await dp.start_polling(bot)


async def main() -> None:
    bot = Bot(Token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    IntentClassifyHandler(bot,dp)
    # Ініціалізація хендлерів

    await start_polling(bot, dp)


if __name__ == "__main__":
    # Запуск асинхронної програми
    asyncio.run(main())
