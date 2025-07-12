import sqlite3
from typing import Optional, Tuple, List
import os

class Database:
    def __init__(self):
        self.db_file = "sql/database.db"
        self.conn = None
        self.setup()

    def setup(self):
        """Initialize database connection and create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_file)
        cursor = self.conn.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create user_levels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Create level_rewards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS level_rewards (
                level INTEGER PRIMARY KEY,
                reward_description TEXT NOT NULL,
                role_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_levels_level ON user_levels(level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_levels_xp ON user_levels(xp)')

        self.conn.commit()

    def get_user_level(self, user_id: str) -> Optional[Tuple[int, int]]:
        """Get user's level and XP"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT xp, level FROM user_levels WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def update_user_level(self, user_id: str, xp: int, level: int):
        """Update user's level and XP"""
        cursor = self.conn.cursor()
        
        # First ensure user exists
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username)
            VALUES (?, ?)
        ''', (user_id, f"User {user_id}"))
        
        # Then update or insert level data
        cursor.execute('''
            INSERT INTO user_levels (user_id, xp, level)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            xp = excluded.xp,
            level = excluded.level,
            updated_at = CURRENT_TIMESTAMP
        ''', (user_id, xp, level))
        
        self.conn.commit()

    def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, int, int]]:
        """Get top users by level and XP"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, xp, level 
            FROM user_levels
            ORDER BY level DESC, xp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close() 