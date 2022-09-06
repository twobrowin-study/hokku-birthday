import telebot

# from datetime import datetime
from settings import BotToken

Bot = telebot.TeleBot(BotToken, parse_mode='Markdown')