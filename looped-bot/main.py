import asyncio
from bot import Bot

loop = asyncio.get_event_loop()
asyncio.ensure_future(Bot.infinity_polling())
loop.run_forever()