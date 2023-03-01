import schedule
import time
from constants import USED_PARSERS
import threading
from datetime import datetime

PARSE_EVERY_MINUTES = 3


def parse_all():
    print(f'Парсинг начался: {datetime.now()}')
    for parser in USED_PARSERS:
        thread = threading.Thread(target=parser.update_with_last_flats)
        thread.start()


schedule.every(PARSE_EVERY_MINUTES).minutes.do(parse_all)

while True:
    schedule.run_pending()
    time.sleep(1)
