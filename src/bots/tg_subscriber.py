from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from src.runners.constants import SUBSCRIPTION_TYPES
from src import db_client
from config import subscriber_TOKEN

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=subscriber_TOKEN)
dp = Dispatcher(bot, storage=storage)


class Sub_definition(StatesGroup):
    sub_type = State()
    sub_value = State()
    sub_ok = State()


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


@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    await message.answer('⛪ Здравствуйте, здесь вы можете оформить подписку на рассылку самых свежих '
                         'объявлений о продаже квартир, отобранных по вашему критерию',
                         reply_markup=create_keyboard('main'))


@dp.callback_query_handler(lambda call: True, state=Sub_definition.sub_type)
async def define_sub_type(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        if call.data in [sub_type[0] for sub_type in SUBSCRIPTION_TYPES]:
            sub_type = list(filter(lambda el: el[0] == call.data, SUBSCRIPTION_TYPES))[0]
            async with state.proxy() as data:
                data['type'] = sub_type
            await Sub_definition.next()
            await bot.send_message(
                chat_id=call.message.chat.id,
                text=sub_type[2]
            )


@dp.message_handler(state=Sub_definition.sub_value)
async def define_sub_value(message: types.Message, state: FSMContext):
    if message.text == "/start":
        await start_bot(message)
        await state.finish()
    else:
        async with state.proxy() as data:
            data['value'] = message.text.title()
            to_send_message = 'Вы выбрали подписку ' + data['type'][1] + ': ' + data['value'] + \
                              '\n\nЕсли все верно, подтвердите'
            data['type'] = data['type'][0]
            await Sub_definition.next()
            await message.answer(to_send_message, reply_markup=create_keyboard('confirm'), parse_mode='html')


@dp.callback_query_handler(lambda call: True, state=Sub_definition.sub_ok)
async def confirm_sub(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        if call.data == "ok":
            async with state.proxy() as data:
                data['tg_id'] = call.message.chat.id
                db_client.add_subscription(data)
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='Отлично, подписка оформлена!'
            )
            await state.finish()


@dp.callback_query_handler(lambda call: True, state='*')
async def keyboard_answer(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        if call.data == "subs":
            await state.finish()
            await Sub_definition.sub_type.set()
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='Выберите тип подписки',
                reply_markup=create_keyboard('types'))
        elif call.data == "unsubs":
            await state.finish()
            subs = db_client.get_subscriptions_by_tg_id(call.message.chat.id)
            if not len(subs):
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text='У вас нет действующих подписок',
                    reply_markup=create_keyboard('main'))
            else:
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text='Выберите подписку, от которой хотите отказаться',
                    reply_markup=create_keyboard('your_subs', subs))
        else:
            db_client.delete_subscriber(int(call.data))
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='Подписка удалена',
            )


if __name__ == "__main__":
    executor.start_polling(dp)
