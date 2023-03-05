import schedule
import time
import requests
from src import db_client
from constants import ARCHIVE_AT
from datetime import datetime


def archive_irrelevant_flats():
    print(f'Архивирование началось: {datetime.now()}')
    flats = db_client.get_all_unarchived_flats()
    print(flats)
    flats_with_response = list(map(lambda el: (el[0], requests.get(el[1])), flats))
    flats_to_archive = list(
        filter(lambda el: el[1].status_code == 404 or (len(el[1].history) and el[1].history[0].status_code == 301),
               flats_with_response))
    db_client.update_is_archive_state(list(map(lambda el: el[0], flats_to_archive)))


schedule.every().day.at(ARCHIVE_AT).do(archive_irrelevant_flats)

while True:
    schedule.run_pending()
    time.sleep(1)
# archive_irrelevant_flats()
