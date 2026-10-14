import asyncio
import os
import sys
from zoneinfo import ZoneInfo

import dotenv
from application import HbApplication
from handlers import ErrorHandler, PrivateChatMessageHandler
from hokku_birthday import HokkuBirthdayJob
from loguru import logger
from telegram.ext import ApplicationBuilder, CallbackContext, Defaults, MessageHandler
from telegram.ext.filters import ChatType

dotenv.load_dotenv(dotenv.find_dotenv())

TZ = os.environ["TZ"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SHEETS_LINK = os.environ["SHEETS_LINK"]
SHEETS_ACC = os.environ["SHEETS_ACC"]
YA_CLOUD_FOLDER_ID = os.environ["YA_CLOUD_FOLDER_ID"]
YA_SEARCH_API_ACC = os.environ["YA_SEARCH_API_ACC"]

if __name__ == "__main__":
    logger.info("Starting now...")
    debug = "-D" in sys.argv
    app: HbApplication = (
        ApplicationBuilder()
        .application_class(
            HbApplication,
            kwargs={
                "zoneinfo": ZoneInfo(TZ),
                "sheets_link": SHEETS_LINK,
                "sheets_acc": SHEETS_ACC,
                "ya_cloud_folder_id": YA_CLOUD_FOLDER_ID,
                "ya_search_api_acc": YA_SEARCH_API_ACC,
                "schedule_jobs": not debug,
                "birthday_callback": HokkuBirthdayJob,
            },
        )
        .token(BOT_TOKEN)
        .defaults(Defaults(tzinfo=ZoneInfo(TZ)))
        .build()
    )  # type: ignore

    if debug:
        logger.info("Debug mode - running jobs straightaway")

        async def main() -> None:
            await app.async_init(app)
            hokku_birthday_context = CallbackContext(application=app)
            if sys.argv[-1] != "-D":
                hokku_birthday_context.bot_data["debug_date"] = sys.argv[-1]
            await HokkuBirthdayJob(hokku_birthday_context)

        asyncio.run(main())
        logger.info("Debug jobs done!")
        sys.exit(0)

    app.add_error_handler(ErrorHandler, block=False)  # type: ignore
    app.add_handler(MessageHandler(ChatType.PRIVATE, callback=PrivateChatMessageHandler, block=False))

    app.run_polling()
    logger.info("Done, have a greate day!")
