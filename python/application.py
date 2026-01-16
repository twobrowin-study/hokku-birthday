import json
import os
import sys
from asyncio import Queue
from datetime import datetime
from typing import Any, Callable, Coroutine

import gspread_asyncio
import jwt
import pandas as pd
import yandexcloud
from google.oauth2.service_account import Credentials
from loguru import logger
from telegram import Bot
from telegram.ext import Application, CallbackContext
from telegram.ext._basepersistence import BasePersistence
from telegram.ext._baseupdateprocessor import BaseUpdateProcessor
from telegram.ext._contexttypes import ContextTypes
from telegram.ext._updater import Updater
from telegram.ext._utils.types import CCT, JobCallback
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.search_api import (
    ImageFormat,
    ImageOrientation,
    ImageSize,
    SearchType,
)

SWITCH = "Switch"
BIRTHDAYS = "Birthdays"
TEXT = "Text"
SETTINGS = "Settings"
PUBLISH = "Publish"
EMOJI = "Emoji"

YES = "yes"
DONE = "done"


class HbApplication(Application):
    def __init__(
        self,
        *,
        bot: Any,
        update_queue: Queue[object],
        updater: Updater | None,
        job_queue: Any,
        update_processor: BaseUpdateProcessor,
        persistence: BasePersistence | None,
        context_types: ContextTypes,
        post_init: Callable[[Application], Coroutine[Any, Any, None]] | None,
        post_shutdown: Callable[[Application], Coroutine[Any, Any, None]] | None,
        post_stop: Callable[[Application], Coroutine[Any, Any, None]] | None,
        sheets_link: str,
        sheets_acc: str,
        ya_cloud_folder_id: str,
        ya_search_api_acc: str,
        schedule_jobs: bool,
        birthday_callback: JobCallback[CCT],
    ):
        post_init = self.async_init
        super().__init__(
            bot=bot,
            update_queue=update_queue,
            updater=updater,
            job_queue=job_queue,
            update_processor=update_processor,
            persistence=persistence,
            context_types=context_types,
            post_init=post_init,
            post_shutdown=post_shutdown,
            post_stop=post_stop,
        )
        self.sheets_link = sheets_link
        self.sheets_acc = sheets_acc
        self.schedule_jobs = schedule_jobs
        self.birthday_callback = birthday_callback

        self.ya_cloud_ml = YCloudML(
            folder_id=ya_cloud_folder_id,
            auth=self.ya_create_iam_token(ya_search_api_acc),
        )

    def ya_create_iam_token(self, ya_search_api_acc: str) -> str:
        ya_search_api_acc_dict = json.loads(ya_search_api_acc)

        private_key = ya_search_api_acc_dict["private_key"]
        key_id = ya_search_api_acc_dict["id"]
        service_account_id = ya_search_api_acc_dict["service_account_id"]

        now = datetime.now().timestamp()
        payload = {
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            "iss": service_account_id,
            "iat": now,
            "exp": now + 3600,
        }

        encoded_jwt_token = jwt.encode(
            payload, private_key, algorithm="PS256", headers={"kid": key_id}
        )

        sa_key = {
            "id": key_id,
            "service_account_id": service_account_id,
            "private_key": private_key,
        }

        sdk = yandexcloud.SDK(service_account_key=sa_key)  # pyright: ignore[reportPrivateImportUsage]
        iam_service = sdk.client(IamTokenServiceStub)
        iam_token_response = iam_service.Create(
            CreateIamTokenRequest(jwt=encoded_jwt_token)
        )

        return iam_token_response.iam_token

    def ya_generate_hokku(
        self, hokku_request: str = "Сгенерируй хокку про Егора Дубровина"
    ) -> str:
        model: Any = self.ya_cloud_ml.models.completions("yandexgpt")
        operation: Any = model.run_deferred(
            [
                {"role": "system", "text": hokku_request},
            ]
        )

        result: Any = operation.wait()
        return result.alternatives[0].text

    def ya_search_for_image(
        self, search_request: str = "Японская живопись", docs_on_page: int = 10
    ) -> list[str]:
        search: Any = self.ya_cloud_ml.search_api.image(
            search_type=SearchType.RU,
            format=ImageFormat.JPEG,
            size=ImageSize.MEDIUM,
            orientation=ImageOrientation.HORIZONTAL,
            docs_on_page=docs_on_page,
        )
        search_result: Any = search.run(search_request, format="parsed")
        return [
            document.url
            for group in search_result.groups
            for document in group.documents
        ]

    async def open_sheets(self) -> None:
        def get_creds() -> Credentials:
            sheets_acc_json = json.loads(self.sheets_acc.replace("\n", "\\n"))
            creds = Credentials.from_service_account_info(sheets_acc_json)
            scoped = creds.with_scopes(
                [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
            )
            return scoped

        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        self.agc = await self.agcm.authorize()
        self.sh = await self.agc.open_by_url(self.sheets_link)

    async def load_dataframe(
        self, wks_name: str
    ) -> tuple[gspread_asyncio.AsyncioGspreadWorksheet, pd.DataFrame]:
        wks = await self.sh.worksheet(wks_name)
        records = await wks.get_all_records()
        return wks, pd.DataFrame(records)

    def get_from_settings(self, key: str) -> str | int | None:
        if self.settings_df is None:
            return None
        selector = self.settings_df["key"] == key
        selected_df = self.settings_df.loc[selector]
        if selected_df.empty:
            return None
        return selected_df.iloc[0]["value"]

    async def async_init(self, application: Application) -> None:
        await self.open_sheets()
        logger.info("Opened sheets")

        self.settings_wks, self.settings_df = await self.load_dataframe(SETTINGS)
        self.reload_every_s = self.get_from_settings("reload_every_s")
        self.admin_chat_id = self.get_from_settings("admin_chat_id")
        self.schedule_birthday = self.get_from_settings("schedule_birthday")
        self.congratulation_name_username = self.get_from_settings(
            "congratulation_name_username"
        )
        self.congratulation_name_no_username = self.get_from_settings(
            "congratulation_name_no_username"
        )
        self.congratulation_list_item = self.get_from_settings(
            "congratulation_list_item"
        )
        self.image_request = self.get_from_settings("image_request")
        self.hokku_request = self.get_from_settings("hokku_request")
        self.request_response = self.get_from_settings("request_response")
        logger.info("Loaded settings df")

        if self.schedule_jobs and self.job_queue:
            self.job_queue.run_repeating(
                self.reload_job, interval=int(str(self.reload_every_s))
            )
            logger.info(f"Scheduled reload job every {self.reload_every_s}s")

            schedule_birthday_time = datetime.strptime(
                str(self.schedule_birthday), "%H:%M"
            ).time()
            self.job_queue.run_daily(
                self.birthday_callback, time=schedule_birthday_time
            )
            logger.info(
                f"Scheduled birthday job daily everyday at {schedule_birthday_time}"
            )

    async def reload_job(self, context: CallbackContext) -> None:
        logger.info("Start reload job")

        await self.open_sheets()
        logger.info("Reopened sheets")

        switch_wks, switch_df = await self.load_dataframe(SWITCH)
        logger.info("Loaded switch df")

        to_reload = switch_df.iloc[0]["reload"] == YES
        if not to_reload:
            logger.info("Done reload job - nothing to do")
            return

        reload_cell_row = switch_df.loc[switch_df["reload"] == YES].index.values[0] + 2
        reload_cell_col = int(str(switch_df.columns.get_loc("reload"))) + 1

        await switch_wks.update_cell(reload_cell_row, reload_cell_col, DONE)
        logger.info("Set reload status to done - we will reload soon")

        logger.info(
            (
                f"Restarting now "
                f"sys.argv was {sys.argv} "
                f"sys.executable was {sys.executable}"
            )
        )
        os.execv(sys.executable, [os.path.basename(sys.executable)] + sys.argv)

    async def send_message_to_admin(self, text: str, parse_mode: str) -> None:
        bot: Bot = self.bot
        await bot.send_message(
            str(self.admin_chat_id), text=text, parse_mode=parse_mode
        )
