import telebot

# http://t.me/newflats_poster_bot
bot = telebot.TeleBot('6276931272:AAHTZRpY_xmi0GWo6QAnjI_n4P6L0oU7LQI')
# https://t.me/+IhhOzPbh7jg4Y2Ey группа NewFlats group
REPORT_GROUP_ID = '-1001821427441'


def send_tg_post(chat_id, message):
    bot.send_message(chat_id, message, parse_mode="html")
