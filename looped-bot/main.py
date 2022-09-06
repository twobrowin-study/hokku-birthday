import asyncio
from bot import Bot

loop = asyncio.get_event_loop()
asyncio.ensure_future(Bot.polling(non_stop=True))
loop.run_forever()