import mysql.connector

DB_NAME = 'articles_habr'
TABLE_NAME = 'articles'

connection = mysql.connector.connect(
    host='localhost',
    user='AcceptTheVoid',
    password='AcceptTheVoid',
    database=f'{DB_NAME}'
)

cursor = connection.cursor()

cursor.execute('SHOW DATABASES')
databases = [i[0] for i in cursor]

if not (DB_NAME in databases):
    cursor.execute(f'CREATE DATABASE {DB_NAME}')
    print('DB created')

cursor.execute('SHOW TABLES')
tables = [i[0] for i in cursor]

if not (TABLE_NAME in tables):
    cursor.execute(f'''
CREATE TABLE {TABLE_NAME}
(id INTEGER NOT NULL AUTO_INCREMENT, href VARCHAR(255), title TEXT, text MEDIUMTEXT, PRIMARY KEY (id))
''')
    print('Table created')

def get_cursor():
    return cursor
