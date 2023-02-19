import requests
from bs4 import BeautifulSoup
from data import Flat
import re
from datetime import datetime
import db_client


PARSER_NAME = 'gohome'


def get_all_last_flats_links(page_from=0, page_to=1):
    flat_links = []
    while page_from < page_to:
        resp = requests.get(f'https://gohome.by/sale/index/{page_from*30}')
        html = BeautifulSoup(resp.content, 'html.parser')
        for a in html.find_all('a', href=True, class_='name__link'):
            flat_links.append(a['href'])
        page_from += 1
    ready_links = list(map(lambda el: 'https://gohome.by'+el, flat_links))
    print(ready_links)
    return ready_links


def enrich_links_to_flats(links):
    flats = []
    for counter, link in enumerate(links):
        resp = requests.get(link)
        html = BeautifulSoup(resp.content, 'html.parser')
        title = html.find('h1').text.strip()
        raw_price = html.find('div', class_='price big').span
        if raw_price is not None:
            price = int(re.sub('[^0-9]', '', raw_price.text.replace(' ', '')))
        else:
            price = 0

        char_sections = html.find_all('li', class_="li-feature")
        square = 0
        rooms_number = 0
        year = 0
        city = ''
        street = ''
        district = ''
        microdistrict = ''
        for section in char_sections:
            try:
                text = section.find('div', class_='name').text.strip()
                value = section.find('div', class_='description').text.strip()

                if text == 'Площадь общая:':
                    square = float(value[:-2])
                elif text == 'Комнат:':
                    rooms_number = int(value[0])
                elif text == 'Год постройки:':
                    year = int(value)
                elif text == 'Населенный пункт:':
                    city = value
                elif text == 'Улица, дом:':
                    street = value
                elif text == 'Район:':
                    district = value
                elif text == 'Микрорайон:':
                    microdistrict = value
                elif text == 'Дата обновления:':
                    try:
                        date = datetime.strptime(value, '%d.%m.%Y')
                    except Exception as e:
                        date = datetime.now()

            except Exception as e:
                continue

        description = html.find('article').p.text.strip()
        seller_number = html.find('div', class_="w-phone").text.strip()
        image_sections = html.find('div', class_="w-advertisement-images").find_all('img', class_="zlazy")
        image_links = list(map(lambda el: 'https://gohome.by'+el['data-webp'], image_sections))

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
            seller_number=seller_number,
            reference=PARSER_NAME,
            image_links=image_links
        ))
        print(f'Спаршено {counter+1} из {len(links)}')

    return flats


def save_flats(flats):
    last_id = db_client.get_last_flat_id()
    for counter, flat in enumerate(flats):
        print(f'Загружено в базу {counter+1} из {len(flats)}')
        db_client.insert_flat(flat, last_id+counter+1)


def get_last_flats(page_from=0, page_to=1):
    links = get_all_last_flats_links(page_from, page_to)
    flats = enrich_links_to_flats(links)[:3]
    save_flats(flats)


get_last_flats()

# def test():
#     resp = requests.get('https://gohome.by/ads/view/600733')
#     html = BeautifulSoup(resp.content, 'html.parser')
#     # image_sections = html.find_all('div', class_="zlazy")
#     # image_sections = html.find_all('img', class_="zlazy")
#     # image_links = list(map(lambda el: 'https://gohome.by' + el['data-webp'], image_sections))
#
#     image_sections = html.find('div', class_="w-advertisement-images").find_all('img', class_="zlazy")
#     print(len(image_sections))
#
# # enrich_links_to_flats([get_all_last_flats_links(page_from=0, page_to=1)[0]])
# test()