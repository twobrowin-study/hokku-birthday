import asyncio
import traceback

from bot import Bot

async def bot_restart_sequence():
    while True:
        try:
            await Bot.infinity_polling()
        except asyncio.CancelledError:
            # don't interfere with cancellations
            raise
        except Exception:
            print("Caught exception")
            traceback.print_exc()

if __name__ == "__main__":
    print("Well, starting night cock...")
    asyncio.run(bot_restart_sequence())