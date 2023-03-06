import telebot
from telebot import types
from src.runners.constants import SUBSCRIPTION_TYPES
from src import db_client

# http://t.me/newflats_subscriber_bot
bot = telebot.TeleBot('токен')

subscription = {}


def create_keyboard(k, subs=None):
    if subs is None:
        subs = []
    keyboard = types.InlineKeyboardMarkup()

    if k == 'main':
        subscribe_btn = types.InlineKeyboardButton(text="Оформить подписку", callback_data='subs')
        unsubscribe_btn = types.InlineKeyboardButton(text="Отказаться от подписки", callback_data='unsubs')
        keyboard.add(subscribe_btn)
        keyboard.add(unsubscribe_btn)
    elif k == 'types':
        for sub_type in SUBSCRIPTION_TYPES:
            type_btn = types.InlineKeyboardButton(text=sub_type[1], callback_data=sub_type[0])
            keyboard.add(type_btn)
    elif k == 'confirm':
        conf_btn = types.InlineKeyboardButton(text="Подтвердить", callback_data='ok')
        back_btn = types.InlineKeyboardButton(text="Выбрать другую подписку", callback_data='subs')
        keyboard.add(conf_btn)
        keyboard.add(back_btn)
    elif k == 'your_subs':
        for sub in subs:
            sub_name = list(filter(lambda el: el[0] == sub[1], SUBSCRIPTION_TYPES))[0][1]
            sub_btn = types.InlineKeyboardButton(text=sub_name + ': ' + sub[2], callback_data=sub[0])
            keyboard.add(sub_btn)
    return keyboard


@bot.message_handler(commands=['start'])
def start_bot(message):
    subscription.clear()
    subscription['type'] = ''
    subscription['value'] = ''
    subscription['tg_id'] = ''
    bot.send_message(message.chat.id, '⛪ Здравствуйте, здесь вы можете оформить подписку на рассылку самых свежих '
                                      'объявлений о продаже квартир, отобранных по вашему критерию',
                     reply_markup=create_keyboard('main'))


@bot.callback_query_handler(func=lambda call: True)
def keyboard_answer(call):
    if call.message:
        if call.data == "subs":
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Выберите тип подписки',
                reply_markup=create_keyboard('types'))
        elif call.data in [sub_type[0] for sub_type in SUBSCRIPTION_TYPES]:
            sub_type = list(filter(lambda el: el[0] == call.data, SUBSCRIPTION_TYPES))[0]
            mess = bot.send_message(
                chat_id=call.message.chat.id,
                text=sub_type[2]
            )
            bot.register_next_step_handler(mess, sub_definition, sub_type)
        elif call.data == "ok":
            subscription['tg_id'] = call.message.chat.id
            db_client.add_subscription(subscription)
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Отлично, подписка оформлена!'
            )
        elif call.data == "unsubs":
            subs = db_client.get_subscriptions_by_tg_id(call.message.chat.id)
            if not len(subs):
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text='У вас нет действующих подписок',
                    reply_markup=create_keyboard('main'))
            else:
                bot.send_message(
                    chat_id=call.message.chat.id,
                    text='Выберите подписку, от которой хотите отказаться',
                    reply_markup=create_keyboard('your_subs', subs))
        else:
            db_client.delete_subscriber(int(call.data))
            bot.send_message(
                chat_id=call.message.chat.id,
                text='Подписка удалена',
            )


@bot.message_handler(content_types=['text'])
def sub_definition(message, sub_type):
    if message.text == "/start":
        start_bot(message)
    else:
        sub_value = message.text.title()
        to_send_message = 'Вы выбрали подписку ' + sub_type[1] + ': ' + sub_value + '\n\nЕсли все верно, подтвердите'
        bot.send_message(message.chat.id, to_send_message, reply_markup=create_keyboard('confirm'), parse_mode='html')
        subscription['type'] = sub_type[0]
        subscription['value'] = sub_value


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
