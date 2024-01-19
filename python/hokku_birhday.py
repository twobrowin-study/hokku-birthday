from loguru import logger
import pandas as pd
from datetime import datetime

import urllib.parse
import requests
import random
import json

from yamager import Yamager

from telegram import Bot
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
from telegram.error import BadRequest

from application import (
    HbApplication,
    BIRTHDAYS,
    TEXT,
    PUBLISH,
    EMOJI,
    YES
)

API_HOKKU = 'https://boredhumans.com/api_haiku.php'

SEND_MESSAGE_RETRYS = 10

async def HokkuBirthdayJob(context: CallbackContext) -> None:
    app: HbApplication = context.application
    logger.info('Start birhday job')

    _, pubish_df = await app.load_dataframe(PUBLISH)
    logger.info('Loaded publish data frame')

    pubish_df = pubish_df.loc[pubish_df['is_active'] == YES]
    if pubish_df.empty:
        logger.info('No chat to publish results - quit job')
        return

    _, bdays_df = await app.load_dataframe(BIRTHDAYS)
    bdays_df['birth_date'] = bdays_df['birth_date'].apply(lambda date: '.'.join(str(date).split('.')[:2]))
    logger.info('Loaded birhtdays data frame')
    
    today = datetime.today().strftime('%d.%m') if 'debug_date' not in context.bot_data else context.bot_data['debug_date']
    bdays_df = bdays_df.loc[bdays_df['birth_date'] == today]
    if bdays_df.empty:
        logger.info('No birthdays for today - quit job')
        return

    num_of_birthday = bdays_df.shape[0]
    single_birthday = (num_of_birthday == 1)
    logger.info(f'Counted birthday for today - {num_of_birthday}')
    
    _, text_df = await app.load_dataframe(TEXT)
    get_text_by_condition = lambda condition: text_df.loc[text_df['condition']==condition].iloc[0]['text']
    birthday_text_template: str = get_text_by_condition('single_birthday') if single_birthday else get_text_by_condition('few_birthdays')
    logger.info('Loaded text data frame')

    _, emoji_df = await app.load_dataframe(EMOJI)
    three_random_emoji = ''.join(random.sample(emoji_df.iloc[0]['data'], 3))
    logger.info('Loaded emojies data')

    bdays_df['congratulation_name_template'] = bdays_df.apply(
        lambda row: app.congratulation_name_username if row['username'] != '' else app.congratulation_name_no_username,
        axis = 'columns'       
    )
    bdays_df['congratulation_name'] = bdays_df.apply(
        lambda row: row['congratulation_name_template'].format(
            declension_name = row['declension_name'],
            username        = row['username'].replace('_', '\\_')
        ),
        axis = 'columns'
    )
    bdays_df['congratulation_list_item'] = bdays_df.apply(
        lambda row: app.congratulation_list_item.format(congratulation_name = row['congratulation_name']),
        axis = 'columns'
    )
    logger.info('Rendered congratulation names')

    bdays_df['hokku'] = bdays_df.apply(
        lambda row: _get_hokku(app, row),
        axis = 'columns'
    )
    logger.info('Got hokkus')

    text = _render_text(single_birthday, birthday_text_template, num_of_birthday, three_random_emoji, bdays_df)
    logger.info('Rendered text')

    flatten_hokku = [el for values in bdays_df['hokku'].values.tolist() for arr in values for el in arr]
    found_images  = Yamager().search_google_images(
        app.image_request.format(hokku_line = random.choice(flatten_hokku))
    )
    best_images = found_images[:min(10,len(found_images))]
    logger.info('Got picture links')

    for iteration in range(SEND_MESSAGE_RETRYS):
        try:
            photo_link = random.choice(best_images)
            logger.info('Selected image')

            bot: Bot =  app.bot
            for _,pubish_s in pubish_df.iterrows():
                await _send_text_and_image(bot, pubish_s['chat_id'], text, photo_link)
            logger.info('Send message')

            break
        except BadRequest as ex:
            logger.warning(f'Iteration {iteration}: Got {ex.__class__} while sending message - retrying with different image')
    
    if iteration == SEND_MESSAGE_RETRYS-1:
        logger.warning(f'Could not send message {SEND_MESSAGE_RETRYS} times - exception')
        raise Exception(f'Could not send message {SEND_MESSAGE_RETRYS} times')

    logger.info('Birthday job done')

def _get_hokku(app: HbApplication, row: pd.Series) -> list[list[str]]:
    request = app.hokku_request.format(name=row['name'], item=row['item'])
    data    = urllib.parse.urlencode({'prompt': urllib.parse.quote(request)})
    responce = requests.post(
        API_HOKKU,
        data    = data,
        headers = {
            'Content-Type':    'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
            'Accept-Encoding': '*',
            'Connection':      'keep-alive', 
            'Range':           'bytes=0-2000000'
        },
    )
    if not responce.ok:
        responce.raise_for_status()
    content_dict = json.loads(responce.text)
    if content_dict['status'] != 'success':
        raise Exception('Bad hokku')
    return content_dict['output']

def _render_text(single_birthday: bool, birthday_text_template: str, num_of_birthday: int, three_random_emoji: str, bdays_df: pd.DataFrame) -> str:
    render_hokku = lambda hokku_array: '\n\n'.join(['\n'.join(x) for x in hokku_array])
    if single_birthday:
        bday_s = bdays_df.iloc[0]
        return birthday_text_template.format(
            congratulation_name = bday_s['congratulation_name'],
            three_random_emoji  = three_random_emoji,
            hokku               = render_hokku(bday_s['hokku']),
            appendix            = bday_s['appendix']
        )
    
    return birthday_text_template.format(
        congratulation_count = num_of_birthday,
        three_random_emoji   = three_random_emoji,
        congratulation_list  = '\n'.join(bdays_df['congratulation_list_item'].values.tolist()),
        hokkus               = '\n\n\n'.join(bdays_df['hokku'].apply(render_hokku).values.tolist()),
        appendixes           = '\n\n'.join(bdays_df['appendix'].values.tolist())
    )

async def _send_text_and_image(bot: Bot, chat_id: str, text: str, photo_link: str) -> None:
    if len(text) > 1024:
        await bot.send_photo(
            chat_id = chat_id,
            photo   = photo_link
        )
        await bot.send_message(
            chat_id    = chat_id,
            text       = text,
            parse_mode = ParseMode.MARKDOWN
        )
        logger.info('Send picture and text separatly')
        return
    
    await bot.send_photo(
        chat_id    = chat_id,
        photo      = photo_link,
        caption    = text,
        parse_mode = ParseMode.MARKDOWN
    )
    logger.info('Send picture and text in one message')