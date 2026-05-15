import sqlite3


class DatabaseManager:
    def __init__(self, conn):
        self.conn = conn

    def add_category(self, name, color, is_income):
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            INSERT INTO category (name, color, is_income) 
            VALUES (?, ?, ?);
            ''', (name, color, is_income))
        self.conn.commit()

    def add_transaction(self, name, amount, category, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM category WHERE name = ?", (category,))
        res = cursor.fetchone()
        category_id = res[0] if res else 1

        cursor.execute(
            '''
            INSERT INTO "transaction" (amount, date, description, category_id) 
            VALUES (?, ?, ?, ?);
            ''', (amount, date, name, category_id))
        self.conn.commit()

    def select_all_from_category(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM category')
        return cursor.fetchall()

    def select_all_from_transaction(self, asc_desc="ASC", category="all"):
        if asc_desc.upper() not in ["ASC", "DESC"]:
            asc_desc = "ASC"

        cursor = self.conn.cursor()
        sql = '''
                SELECT "transaction".id, "transaction".amount, "transaction".date, "transaction".description, category.name
                FROM "transaction"
                JOIN category ON "transaction".category_id = category.id
            '''

        params = []
        if category != "all":
            sql += ' WHERE category.name = ?'
            params.append(category)

        sql += f' ORDER BY "transaction".date {asc_desc};'
        cursor.execute(sql, params)
        return cursor.fetchall()

    def sum_all(self):
        cursor = self.conn.cursor()
        cursor.execute(
            '''
            SELECT 
                IFNULL(SUM(CASE WHEN category.is_income = 1 THEN CAST("transaction".amount AS REAL) ELSE 0 END), 0) -
                IFNULL(SUM(CASE WHEN category.is_income = 0 THEN CAST("transaction".amount AS REAL) ELSE 0 END), 0)
            FROM "transaction"
            JOIN category ON "transaction".category_id = category.id;
            '''
        )
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0.0

    def sum_by_category(self):
        cursor = self.conn.cursor()
        sql = '''
            SELECT category.name, category.color, SUM(CAST("transaction".amount AS REAL))
            FROM "transaction"
            JOIN category ON "transaction".category_id = category.id
            WHERE category.is_income = 0  
            GROUP BY category.name
            HAVING SUM(CAST("transaction".amount AS REAL)) > 0
        '''
        cursor.execute(sql)
        return cursor.fetchall()

    def update_transaction(self, transaction_id, name, amount, category_name, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM category WHERE name = ?", (category_name,))
        cat_id = cursor.fetchone()[0]

        cursor.execute('''
            UPDATE "transaction" 
            SET description = ?, amount = ?, category_id = ?, date = ? 
            WHERE id = ?
        ''', (name, amount, cat_id, date, transaction_id))
        self.conn.commit()

    def delete_transaction(self, transaction_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM "transaction" WHERE id = ?', (transaction_id,))
        self.conn.commit()