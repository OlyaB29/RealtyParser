import psycopg2
import requests

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
                street CHARACTER VARYING(30),
                district CHARACTER VARYING(30),
                microdistrict CHARACTER VARYING(30),
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
                link CHARACTER VARYING(1000),
                photo BYTEA,
                FOREIGN KEY (flat) REFERENCES flats (id)                
                )''')


def get_last_flat_id():
    with psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST) as conn:
        with conn.cursor() as cur:
            cur.execute('''
            SELECT (ID) FROM flats''')
            try:
                last_id = cur.fetchall()[-1][0]
            except Exception as e:
                last_id = 0
    return last_id



def insert_flat(flat, flat_id):
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
        print("Error while inserting data in photos table", error)

# create_flats_table()


# create_photos_table()


