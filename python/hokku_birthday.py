import random
from datetime import datetime

import pandas as pd
from application import BIRTHDAYS, EMOJI, PUBLISH, TEXT, YES, HbApplication
from loguru import logger
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext

SEND_MESSAGE_RETRIES = 10


async def HokkuBirthdayJob(context: CallbackContext) -> None:
    app: HbApplication = context.application  # type: ignore
    logger.info("Start birthday job")

    _, publish_df = await app.load_dataframe(PUBLISH)
    logger.info("Loaded publish data frame")

    publish_df = publish_df.loc[publish_df["is_active"] == YES]
    if publish_df.empty:
        logger.info("No chat to publish results - quit job")
        return

    _, bdays_df = await app.load_dataframe(BIRTHDAYS)
    bdays_df["birth_date"] = bdays_df["birth_date"].apply(
        lambda date: ".".join(str(date).split(".")[:2])
    )
    logger.info("Loaded birthdays data frame")

    today = (
        datetime.today().strftime("%d.%m")
        if "debug_date" not in context.bot_data
        else context.bot_data["debug_date"]
    )
    bdays_df = bdays_df.loc[bdays_df["birth_date"] == today]
    if bdays_df.empty:
        logger.info("No birthdays for today - quit job")
        return

    num_of_birthday = bdays_df.shape[0]
    single_birthday = num_of_birthday == 1
    logger.info(f"Counted birthday for today - {num_of_birthday}")

    _, text_df = await app.load_dataframe(TEXT)

    def get_text_by_condition(condition):
        return text_df.loc[text_df["condition"] == condition].iloc[0]["text"]

    birthday_text_template: str = (
        get_text_by_condition("single_birthday")
        if single_birthday
        else get_text_by_condition("few_birthdays")
    )
    logger.info("Loaded text data frame")

    _, emoji_df = await app.load_dataframe(EMOJI)
    three_random_emoji = "".join(random.sample(emoji_df.iloc[0]["data"], 3))
    logger.info("Loaded emojis data")

    bdays_df["congratulation_name_template"] = bdays_df.apply(
        lambda row: app.congratulation_name_username
        if row["username"] != ""
        else app.congratulation_name_no_username,  # type: ignore
        axis="columns",
    )  # type: ignore
    bdays_df["congratulation_name"] = bdays_df.apply(
        lambda row: row["congratulation_name_template"].format(
            declension_name=row["declension_name"],
            username=row["username"],
        ),
        axis="columns",
    )
    bdays_df["congratulation_list_item"] = bdays_df.apply(
        lambda row: str(app.congratulation_list_item).format(
            congratulation_name=row["congratulation_name"]
        ),
        axis="columns",
    )
    logger.info("Rendered congratulation names")

    bdays_df["hokku"] = bdays_df.apply(
        lambda row: app.ya_generate_hokku(
            str(app.hokku_request).format(name=row["declension_name"], item=row["item"])
        ),
        axis="columns",
    )
    logger.info("Got hokku")

    text = _render_text(
        date=today,
        single_birthday=single_birthday,
        birthday_text_template=birthday_text_template,
        num_of_birthday=num_of_birthday,
        three_random_emoji=three_random_emoji,
        bdays_df=bdays_df,
    )
    logger.info("Rendered text")

    flatten_hokku = [
        el
        for value in bdays_df["hokku"].values.tolist()
        for arr in value.split("\n")
        for el in arr
    ]
    found_images = app.ya_search_for_image(
        str(app.image_request).format(hokku_line=random.choice(flatten_hokku))
    )
    best_images = found_images[: min(10, len(found_images))]
    logger.info(f"Got {len(best_images)} picture links")

    for iteration in range(SEND_MESSAGE_RETRIES):
        try:
            photo_link = random.choice(best_images)
            logger.info("Selected image")

            bot: Bot = app.bot
            for _, publish_s in publish_df.iterrows():
                await _send_text_and_image(
                    bot, publish_s["chat_id"], text, photo_link=photo_link
                )
            logger.info("Send message")

            break
        except BadRequest as ex:
            logger.warning(
                f"Iteration {iteration}: Got {ex.__class__} while sending message - retrying with different image\n{ex.message}"
            )
        finally:
            if iteration == SEND_MESSAGE_RETRIES - 1:
                logger.warning(
                    f"Could not send message {SEND_MESSAGE_RETRIES} times - exception"
                )
                raise Exception(f"Could not send message {SEND_MESSAGE_RETRIES} times")

    logger.info("Birthday job done")


def _render_text(
    date: str,
    single_birthday: bool,
    birthday_text_template: str,
    num_of_birthday: int,
    three_random_emoji: str,
    bdays_df: pd.DataFrame,
) -> str:
    if single_birthday:
        bday_s = bdays_df.iloc[0]
        return birthday_text_template.format(
            date=date,
            congratulation_name=bday_s["congratulation_name"],
            three_random_emoji=three_random_emoji,
            hokku=bday_s["hokku"],
            appendix=bday_s["appendix"],
        )

    return birthday_text_template.format(
        date=date,
        congratulation_count=num_of_birthday,
        three_random_emoji=three_random_emoji,
        congratulation_list="\n".join(
            bdays_df["congratulation_list_item"].values.tolist()
        ),
        hokku="\n\n".join(bdays_df["hokku"].values.tolist()),
        appendix="\n\n".join(bdays_df["appendix"].values.tolist()),
    )


async def _send_text_and_image(
    bot: Bot, chat_id: str, text: str, photo_link: str
) -> None:
    if len(text) > 1024:
        await bot.send_photo(chat_id=chat_id, photo=photo_link)
        await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN
        )
        logger.info("Send picture and text separatly")
        return

    await bot.send_photo(
        chat_id=chat_id, photo=photo_link, caption=text, parse_mode=ParseMode.MARKDOWN
    )
    logger.info("Send picture and text in one message")
