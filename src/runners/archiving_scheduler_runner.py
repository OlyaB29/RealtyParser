import schedule
import time
import requests
from src import db_client
from constants import ARCHIVE_AT
from datetime import datetime
from loggers import sentry_logger
import logging
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('archive_logger')
logger.setLevel(logging.INFO)


def archive_irrelevant_flats():
    print(f'Архивирование началось: {datetime.now()}')
    flats = db_client.get_all_unarchived_flats()
    logger.info(f'Total unarchived flats: {len(flats)}')
    flats_with_response = list(map(lambda el: (el[0], requests.get(el[1])), flats))
    flats_to_archive = list(
        filter(lambda el: el[1].status_code == 404 or (len(el[1].history) and el[1].history[0].status_code == 301),
               flats_with_response))
    db_client.update_is_archive_state(list(map(lambda el: el[0], flats_to_archive)))
    logger.info(f'Number of flats added to the archive: {len(flats_to_archive)}')


def execute_task(application, task_name):
    with newrelic.agent.BackgroundTask(application, name=task_name, group='Task'):
        archive_irrelevant_flats()

def run_archiving():
    execute_task(newrelic.agent.register_application(timeout=0.2), "archive")

# execute_task(newrelic.agent.register_application(timeout=0.2), "archive")

# schedule.every().day.at(ARCHIVE_AT).do(archive_irrelevant_flats)
schedule.every().day.at(ARCHIVE_AT).do(run_archiving)
#
while True:
    schedule.run_pending()
    time.sleep(1)


# archive_irrelevant_flats()
