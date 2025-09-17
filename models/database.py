import sqlite3
import os
from typing import Optional
from astrbot.api import logger

class DatabaseManager:
    def __init__(self, db_path: str = "data/gaismanor.db"):
        # 确保data目录存在
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        return conn

    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                nickname TEXT NOT NULL,
                gold INTEGER DEFAULT 100,
                exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                fishing_count INTEGER DEFAULT 0,
                total_fish_weight REAL DEFAULT 0,
                total_income INTEGER DEFAULT 0,
                last_fishing_time INTEGER DEFAULT 0,
                auto_fishing BOOLEAN DEFAULT FALSE,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')

        # 鱼类模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fish_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity INTEGER NOT NULL,  -- 1-5星
                base_value INTEGER NOT NULL,
                description TEXT,
                catch_rate REAL DEFAULT 1.0
            )
        ''')

        # 鱼竿模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rod_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity INTEGER NOT NULL,  -- 1-5星
                description TEXT,
                price INTEGER NOT NULL,
                catch_bonus REAL DEFAULT 1.0,
                weight_bonus REAL DEFAULT 1.0
            )
        ''')

        # 饰品模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accessory_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity INTEGER NOT NULL,  -- 1-5星
                description TEXT,
                price INTEGER NOT NULL,
                effect_type TEXT,  -- 效果类型
                effect_value REAL  -- 效果值
            )
        ''')

        # 鱼饵模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bait_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rarity INTEGER NOT NULL,  -- 1-5星
                description TEXT,
                price INTEGER NOT NULL,
                catch_rate_bonus REAL DEFAULT 1.0,
                duration INTEGER DEFAULT 300  -- 持续时间(秒)
            )
        ''')

        # 用户鱼类库存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_fish_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fish_template_id INTEGER NOT NULL,
                weight REAL NOT NULL,
                value INTEGER NOT NULL,
                caught_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (fish_template_id) REFERENCES fish_templates (id)
            )
        ''')

        # 用户鱼竿实例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_rod_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                rod_template_id INTEGER NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                is_equipped BOOLEAN DEFAULT FALSE,
                acquired_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (rod_template_id) REFERENCES rod_templates (id)
            )
        ''')

        # 用户饰品实例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accessory_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                accessory_template_id INTEGER NOT NULL,
                is_equipped BOOLEAN DEFAULT FALSE,
                acquired_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (accessory_template_id) REFERENCES accessory_templates (id)
            )
        ''')

        # 用户鱼饵库存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_bait_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                bait_template_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (bait_template_id) REFERENCES bait_templates (id)
            )
        ''')

        # 钓鱼日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fishing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fish_template_id INTEGER,
                fish_weight REAL,
                fish_value INTEGER,
                rod_id INTEGER,
                bait_id INTEGER,
                success BOOLEAN NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (fish_template_id) REFERENCES fish_templates (id),
                FOREIGN KEY (rod_id) REFERENCES user_rod_instances (id),
                FOREIGN KEY (bait_id) REFERENCES user_bait_inventory (id)
            )
        ''')

        # 抽卡日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gacha_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_type TEXT NOT NULL,  -- 'rod', 'accessory', 'bait'
                item_template_id INTEGER NOT NULL,
                rarity INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 市场表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_user_id TEXT NOT NULL,
                item_type TEXT NOT NULL,  -- 'fish', 'rod', 'accessory'
                item_id INTEGER NOT NULL,  -- 对应物品的ID
                price INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY (seller_user_id) REFERENCES users (user_id)
            )
        ''')

        # 成就表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                condition_type TEXT NOT NULL,  -- 'fishing_count', 'rare_fish', etc.
                condition_value INTEGER NOT NULL,
                reward_gold INTEGER NOT NULL,
                reward_exp INTEGER NOT NULL
            )
        ''')

        # 用户成就进度表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                achievement_id INTEGER NOT NULL,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements (id)
            )
        ''')

        # 称号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value INTEGER NOT NULL
            )
        ''')

        # 用户称号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_titles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title_id INTEGER NOT NULL,
                acquired_at INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (title_id) REFERENCES titles (id)
            )
        ''')

        # 税收记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 签到记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sign_in_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,  -- YYYY-MM-DD
                streak INTEGER NOT NULL,  -- 连续签到天数
                reward_gold INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                UNIQUE(user_id, date),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

    def execute_query(self, query: str, params: tuple = ()):
        """执行查询语句"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def fetch_one(self, query: str, params: tuple = ()):
        """获取单条记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result

    def fetch_all(self, query: str, params: tuple = ()):
        """获取所有记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results