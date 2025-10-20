import aiosqlite
import asyncio

async def create_table():
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS quiz_state (
                user_id INTEGER PRIMARY KEY,
                question_index INTEGER,
                score INTEGER DEFAULT 0
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS results (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER,
                total INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def update_quiz_index(user_id, index, score):
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute(
            'INSERT OR REPLACE INTO quiz_state (user_id, question_index, score) VALUES (?, ?, ?)',
            (user_id, index, score)
        )
        await db.commit()

async def get_quiz_index(user_id):
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT question_index, score FROM quiz_state WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result if result else (0, 0)

async def save_result(user_id, username, score, total):
    async with aiosqlite.connect('quiz_bot.db') as db:
        await db.execute(
            'INSERT OR REPLACE INTO results (user_id, username, score, total) VALUES (?, ?, ?, ?)',
            (user_id, username, score, total)
        )
        await db.commit()

async def get_stats(user_id):
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT score, total FROM results WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result if result else (0, 0)

async def get_top_players(limit=5):
    async with aiosqlite.connect('quiz_bot.db') as db:
        async with db.execute('SELECT username, score, total FROM results ORDER BY score DESC LIMIT ?', (limit,)) as cursor:
            return await cursor.fetchall()