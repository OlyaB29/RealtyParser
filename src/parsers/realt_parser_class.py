from src.parsers.base_parser import BaseParser
import re
from datetime import datetime
from loggers import sentry_logger
import logging
import traceback
import newrelic.agent

logger = logging.getLogger('realt_parser')
logger.setLevel(logging.INFO)

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')


class RealtParser(BaseParser):
    def __init__(self, page_from=1, page_to=2):
        super().__init__('realt', 'https://realt.by/sale/flats/?page=', 'teaser-title', page_from, page_to)

    def get_ready_links(self):
        flat_links = self.get_all_last_flats_links()
        ready_links = list(filter(lambda el: 'object' in el, flat_links))
        return ready_links

    def get_flat_characteristics(self, html, characteristics, counter):
        try:
            characteristics['title'] = html.find('h1', class_='order-1').text.strip()
        except Exception as e:
            try:
                characteristics['title'] = html.find('h1', class_='order-1').span.text.strip()
            except Exception as e:
                logger.exception(
                    f'{e}. (Search for the title of flat {counter + 1}).\n')

        try:
            raw_price = html.find('h2', class_='w-full')
            if raw_price is not None:
                characteristics['price'] = int(re.sub('[^0-9]', '', raw_price.text.strip()))
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the price of flat {counter + 1}).\n')

        try:
            char_sections = html.find_all('div', class_="w-1/2")
            for section in char_sections:
                try:
                    text = section.span.text.strip()
                    value_section = section.parent.contents[1]
                    if text == 'Площадь общая':
                        characteristics['square'] = float(value_section.p.text.strip()[:-3])
                    elif text == 'Количество комнат':
                        characteristics['rooms_number'] = int(value_section.p.text.strip())
                    elif text == 'Год постройки':
                        characteristics['year'] = int(value_section.p.text.strip())
                    elif text == 'Населенный пункт':
                        characteristics['city'] = value_section.a.text.strip()
                    elif text == 'Улица':
                        characteristics['street'] = value_section.a.text.strip()
                    elif text == 'Район города':
                        characteristics['district'] = value_section.a.text.strip()
                    elif text == 'Микрорайон':
                        characteristics['microdistrict'] = value_section.a.text.strip()
                except Exception as e:
                    continue
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the characters of flat {counter + 1}).\n')

        try:
            characteristics['description'] = html.find('section', class_='bg-white').text.strip()
        except Exception as e:
            logger.exception(
                f'{e}. (Search for a description of flat {counter + 1}).\n')

    # seller_number
        try:
            characteristics['date'] = datetime.strptime(html.find('span', class_='mr-1.5').text.strip(), '%d.%m.%Y')
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the date of flat {counter + 1}).\n')
            characteristics['date'] = datetime.now()

        try:
            image_sections = html.find('div', class_="swiper-wrapper").find_all('img')
            srcs = list(map(lambda el: el['src'], image_sections))
            characteristics['image_links'] = list(set(filter(lambda el: 'data' not in el, srcs)))
        except Exception as e:
            logger.exception(
                f'{e}. (Search for the image links of flat {counter + 1}).\n')

        return characteristics

# get_last_flats()
