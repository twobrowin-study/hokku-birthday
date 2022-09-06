import telebot

from datetime import datetime
from settings import BotToken

Bot = telebot.TeleBot(BotToken, parse_mode='Markdown')

@Bot.message_handler()
def no_reaction_handler(message):
    print("\n{}: Got message".format(datetime.now()))
    print(message)
    Bot.send_message(message.chat.id, """
На таких петушар как ты я не реагирую!
    """)