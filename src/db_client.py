import psycopg2, psycopg
import requests
import re
from PIL import Image, ImageChops
from progress.bar import ChargingBar
from colorama import init, Fore
from loggers import sentry_logger
import logging
import traceback
import newrelic.agent

newrelic.agent.initialize('E:\Olya Work\\Users\oabor\PycharmProjects\RealtyParser\\newrelic.ini')

logger = logging.getLogger('db_client')
logger.setLevel(logging.INFO)

init(autoreset=True)

DBNAME = 'realty'
USER = 'postgres'
PASSWORD = 'Panterka29!'
HOST = '127.0.0.1'


def create_flats_table():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS flats(
                id serial PRIMARY KEY,
                link CHARACTER VARYING(300) UNIQUE NOT NULL,
                reference CHARACTER VARYING(30),
                price INTEGER,
                title CHARACTER VARYING(1000),
                square INTEGER,
                city CHARACTER VARYING(30),
                street CHARACTER VARYING(500),
                district CHARACTER VARYING(100),
                microdistrict CHARACTER VARYING(500),
                rooms_number INTEGER,
                year INTEGER,
                description CHARACTER VARYING(3000),
                seller_number CHARACTER VARYING(30),
                date TIMESTAMP WITH TIME ZONE
                )''')


def create_photos_table():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS photos(
                id serial PRIMARY KEY,
                flat INTEGER,
                link CHARACTER VARYING(1000) UNIQUE NOT NULL,
                photo BYTEA,
                FOREIGN KEY (flat) REFERENCES flats (id)                
                )''')


def create_subscriptions_table():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions(
                id serial PRIMARY KEY,
                selection_field CHARACTER VARYING(15),
                selection_value CHARACTER VARYING(500),
                CONSTRAINT subs_unique UNIQUE (selection_field, selection_value)        
                )''')


def create_subscribers_table():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS subscribers(
                id serial PRIMARY KEY,
                tg_id CHARACTER VARYING(20),
                sub_id INTEGER,
                FOREIGN KEY (sub_id) REFERENCES subscriptions (id)
                CONSTRAINT subs_tg_unique UNIQUE (tg_id, sub_id)                
                )''')


def images_comparison(img1, img2):
    image_1 = Image.open(img1)
    image_2 = Image.open(img2)
    size = (400, 300)
    image_1.thumbnail(size)
    image_2.thumbnail(size)
    try:
        result = ImageChops.difference(image_1, image_2).getbbox()
    except ValueError as e:
        logger.exception(
            f'{e}. (Comparing photos of different formats).\n')
        try:
            result = ImageChops.difference(image_1.convert('CMYK'), image_2.convert('CMYK')).getbbox()
        except Exception as e:
            print('Фото нельзя сравнить', e)
            logger.exception(
                f'{e}. (Uncomparable photos).\n')
            return False
    if result is None:
        return True
    else:
        return False


def street_format(street):
    street = street.split(',')[0].split('д.')[0].split('д ')[0]
    street = re.sub(
        r'(ул.|ул | ул|пер.|пер | пер|пр.|пр | пр|просп.|просп | просп|тракт | тракт|б-р|проезд | проезд|улица|переулок|проспект | проспект|пл.|пл | пл|площадь|шоссе | шоссе)',
        '', street).strip().strip('.').strip()
    return street


def city_format(city):
    city = re.sub(
        r'(г.|г |п.|п |д.|д |аг.|аг |гп.|гп )', '', city).strip()
    return city


def check_photos(links, photos, check_all):
    links_to_insert = links
    flat_id = 0
    links_not_to_insert = []
    for index, link in enumerate(links):
        image = requests.get(link).content
        with open('checked_img.jpg', 'wb') as f:
            f.write(image)

        for photo in photos:
            with open('searched_img.jpg', 'wb') as f:
                f.write(photo[2])
            is_such = images_comparison('checked_img.jpg', 'searched_img.jpg')
            if is_such and not check_all:
                flat_id = photo[1]
                links_to_insert = links[:index]
                return flat_id, links_to_insert
            elif is_such and check_all:
                links_not_to_insert.append(link)
                break

    links_to_insert = list(filter(lambda el: el not in links_not_to_insert, links_to_insert))
    return flat_id, links_to_insert


