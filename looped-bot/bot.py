from telebot.async_telebot import AsyncTeleBot

from datetime import datetime
from settings import BotToken

Bot = AsyncTeleBot(BotToken, parse_mode='Markdown')

@Bot.message_handler()
async def no_reaction_handler(message):
    print("\n{}: Got message".format(datetime.now()))
    print(message)
    await Bot.send_message(message.chat.id, """
На таких петушар как ты я не реагирую!
    """)