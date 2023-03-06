import telebot

# http://t.me/newflats_poster_bot
bot = telebot.TeleBot('токен')
# https://t.me/+IhhOzPbh7jg4Y2Ey группа NewFlats group
REPORT_GROUP_ID = 'id группы'


def send_tg_post(chat_id, message):
    bot.send_message(chat_id, message, parse_mode="html")
