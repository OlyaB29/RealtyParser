from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from src.runners.constants import SUBSCRIPTION_TYPES
from src import db_client
from config import subscriber_TOKEN, UKassa_TOKEN
from loggers import sentry_logger
import logging
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('tg_subscriber')
logger.setLevel(logging.INFO)


storage = MemoryStorage()
bot = Bot(token=subscriber_TOKEN)
dp = Dispatcher(bot, storage=storage)

PRICE = types.LabeledPrice(label="Оформление подписки", amount=500 * 100)  # в копейках (руб)
PAYMENTS_TOKEN = UKassa_TOKEN


class SubDefinition(StatesGroup):
    sub_type = State()
    sub_value = State()
    sub_ok = State()
    sub_pay = State()


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
        conf_btn = types.InlineKeyboardButton(text="Подтвердить и оплатить", callback_data='ok')
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
    await message.answer('⛪ Здравствуйте, здесь вы можете оформить платную подписку на рассылку самых свежих '
                         'объявлений о продаже квартир, отобранных по вашему критерию',
                         reply_markup=create_keyboard('main'))


@dp.callback_query_handler(lambda call: call.data in [sub_type[0] for sub_type in SUBSCRIPTION_TYPES], state=SubDefinition.sub_type)
async def define_sub_type(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        sub_type = list(filter(lambda el: el[0] == call.data, SUBSCRIPTION_TYPES))[0]
        async with state.proxy() as data:
            data['type'] = sub_type
        await SubDefinition.next()
        await bot.send_message(
            chat_id=call.message.chat.id,
            text=sub_type[2]
        )


@dp.message_handler(state=SubDefinition.sub_value)
async def define_sub_value(message: types.Message, state: FSMContext):
    if message.text == "/start":
        await start_bot(message)
        await state.finish()
    else:
        stop = False
        async with state.proxy() as data:
            if data['type'][0] == 'price':
                try:
                    value = float(message.text)
                except (Exception, ValueError) as error:
                    logger.exception(f'{error}. (Price value is uncorrect).\n')
                    await message.answer("Введите стоимость цифрами")
                    stop = True
            if not stop:
                data['value'] = message.text.title()
                to_send_message = 'Вы выбрали подписку ' + data['type'][1] + ': ' + data['value'] + \
                              '\n\nЕсли все верно, подтвердите'
                await SubDefinition.next()
                await message.answer(to_send_message, reply_markup=create_keyboard('confirm'), parse_mode='html')


@dp.callback_query_handler(lambda call: call.data == 'ok', state=SubDefinition.sub_ok)
async def pay_sub(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        await SubDefinition.next()
        if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
            await bot.send_message(call.message.chat.id, "Тестовый платеж!!!")
        async with state.proxy() as data:
            await bot.send_invoice(call.message.chat.id,
                                   title="Активация подписки на бота",
                                   description="Подписка на рассылку объявлений о продаже квартир " + data['type'][1] +
                                               ': ' + data['value'],
                                   provider_token=PAYMENTS_TOKEN,
                                   currency="rub",
                                   photo_url="https://novostroev.ru/upload/iblock/4df/investicii_s_chego_nachat.jpg",
                                   photo_width=416,
                                   photo_height=234,
                                   photo_size=416,
                                   is_flexible=False,
                                   prices=[PRICE],
                                   start_parameter="one-month-subscription",
                                   payload="test-invoice-payload")


@dp.callback_query_handler(lambda call: True, state='*')
async def keyboard_answer(call: types.CallbackQuery, state: FSMContext):
    if call.message:
        await bot.answer_callback_query(call.id)
        if call.data == "subs":
            await state.finish()
            await SubDefinition.sub_type.set()
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='👇 Выберите тип подписки',
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
                    text='👇 Выберите подписку, от которой хотите отказаться',
                    reply_markup=create_keyboard('your_subs', subs))
        elif call.data.isdigit():
            db_client.delete_subscriber(int(call.data))
            logger.info(f'Deleting subscriber {call.data}, user {call.message.chat.id}')
            await bot.send_message(
                chat_id=call.message.chat.id,
                text='Подписка удалена',
            )


@dp.pre_checkout_query_handler(lambda query: True, state=SubDefinition.sub_pay)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=types.message.ContentType.SUCCESSFUL_PAYMENT, state=SubDefinition.sub_pay)
async def successful_payment(message: types.Message, state: FSMContext):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    async with state.proxy() as data:
        data['tg_id'] = message.chat.id
        data['type'] = data['type'][0]
        db_client.add_subscription(data)
        logger.info(f'Making subscription ({data["type"]} {data["value"]})')
    await bot.send_message(message.chat.id, f"Платеж на сумму {message.successful_payment.total_amount // 100}"
                                            f" {message.successful_payment.currency} прошел успешно!\nПодписка оформлена!!")
    await state.finish()


if __name__ == "__main__":
    # executor.start_polling(dp, skip_updates=False)
    def execute_task(application, task_name):
        with newrelic.agent.BackgroundTask(application, name=task_name, group='Task'):
            executor.start_polling(dp, skip_updates=False)

    execute_task(newrelic.agent.register_application(timeout=0.2), "subscribe")

