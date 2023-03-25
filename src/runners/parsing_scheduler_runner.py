import schedule
import time
from constants import USED_PARSERS, PARSE_EVERY_MINUTES
import threading
from datetime import datetime
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')


def parse_all():
    print(f'Парсинг начался: {datetime.now()}')
    for parser in USED_PARSERS:
        thread = threading.Thread(target=parser.update_with_last_flats)
        thread.start()


def execute_task(application, task_name):
    with newrelic.agent.BackgroundTask(application, name=task_name, group='Task'):
        parse_all()


def run_parsing():
    execute_task(newrelic.agent.register_application(timeout=0.2), "parsing")


# schedule.every(PARSE_EVERY_MINUTES).minutes.do(parse_all)
schedule.every(PARSE_EVERY_MINUTES).minutes.do(run_parsing)

while True:
    schedule.run_pending()
    time.sleep(1)
