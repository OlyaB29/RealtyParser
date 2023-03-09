import telebot
from src.bots.config import poster_TOKEN

bot = telebot.TeleBot(token=poster_TOKEN)


def send_tg_post(chat_id, message):
    bot.send_message(chat_id, message, parse_mode="html")
