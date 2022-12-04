from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes
from telegram.ext.filters import MessageFilter

from datetime import datetime
from settings import BotToken

class PrivateChatClass(MessageFilter):
    def filter(self, message: Message) -> bool:
        return message.chat.type == 'private'
PrivateChatFilter = PrivateChatClass()

async def no_reaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("\n{}: Got message from".format(datetime.now()))
    print(f"From {update.effective_user.id} aka {update.effective_user.name} in {update.effective_chat.id} witch is {update.effective_chat.title}")
    await update.message.reply_markdown("На таких петушар как ты я не реагирую!")

Bot = ApplicationBuilder().token(BotToken).build()
Bot.add_handler(MessageHandler(PrivateChatFilter, no_reaction_handler))