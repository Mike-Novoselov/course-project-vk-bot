import psycopg2 as pg
from config import host, user, password, db_name

with pg.connect(
        user=user,  
        password=password,  
        database=db_name  
        ) as conn:
    
    conn.autocommit = True


def create_table_viewed():  
    """функция создает таблицу viewed в базе данных"""
    with conn.cursor() as cursor:
        cursor.execute("""CREATE TABLE IF NOT EXISTS viewed(id serial, id_vk varchar(50) PRIMARY KEY);""")


def insert_data_viewed(id_vk):
    """функция вставляет данные в таблицу viewed"""
    with conn.cursor() as cursor:
        cursor.execute(f"""INSERT INTO viewed (id_vk)VALUES (%s)""", (id_vk,))


def check():
    """функция выполняет запрос к таблице viewed и возвращает все значения столбца id_vk в виде списка"""
    with conn.cursor() as cursor:
        cursor.execute(f"""SELECT sp.id_vk FROM viewed AS sp;""")
        return cursor.fetchall()


def delete_table_viewed():
    """функция удаляет таблицу viewed из базы данных"""
    with conn.cursor() as cursor:
        cursor.execute("""DROP TABLE  IF EXISTS viewed CASCADE;""")


create_table_viewed()
print("База данных создана!")

