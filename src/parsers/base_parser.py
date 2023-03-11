from abc import ABC, abstractmethod
import requests, threading
from progress.bar import ChargingBar
from bs4 import BeautifulSoup
from datetime import datetime
from src.data import Flat
from src import db_client
from colorama import init, Fore

init(autoreset=True)

lock = threading.RLock()


class BaseParser(ABC):
    def __init__(self, parser_name, main_link, a_class, page_from=1, page_to=2, n=1):
        self.parser_name = parser_name
        self.main_link = main_link
        self.page_from = page_from
        self.page_to = page_to
        self.a_class = a_class
        self.n = n
        self.start = 0

    def get_all_last_flats_links(self):
        flat_links = []
        self.start = self.page_from
        while self.start < self.page_to:
            resp = requests.get('{}{}'.format(self.main_link, self.start * self.n))
            html = BeautifulSoup(resp.content, 'html.parser')
            for a in html.find_all('a', href=True, class_=self.a_class):
                flat_links.append(a['href'])
            self.start += 1

        return flat_links

    @abstractmethod
    def get_ready_links(self):
        return []

    @abstractmethod
    def get_flat_characteristics(self, html, characteristics):
        return {}

    def enrich_links_to_flats(self, links):
        flats = []
        bar = ChargingBar(
            f'{Fore.GREEN}Получено данных по квартирам с сайта {Fore.YELLOW} {self.parser_name} {Fore.RED}', fill='✍  ',
            max=len(links), suffix='%(index)d''/%(max)d'' | %(percent)d%%')
        for counter, link in enumerate(links):
            resp = requests.get(link)
            html = BeautifulSoup(resp.content, 'html.parser')

            characteristics = {'title': '', 'price': 0, 'square': 0, 'city': '', 'street': '', 'district': '',
                               'microdistrict': '', 'rooms_number': 0, 'year': 0, 'description': '',
                               'date': datetime.now(), 'seller_number': '', 'image_links': []}
            flat_characteristics = self.get_flat_characteristics(html, characteristics)

            flats.append(Flat(
                link=link,
                title=flat_characteristics['title'],
                price=flat_characteristics['price'],
                square=flat_characteristics['square'],
                city=flat_characteristics['city'],
                street=flat_characteristics['street'],
                district=flat_characteristics['district'],
                microdistrict=flat_characteristics['microdistrict'],
                rooms_number=flat_characteristics['rooms_number'],
                year=flat_characteristics['year'],
                description=flat_characteristics['description'],
                date=flat_characteristics['date'],
                seller_number=flat_characteristics['seller_number'],
                reference=self.parser_name,
                image_links=flat_characteristics['image_links']
            ))
            bar.next()
        bar.finish()

        return flats

    def save_flats(self, flats):
        lock.acquire()
        try:
            db_client.check_flats_by_photo(flats, self.parser_name)
        except Exception as e:
            print("Ошибка добавления данных в базу", e)
        finally:
            lock.release()

    def update_with_last_flats(self):
        links = self.get_ready_links()[:10]
        flats = self.enrich_links_to_flats(links)
        self.save_flats(flats)
