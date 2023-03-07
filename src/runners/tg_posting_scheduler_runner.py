import schedule
import time
from constants import USED_PARSERS, SUBSCRIPTION_TYPES, POST_EVERY_MINUTES
from src.bots.config import REPORT_GROUP_ID
from src import db_client
from src.bots import tg_poster
from datetime import datetime


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
            for subsription in subs_by_type:
                if sub_type[0] == "city":
                    posts = list(filter(lambda post: subsription[0] in post[6], all_posts))
                elif sub_type[0] == "price":
                    posts = list(filter(lambda post: post[3] / post[5] <= float(subsription[0]), all_posts))
                else:
                    posts = all_posts

                if len(posts):
                    print(f'Телеграм оповещения по {sub_type[0]} {subsription[0]} стартовали: {datetime.now()}')
                    send_messages(posts, subsription[1])

    db_client.update_is_posted_state(list(map(lambda el: el[0], all_posts)))


def send_messages(posts, chat_id_list):
    for post in posts:
        post_message = post[1]+'\n'
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


schedule.every(POST_EVERY_MINUTES).minutes.do(do_post_in_telegram)

while True:
    schedule.run_pending()
    time.sleep(1)
