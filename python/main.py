import os, sys, dotenv
import asyncio
from loguru import logger
from zoneinfo import ZoneInfo

from telegram.ext import (
    ApplicationBuilder,
    Defaults,
    MessageHandler,
    CallbackContext
)
from telegram.ext.filters import ChatType

from application import HbApplication
from handlers import PrivateChatMessageHandler, ErrorHandler
from hokku_birhday import HokkuBirthdayJob

dotenv.load_dotenv(dotenv.load_dotenv())

TZ            = os.environ['TZ']
BOT_TOKEN     = os.environ['BOT_TOKEN']
SHEETS_LINK   = os.environ['SHEETS_LINK']
SHEETS_ACC    = os.environ['SHEETS_ACC']

if __name__ == '__main__':
    logger.info('Starting now...')
    debug = ('-D' in sys.argv)
    app: HbApplication = ApplicationBuilder() \
        .application_class(
            HbApplication,
            kwargs={
                'sheets_link':      SHEETS_LINK,
                'sheets_acc':       SHEETS_ACC,
                'schedule_jobs':    not debug,
                'birhday_callback': HokkuBirthdayJob
            }
        ) \
        .token(BOT_TOKEN) \
        .defaults(Defaults(tzinfo=ZoneInfo(TZ))) \
        .build()

    if debug:
        logger.info('Debug mode - running jobs straightaway')
        async def main() -> None:
            await app.async_init(app)
            hokku_birthday_context = CallbackContext(application=app)
            if sys.argv[-1] != '-D':
                hokku_birthday_context.bot_data['debug_date'] = sys.argv[-1]
            await HokkuBirthdayJob(hokku_birthday_context)
        asyncio.run(main())
        logger.info('Debug jobs done!')
        exit(0)

    app.add_error_handler(ErrorHandler, block=False)
    app.add_handler(MessageHandler(ChatType.PRIVATE, callback=PrivateChatMessageHandler, block=False))

    app.run_polling()
    logger.info('Done, have a greate day!')