import requests
from bs4 import BeautifulSoup
from data import Flat
import re
from datetime import datetime
import db_client


PARSER_NAME = 'realt'


def get_all_last_flats_links(page_from=0, page_to=1):
    flat_links = []
    while page_from < page_to:
        resp = requests.get(f'https://realt.by/sale/flats/?page={page_from}')
        html = BeautifulSoup(resp.content, 'html.parser')
        for a in html.find_all('a', href=True, class_='teaser-title'):
            flat_links.append(a['href'])
        page_from += 1
    ready_links = list(filter(lambda el: 'object' in el, flat_links))
    return ready_links


def enrich_links_to_flats(links):
    flats = []
    for counter, link in enumerate(links):
        resp = requests.get(link)
        html = BeautifulSoup(resp.content, 'html.parser')
        title = html.find('h1', class_='order-1').span.text.strip()
        raw_price = html.find('h2', class_='w-full')
        if raw_price is not None:
            price = int(re.sub('[^0-9]', '', raw_price.text.strip()))
        else:
            price = 0

        char_sections = html.find_all('div', class_="w-1/2")
        square = 0
        rooms_number = 0
        year = 0
        city = ''
        street = ''
        district = ''
        microdistrict = ''
        for section in char_sections:
            try:
                text = section.span.text.strip()
                value_section = section.parent.contents[1]
                if text == 'Площадь общая':
                    square = float(value_section.p.text.strip()[:-3])
                elif text == 'Количество комнат':
                    rooms_number = int(value_section.p.text.strip())
                elif text == 'Год постройки':
                    year = int(value_section.p.text.strip())
                elif text == 'Населенный пункт':
                    city = value_section.a.text.strip()
                elif text == 'Улица':
                    street = value_section.a.text.strip()
                elif text == 'Район города':
                    district = value_section.a.text.strip()
                elif text == 'Микрорайон':
                    microdistrict = value_section.a.text.strip()
            except Exception as e:
                continue

        description = html.find('section', class_='bg-white').text.strip()

        # seller_number
        try:
            date = datetime.strptime(html.find('span', class_='mr-1.5').text.strip(), '%d.%m.%Y')
        except Exception as e:
            date = datetime.now()

        image_sections = html.find('div', class_="swiper-wrapper").find_all('img')
        srcs = list(map(lambda el: el['src'], image_sections))
        image_links = list(set(filter(lambda el: 'data' not in el, srcs)))

        flats.append(Flat(
            link=link,
            title=title,
            price=price,
            square=square,
            city=city,
            street=street,
            district=district,
            microdistrict=microdistrict,
            rooms_number=rooms_number,
            year=year,
            description=description,
            date=date,
            reference=PARSER_NAME,
            image_links=image_links
        ))
        print(f'Спаршено {counter+1} из {len(links)}')
    return flats


def save_flats(flats):

    for counter, flat in enumerate(flats):
        print(f'Загружено в базу {counter+1} из {len(flats)}')
        db_client.insert_flat(flat)


def get_last_flats(page_from=0, page_to=10):
    links = get_all_last_flats_links(page_from, 1)[:2]
    flats = enrich_links_to_flats(links)[:2]
    save_flats(flats)


# get_last_flats()