def check_flats_by_photo(flats, parser):
    flats_to_insert = []
    flats_to_update = []
    update_id_list = []
    image_links_list = []
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            bar = ChargingBar(
                f'{Fore.MAGENTA}Проверено квартир на совпадение фото в базе с сайта {Fore.BLUE} {parser} {Fore.RED}',
                fill=' ⛪️', max=len(flats), suffix='%(index)d''/%(max)d'' | %(percent)d%%')
            for flat in flats:
                cur.execute('''
                SELECT id, street FROM flats WHERE street LIKE %s and city LIKE %s and 
                    (is_archive = false or is_archive IS NULL)''',
                            (f'%{street_format(flat.street)}%', f'%{city_format(flat.city)}%'))
                such_street_flats = cur.fetchall()
                if len(such_street_flats) == 0:
                    flats_to_insert.append(flat)
                    bar.next()
                    continue

                id_list = [flat[0] for flat in such_street_flats]
                cur.execute('''
                SELECT id, flat, photo FROM photos WHERE flat in %s''', (tuple(id_list),))
                such_street_photos = cur.fetchall()

                if len(such_street_photos) == 0:
                    flats_to_insert.append(flat)
                    bar.next()
                    continue

                flat_id, links_to_insert = check_photos(flat.image_links, such_street_photos, False)

                if flat_id != 0:
                    such_street_photos = list(filter(lambda el: el[1] == flat_id, such_street_photos))
                    links = flat.image_links[len(links_to_insert) + 1:]
                    links_to_insert += check_photos(links, such_street_photos, True)[1]
                    flats_to_update.append(flat)
                    update_id_list.append(flat_id)
                    image_links_list.append(links_to_insert)
                else:
                    flats_to_insert.append(flat)
                bar.next()
            bar.finish()
    if len(flats_to_insert):
        insert_flats(flats_to_insert, parser)
    if len(flats_to_update):
        update_flats(flats_to_update, update_id_list, parser)
    if len(image_links_list):
        insert_photos(update_id_list, image_links_list, parser)


def update_flats(flats, flat_id_list, parser):
    flats_list = [
        (flat.link, flat.reference, flat.price, flat.title, flat.square, flat.city, flat.street, flat.district,
         flat.microdistrict, flat.rooms_number, flat.year, flat.description, flat.seller_number, flat.date,
         flat_id_list[counter]) for counter, flat in enumerate(flats)]
    try:
        with psycopg.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
            with conn.cursor() as cur:
                cur.executemany('''
                UPDATE flats 
                SET
                link = %s,
                reference = %s,
                price = %s,
                title = %s,
                square = %s,
                city = %s,
                street = %s,
                district = %s,
                microdistrict = %s,
                rooms_number = %s,
                year = %s,                
                description = %s,
                seller_number = %s,
                date = %s
                WHERE id = %s
                 ''', flats_list)
        logger.info(f'Number of updated flats from the site {parser}: {len(flats)}')
    except (Exception, psycopg.DatabaseError) as error:
        print("Ошибка обновления данных в таблице квартир", error)
        logger.exception(
            f'{error}. (Error updating flats from the site {parser}).\n')


def insert_flats(flats, parser):
    flats_list = [
        (flat.link, flat.reference, flat.price, flat.title, flat.square, flat.city, flat.street, flat.district,
         flat.microdistrict, flat.rooms_number, flat.year, flat.description, flat.seller_number, flat.date)
        for flat in flats]
    try:
        with psycopg.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
            with conn.cursor() as cur:
                cur.executemany('''
                INSERT INTO flats (link, reference, price, title, square, city, street, district,
                 microdistrict, rooms_number, year, description, seller_number, date) VALUES (%s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link) DO UPDATE
                SET
                link = EXCLUDED.link,
                price = EXCLUDED.price,
                title = EXCLUDED.title,
                square = EXCLUDED.square,
                city = EXCLUDED.city,
                street = EXCLUDED.street,
                district = EXCLUDED.district,
                microdistrict = EXCLUDED.microdistrict,
                rooms_number = EXCLUDED.rooms_number,
                year = EXCLUDED.year,                
                description = EXCLUDED.description,
                seller_number = EXCLUDED.seller_number,
                date = EXCLUDED.date
                RETURNING id
                 ''', flats_list, returning=True)
                id_list = [cur.fetchone()[0]]
                i = 1
                while i < len(flats_list):
                    cur.nextset()
                    id_list.append(cur.fetchone()[0])
                    i += 1
        logger.info(f'Number of inserted flats from the site {parser}: {len(flats)}')
        links_list = [flat.image_links for flat in flats]
        insert_photos(id_list, links_list, parser)
    except (Exception, psycopg.DatabaseError) as error:
        print("Ошибка добавления данных в таблицу квартир", error)
        logger.exception(
            f'{error}. (Error inserting flats from the site {parser}).\n')


