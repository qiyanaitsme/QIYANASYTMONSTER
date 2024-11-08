import aiosqlite
from datetime import datetime

class Database:
    def __init__(self, db_name='bot.db'):
        self.db_name = db_name

    async def create_tables(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    joined_date TIMESTAMP,
                    balance REAL DEFAULT 0,
                    is_agreed BOOLEAN DEFAULT FALSE
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id INTEGER,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            await db.commit()

    async def add_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)',
                (user_id, username, datetime.now())
            )
            await db.commit()

    async def set_user_agreed(self, user_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'UPDATE users SET is_agreed = TRUE WHERE user_id = ?',
                (user_id,)
            )
            await db.commit()

    async def is_user_agreed(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT is_agreed FROM users WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    async def get_users_count(self) -> int:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                result = await cursor.fetchone()
                return result[0]

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute('SELECT user_id FROM users') as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def add_order(self, user_id: int, order_id: int, url: str):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                'INSERT INTO orders (user_id, order_id, url) VALUES (?, ?, ?)',
                (user_id, order_id, url)
            )
            await db.commit()

    async def get_user_orders(self, user_id: int, offset: int = 0):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT created_at, order_id, url FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10 OFFSET ?',
                (user_id, offset)
            ) as cursor:
                return await cursor.fetchall()

    async def get_last_order_time(self, user_id: int) -> datetime:
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                'SELECT created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
                (user_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return datetime.fromisoformat(result[0]) if result else None

    async def can_create_order(self, user_id: int) -> bool:
        last_order = await self.get_last_order_time(user_id)
        if not last_order:
            return True
        time_diff = datetime.now() - last_order
        return time_diff.total_seconds() >= 86400