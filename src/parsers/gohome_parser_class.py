from src.parsers.base_parser import BaseParser
import re
from datetime import datetime
from loggers import sentry_logger
import logging
import traceback
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('gohome_parser')
logger.setLevel(logging.INFO)


class GohomeParser(BaseParser):
    def __init__(self, page_from=1, page_to=2, n=30):
        super().__init__('gohome', 'https://gohome.by/sale/index/', 'name__link', page_from - 1, page_to - 1, n)

    def get_ready_links(self):
        flat_links = self.get_all_last_flats_links()
        ready_links = list(map(lambda el: 'https://gohome.by' + el, flat_links))
        return ready_links

    def get_flat_characteristics(self, html, characteristics, counter):
        try:
            characteristics['title'] = html.find('h1').text.strip()
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the title of flat {counter + 1}).\n')

        try:
            raw_price = html.find('div', class_='price big').span
            if raw_price is not None:
                characteristics['price'] = int(re.sub('[^0-9]', '', raw_price.text.replace(' ', '')))
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the price of flat {counter + 1}).\n')

        try:
            char_sections = html.find_all('li', class_="li-feature")
            for section in char_sections:
                try:
                    text = section.find('div', class_='name').text.strip()
                    value = section.find('div', class_='description').text.strip()
                    if text == 'Площадь общая:':
                        characteristics['square'] = float(value[:-2])
                    elif text == 'Комнат:':
                        characteristics['rooms_number'] = int(value[0])
                    elif text == 'Год постройки:':
                        characteristics['year'] = int(value)
                    elif text == 'Населенный пункт:':
                        characteristics['city'] = value
                    elif text == 'Улица, дом:':
                        characteristics['street'] = value
                    elif text == 'Район:':
                        characteristics['district'] = value
                    elif text == 'Микрорайон:':
                        characteristics['microdistrict'] = value
                    elif text == 'Дата обновления:':
                        try:
                            characteristics['date'] = datetime.strptime(value, '%d.%m.%Y')
                        except Exception as e:
                            logger.exception(
                                f'{e}. (Search for the date of flat {counter + 1}).\n')
                            characteristics['date'] = datetime.now()
                except Exception as e:
                    continue
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the characters of flat {counter + 1}).\n')

        try:
            characteristics['description'] = html.find('article').p.text.strip()
        except Exception as e:
            logger.exception(
                f'{e}. (Search for a description of flat {counter + 1}).\n')
        try:
            characteristics['seller_number'] = html.find('div', class_="w-phone").text.strip()
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the seller_number of flat {counter + 1}).\n')
        try:
            image_sections = html.find('div', class_="w-advertisement-images").find_all('img', class_="zlazy")
            characteristics['image_links'] = list(map(lambda el: 'https://gohome.by' + el['data-webp'], image_sections))
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the image links of flat {counter + 1}).\n')

        return characteristics

# get_last_flats()
