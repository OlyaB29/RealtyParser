import psycopg2
import requests
import re
from PIL import Image, ImageChops

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


def images_comparison(img1, img2):
    image_1 = Image.open(img1)
    image_2 = Image.open(img2)
    size = (400, 300)
    image_1.thumbnail(size)
    image_2.thumbnail(size)
    try:
        result = ImageChops.difference(image_1, image_2).getbbox()
    except ValueError:
        try:
            result = ImageChops.difference(image_1.convert('CMYK'), image_2.convert('CMYK')).getbbox()
        except Exception as e:
            print('Фото нельзя сравнить', e)
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


def check_flat_by_photo(flat):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            SELECT id, street FROM flats WHERE street LIKE %s and city LIKE %s''',
                        (f'%{street_format(flat.street)}%', f'%{city_format(flat.city)}%'))
            such_street_flats = cur.fetchall()
            # print(flat.street)
            # print(such_street_flats)
            if len(such_street_flats) == 0:
                insert_flat(flat)
                return

            id_list = [flat[0] for flat in such_street_flats]
            cur.execute('''
            SELECT id, flat, photo FROM photos WHERE flat in %s''', (tuple(id_list),))
            such_street_photos = cur.fetchall()

            flat_id, links_to_insert = check_photos(flat.image_links, such_street_photos, False)

            if flat_id != 0:
                such_street_photos = list(filter(lambda el: el[1] == flat_id, such_street_photos))
                links = flat.image_links[len(links_to_insert) + 1:]
                links_to_insert += check_photos(links, such_street_photos, True)[1]
                update_flat(flat, flat_id)
                for link in links_to_insert:
                    insert_photo(link, flat_id)
            else:
                insert_flat(flat)


def update_flat(flat, flat_id):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
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
                 ''', (flat.link, flat.reference, flat.price, flat.title, flat.square, flat.city, flat.street,
                       flat.district, flat.microdistrict, flat.rooms_number, flat.year, flat.description,
                       flat.seller_number, flat.date, flat_id)
                        )


def insert_flat(flat):
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
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
                 ''', (flat.link, flat.reference, flat.price, flat.title, flat.square, flat.city, flat.street,
                       flat.district, flat.microdistrict, flat.rooms_number, flat.year, flat.description,
                       flat.seller_number, flat.date)
                        )
            cur.execute('''
                SELECT id FROM flats WHERE link = %s''', (flat.link,))
            output = cur.fetchone()
            try:
                flat_id = output[0]
            except Exception as e:
                print(e, 'Квартира не найдена')

    if flat_id is not None:
        for link in flat.image_links:
            insert_photo(link, flat_id)


def insert_photo(image_link, flat_id):
    # drawing = open(file_path, 'rb').read()
    image = requests.get(image_link).content
    try:
        with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
            with conn.cursor() as cur:
                cur.execute('''
                        INSERT INTO photos (flat, link, photo) VALUES (%s, %s, %s)   
                        ON CONFLICT (link) DO NOTHING            
                         ''', (flat_id, image_link, psycopg2.Binary(image)))
    except (Exception, psycopg2.DatabaseError) as error:
        print("Ошибка добавления данных в таблицу фото", error)

#
# create_flats_table()
# create_photos_table()
