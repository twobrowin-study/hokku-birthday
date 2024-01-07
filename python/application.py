from asyncio import Queue
from typing import Any, Callable, Coroutine
from telegram.ext import Application, CallbackContext
from telegram.ext._basepersistence import BasePersistence
from telegram.ext._baseupdateprocessor import BaseUpdateProcessor
from telegram.ext._contexttypes import ContextTypes
from telegram.ext._updater import Updater
from telegram.ext._utils.types import CCT, JobCallback

from telegram import Bot

import os, sys
import json
import pandas as pd
from loguru import logger
from datetime import datetime

import gspread_asyncio
from google.oauth2.service_account import Credentials 

SWITCH    = 'Switch'
BIRTHDAYS = 'Birthdays'
TEXT      = 'Text'
SETTINGS  = 'Settings'
PUBLISH   = 'Publish'
EMOJI     = 'Emoji'

YES  = 'yes'
DONE = 'done'

class HbApplication(Application):
    def __init__(
            self, *,
            bot: Any, update_queue: Queue[object],
            updater: Updater | None, job_queue: Any,
            update_processor: BaseUpdateProcessor,
            persistence: BasePersistence | None,
            context_types: ContextTypes,
            post_init: Callable[[Application], Coroutine[Any, Any, None]] | None,
            post_shutdown: Callable[[Application], Coroutine[Any, Any, None]] | None,
            post_stop: Callable[[Application], Coroutine[Any, Any, None]] | None,
            sheets_link: str, sheets_acc: str,
            schedule_jobs: bool, birhday_callback: JobCallback[CCT]):
        post_init = self.async_init
        super().__init__(
            bot=bot, update_queue=update_queue,
            updater=updater, job_queue=job_queue,
            update_processor=update_processor, persistence=persistence,
            context_types=context_types, post_init=post_init,
            post_shutdown=post_shutdown, post_stop=post_stop
        )
        self.sheets_link      = sheets_link
        self.sheets_acc       = sheets_acc
        self.schedule_jobs    = schedule_jobs
        self.birhday_callback = birhday_callback
    
    async def open_sheets(self) -> None:
        def get_creds() -> Credentials:
            sheets_acc_json = json.loads(self.sheets_acc.replace('\n', '\\n'))
            creds = Credentials.from_service_account_info(sheets_acc_json)
            scoped = creds.with_scopes([
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ])
            return scoped

        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.agc  = await self.agcm.authorize()
        self.sh   = await self.agc.open_by_url(self.sheets_link)
    
    async def load_dataframe(self, wks_name: str) -> tuple[gspread_asyncio.AsyncioGspreadWorksheet, pd.DataFrame]:
        wks     = await self.sh.worksheet(wks_name)
        records = await wks.get_all_records()
        return wks, pd.DataFrame(records)

    def get_from_settings(self, key: str) -> str|int|None:
        if self.settings_df is None:
            return None
        selector    = (self.settings_df['key'] == key)
        selected_df = self.settings_df.loc[selector]
        if selected_df.empty:
            return None
        return selected_df.iloc[0]['value']

    async def async_init(self, application: Application) -> None:
        await self.open_sheets()
        logger.info('Opened sheets')
        
        self.settings_wks, self.settings_df  = await self.load_dataframe(SETTINGS)
        self.reload_every_s                  = self.get_from_settings('reload_every_s')
        self.admin_chat_id                   = self.get_from_settings('admin_chat_id')
        self.scheldue_birthday               = self.get_from_settings('scheldue_birthday')
        self.congratulation_name_username    = self.get_from_settings('congratulation_name_username')
        self.congratulation_name_no_username = self.get_from_settings('congratulation_name_no_username')
        self.congratulation_list_item        = self.get_from_settings('congratulation_list_item')
        self.image_request                   = self.get_from_settings('image_request')
        self.hokku_request                   = self.get_from_settings('hokku_request')
        self.request_responce                = self.get_from_settings('request_responce')
        logger.info('Loaded settings df')

        if self.schedule_jobs:
            self.job_queue.run_repeating(self.reload_job, interval=int(self.reload_every_s))
            logger.info(f'Scheduled reload job every {self.reload_every_s}s')

            scheldue_birthday_time = datetime.strptime(self.scheldue_birthday, '%H:%M').time()
            self.job_queue.run_daily(self.birhday_callback, time=scheldue_birthday_time)
            logger.info(f"Scheduled birthday job daily everyday at {scheldue_birthday_time}")
    
    async def reload_job(self, context: CallbackContext) -> None:
        logger.info('Start reload job')

        await self.open_sheets()
        logger.info('Reopened sheets')

        switch_wks, switch_df  = await self.load_dataframe(SWITCH)
        logger.info('Loaded switch df')

        to_reload = (switch_df.iloc[0]['reload'] == YES)
        if not to_reload:
            logger.info('Done reload job - nothing to do')
            return

        reload_cell_row = switch_df.loc[switch_df['reload'] == YES].index.values[0] + 2
        reload_cell_col = switch_df.columns.get_loc('reload') + 1

        await switch_wks.update_cell(reload_cell_row, reload_cell_col, DONE)
        logger.info('Set reload status to done - we will reload soon')

        logger.info((
            f'Restarting now '
            f'sys.argv was {sys.argv} '
            f'sys.executable was {sys.executable}'
        ))
        os.execv(sys.executable, [os.path.basename(sys.executable)] + sys.argv)
    
    async def send_message_to_admin(self, text: str, parse_mode: str) -> None:
        bot: Bot = self.bot
        await bot.send_message(self.admin_chat_id, text=text, parse_mode=parse_mode)