def insert_photos(flat_id_list, image_links_list, parser):
    photos_list = [(flat_id_list[counter], link, psycopg.Binary(requests.get(link).content))
                   for counter, image_links in enumerate(image_links_list) for link in image_links]
    try:
        with psycopg.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
            with conn.cursor() as cur:
                cur.executemany('''
                        INSERT INTO photos (flat, link, photo) VALUES (%s, %s, %s)   
                        ON CONFLICT (link) DO NOTHING            
                         ''', photos_list)
    except (Exception, psycopg.DatabaseError) as error:
        print("Ошибка добавления данных в таблицу фото", error)
        logger.exception(
            f'{error}. (Error adding photos to the database from the site {parser}).\n')


def get_all_not_posted_flats(parser_types):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT id, link, reference, price, title, square, city FROM flats 
                    WHERE (is_tg_posted = false or is_tg_posted IS NULL)
                    AND reference IN %(parser_types)s 
                 ''',
                        {'parser_types': tuple(parser_types)}
                        )
            flats = cur.fetchall()[:10]
            flats = list(map(lambda el: list(el), flats))
            for flat in flats:
                cur.execute('''
                        SELECT flat, link FROM photos
                        WHERE flat = %s
                        LIMIT 3
                    ''', (flat[0],)
                            )
                photos = cur.fetchall()
                image_links = list(map(lambda el: el[1], photos))
                flat.append(image_links)

            return flats

    # get_all_not_posted_flats(['realt', 'gohome'])


def update_is_posted_state(id_list):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    UPDATE flats 
                    SET is_tg_posted = true
                    WHERE id = ANY(%s)
                 ''',
                        [id_list, ]
                        )


def get_all_unarchived_flats():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    SELECT id, link FROM flats 
                    WHERE (is_archive = false or is_archive IS NULL) LIMIT 10
                 ''')
            return cur.fetchall()


def update_is_archive_state(id_list):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    UPDATE flats 
                    SET is_archive = true
                    WHERE id = ANY(%s) 
                 ''',
                        [id_list, ]
                        )


def add_subscription(subscription):
    try:
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO subscriptions (selection_field, selection_value) VALUES (%s, %s)
                    ON CONFLICT (selection_field, selection_value) DO UPDATE 
                    SET 
                    selection_field=EXCLUDED.selection_field,
                    selection_value=EXCLUDED.selection_value
                    RETURNING id
                ''', (subscription['type'], subscription['value']))
                sub_id = cur.fetchone()[0]
        add_subscriber(subscription['tg_id'], sub_id)
    except (Exception, psycopg.DatabaseError) as error:
        print("Ошибка добавления данных в таблицу фото", error)
        logger.exception(f'{error}. (Error adding subscription to the database).\n')


def add_subscriber(tg_id, sub_id):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                    INSERT INTO subscribers (tg_id, sub_id) VALUES (%s, %s)
                    ON CONFLICT (tg_id, sub_id) DO NOTHING
                ''', (tg_id, sub_id))


def get_subscriptions(field):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                     SELECT selection_value, tg_id, count(tg_id) OVER (PARTITION BY subscriptions.id)
                     FROM subscriptions JOIN subscribers ON subscriptions.id=subscribers.sub_id
                     WHERE selection_field = %s                
                ''', (field,))

            return cur.fetchall()


def get_subscriptions_by_tg_id(tg_id):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                     SELECT subscribers.id, selection_field, selection_value
                     FROM subscriptions JOIN subscribers ON subscriptions.id=subscribers.sub_id
                     WHERE tg_id = %s                
                ''', (str(tg_id),))

            return cur.fetchall()


def delete_subscriber(id):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                     DELETE FROM subscribers WHERE id = %s                
                ''', (id,))

# create_flats_table()
# create_photos_table()
# create_subscriptions_table()
# create_subscribers_table()
