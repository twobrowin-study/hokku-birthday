import asyncio
import logging

from bot import Bot

if __name__ == "__main__":
    print("Well, starting night cock...")
    asyncio.run(Bot.infinity_polling(timeout=1, logger_level=logging.INFO))