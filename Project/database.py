import sqlite3
def init_database(conn):
    cursor = conn.cursor()
    cursor.executescript(
    '''
        
    CREATE TABLE IF NOT EXISTS category (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        color TEXT NOT NULL,
        is_income BOOLEAN NOT NULL 
    );
    
    CREATE TABLE IF NOT EXISTS "transaction" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount DOUBLE NOT NULL,
        date DATE NOT NULL,
        description TEXT,
        category_id INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES category (id)
    );
    
    ''')


def setup_defaults(conn):
    cursor = conn.cursor()

    # Výchozí kategorie
    default_categories = [
        ('Jídlo', 'ff5733', 0),
        ('Bydlení', '33ff57', 0),
        ('Výplata', '3357ff', 1),
        ('Ostatní', 'cccccc', 0)
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO category (name, color, is_income) 
        VALUES (?, ?, ?)
    ''', default_categories)

    conn.commit()