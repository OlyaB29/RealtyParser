import schedule
import time
from constants import USED_PARSERS, SUBSCRIPTION_TYPES, POST_EVERY_MINUTES
from src.bots.config import REPORT_GROUP_ID
from src import db_client
from src.bots import tg_poster
from datetime import datetime
from loggers import sentry_logger
import logging
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('tg_posting')
logger.setLevel(logging.INFO)


def do_post_in_telegram():
    # print(f'Телеграм оповещения стартовали: {datetime.now()}')
    parser_names = list(map(lambda el: el.parser_name, USED_PARSERS))
    all_posts = db_client.get_all_not_posted_flats(parser_names)

    if len(all_posts):
        print(f'Телеграм оповещения общие стартовали: {datetime.now()}')
        send_messages(all_posts, [REPORT_GROUP_ID])

        for sub_type in SUBSCRIPTION_TYPES:
            subs_items = db_client.get_subscriptions(sub_type[0])
            subs_by_type = list(
                set([(item[0], tuple(map(lambda el: el[1], list(filter(lambda el: el[0] == item[0], subs_items))))) for
                     item in subs_items]))
            for subscription in subs_by_type:
                if sub_type[0] == "city":
                    posts = list(filter(lambda post: subscription[0] in post[6], all_posts))
                elif sub_type[0] == "price":
                    posts = list(filter(lambda post: post[3] / post[5] <= float(subscription[0]), all_posts))
                else:
                    posts = all_posts

                if len(posts):
                    print(f'Телеграм оповещения по {sub_type[0]} {subscription[0]} стартовали: {datetime.now()}')
                    send_messages(posts, subscription[1])
                    logger.info(f'Number of flats posted by subscription {sub_type[0]} {subscription[0]}: {len(posts)}')

    db_client.update_is_posted_state(list(map(lambda el: el[0], all_posts)))
    logger.info(f'Total number of flats posted in TG: {len(all_posts)}')


def send_messages(posts, chat_id_list):
    for post in posts:
        post_message = post[1] + '\n'
        post_message += '<b>Цена:</b>'
        if post[3] == 0:
            post_message += ' договорная\n'
        else:
            post_message += f' {post[3]} BYN\n'
        post_message += f'<b>Площадь:</b> {post[5]} м²\n\n'
        post_message += '\n'.join(post[7])
        for chat_id in chat_id_list:
            tg_poster.send_tg_post(chat_id, post_message)
            time.sleep(5)


def execute_task(application, task_name):
    with newrelic.agent.BackgroundTask(application, name=task_name, group='Task'):
        do_post_in_telegram()


def run_posting():
    execute_task(newrelic.agent.register_application(timeout=0.2), "posting")


# schedule.every(POST_EVERY_MINUTES).minutes.do(do_post_in_telegram)
schedule.every(POST_EVERY_MINUTES).minutes.do(run_posting)

while True:
    schedule.run_pending()
    time.sleep(1)
