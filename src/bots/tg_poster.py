import telebot
from config import poster_TOKEN

bot = telebot.TeleBot(poster_TOKEN)


def send_tg_post(chat_id, message):
    bot.send_message(chat_id, message, parse_mode="html")
