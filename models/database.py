import sqlite3
import os
import time
from typing import Optional
from astrbot.api import logger
from ..data.initial_data import FISH_DATA, BAIT_DATA, ROD_DATA, ACCESSORY_DATA

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
                platform TEXT NOT NULL DEFAULT 'unknown',
                group_id TEXT,
                nickname TEXT NOT NULL,
                gold INTEGER DEFAULT 100,
                exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                fishing_count INTEGER DEFAULT 0,
                total_fish_weight REAL DEFAULT 0,
                total_income INTEGER DEFAULT 0,
                last_fishing_time INTEGER DEFAULT 0,
                auto_fishing BOOLEAN DEFAULT FALSE,
                total_fishing_count INTEGER DEFAULT 0,
                total_coins_earned INTEGER DEFAULT 0,
                fish_pond_capacity INTEGER DEFAULT 50,
                current_bait_id INTEGER,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')

        # 鱼类模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fish_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rarity INTEGER NOT NULL,  -- 1-5星
                base_value INTEGER NOT NULL,
                min_weight INTEGER NOT NULL,
                max_weight INTEGER NOT NULL,
                icon_url TEXT
            )
        ''')

        # 鱼竿模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rod_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rarity INTEGER NOT NULL,  -- 1-5星
                source TEXT NOT NULL,  -- shop, gacha
                purchase_cost INTEGER,
                quality_mod REAL DEFAULT 1.0,
                quantity_mod REAL DEFAULT 1.0,
                rare_mod REAL DEFAULT 0.0,
                durability INTEGER,
                icon_url TEXT
            )
        ''')

        # 饰品模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accessory_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rarity INTEGER NOT NULL,  -- 1-5星
                slot_type TEXT NOT NULL,
                quality_mod REAL DEFAULT 1.0,
                quantity_mod REAL DEFAULT 1.0,
                rare_mod REAL DEFAULT 0.0,
                coin_mod REAL DEFAULT 1.0,
                other_desc TEXT,
                icon_url TEXT
            )
        ''')

        # 鱼饵模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bait_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rarity INTEGER NOT NULL,  -- 1-5星
                effect_description TEXT,
                duration_minutes INTEGER DEFAULT 0,
                cost INTEGER NOT NULL,
                required_rod_rarity INTEGER DEFAULT 0,
                success_rate_modifier REAL DEFAULT 0.0,
                rare_chance_modifier REAL DEFAULT 0.0,
                garbage_reduction_modifier REAL DEFAULT 0.0,
                value_modifier REAL DEFAULT 1.0,
                quantity_modifier REAL DEFAULT 1.0,
                is_consumable BOOLEAN DEFAULT TRUE
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
                durability INTEGER DEFAULT 0,
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
                wipe_multiplier REAL DEFAULT 1.0,
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

        # 擦弹记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wipe_bomb_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                bet_amount INTEGER NOT NULL,
                multiplier REAL NOT NULL,
                earned_amount INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # 卡池表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gacha_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                cost_coins INTEGER DEFAULT 0,
                cost_premium_currency INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT TRUE,
                sort_order INTEGER DEFAULT 0,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')

        # 卡池物品关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gacha_pool_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,  -- 'rod', 'accessory', 'bait'
                item_template_id INTEGER NOT NULL,
                rarity INTEGER NOT NULL,
                weight INTEGER DEFAULT 100,  -- 权重，用于概率计算
                created_at INTEGER NOT NULL,
                FOREIGN KEY (pool_id) REFERENCES gacha_pools (id)
            )
        ''')

        # 卡池稀有度概率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gacha_pool_rarity_weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_id INTEGER NOT NULL,
                rarity INTEGER NOT NULL,  -- 1-5星
                weight INTEGER NOT NULL,  -- 概率权重
                created_at INTEGER NOT NULL,
                FOREIGN KEY (pool_id) REFERENCES gacha_pools (id),
                UNIQUE(pool_id, rarity)
            )
        ''')

        # 科技树表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                required_level INTEGER NOT NULL DEFAULT 1,
                required_gold INTEGER NOT NULL DEFAULT 0,
                required_tech_ids TEXT,  -- JSON格式存储前置科技ID列表
                effect_type TEXT NOT NULL,
                effect_value INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
        ''')

        # 用户科技表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                tech_id INTEGER NOT NULL,
                unlocked_at INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (tech_id) REFERENCES technologies (id),
                UNIQUE(user_id, tech_id)
            )
        ''')

        # 商店鱼竿模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_rod_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rod_template_id INTEGER NOT NULL,
                purchase_cost INTEGER,
                stock INTEGER DEFAULT 0,  -- 0表示无限库存
                enabled BOOLEAN DEFAULT TRUE,  -- 是否上架
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (rod_template_id) REFERENCES rod_templates (id),
                UNIQUE(rod_template_id)
            )
        ''')

        # 商店鱼饵模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_bait_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bait_template_id INTEGER NOT NULL,
                cost INTEGER,
                stock INTEGER DEFAULT 0,  -- 0表示无限库存
                enabled BOOLEAN DEFAULT TRUE,  -- 是否上架
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (bait_template_id) REFERENCES bait_templates (id),
                UNIQUE(bait_template_id)
            )
        ''')

        # 商店饰品模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_accessory_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accessory_template_id INTEGER NOT NULL,
                cost INTEGER,
                stock INTEGER DEFAULT 0,  -- 0表示无限库存
                enabled BOOLEAN DEFAULT TRUE,  -- 是否上架
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY (accessory_template_id) REFERENCES accessory_templates (id),
                UNIQUE(accessory_template_id)
            )
        ''')

        conn.commit()
        conn.close()

        # 初始化基础数据
        self._init_base_data()
        logger.info("数据库初始化完成")

    def _init_achievements_and_titles(self):
        """初始化成就和称号数据"""
        from ..data.initial_data import ACHIEVEMENT_DATA, TITLE_DATA

        # 插入成就数据
        for achievement in ACHIEVEMENT_DATA:
            # 先检查是否已存在该ID的成就
            existing = self.fetch_one(
                "SELECT id FROM achievements WHERE id = ?",
                (achievement[0],)
            )
            if not existing:
                self.execute_query(
                    """INSERT INTO achievements
                       (id, name, description, condition_type, condition_value, reward_gold, reward_exp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    achievement
                )

        # 插入称号数据
        for title in TITLE_DATA:
            # 先检查是否已存在该ID的称号
            existing = self.fetch_one(
                "SELECT id FROM titles WHERE id = ?",
                (title[0],)
            )
            if not existing:
                # TITLE_DATA格式: (id, name, description, display_format)
                # 数据库格式: (id, name, description, condition_type, condition_value)
                # 我们需要调整格式以匹配数据库表结构
                self.execute_query(
                    """INSERT INTO titles
                       (id, name, description, condition_type, condition_value)
                       VALUES (?, ?, ?, '', 0)""",
                    (title[0], title[1], title[2])
                )

    def _init_technology_data(self):
        """初始化科技树数据"""
        import json
        current_time = int(time.time())

        # 检查是否已有科技数据
        tech_count = self.fetch_one("SELECT COUNT(*) as count FROM technologies")
        if tech_count and tech_count['count'] > 0:
            # 检查是否是完整的科技数据，如果不是则重新插入
            for i in range(1, 6):
                existing_tech = self.fetch_one("SELECT id FROM technologies WHERE id = ?", (i,))
                if not existing_tech:
                    # 如果缺少某个科技，则清空并重新插入所有科技数据
                    self.execute_query("DELETE FROM technologies")
                    break
            else:
                # 如果所有科技都存在，则不重新插入
                return

        # 科技树数据
        TECHNOLOGY_DATA = [
            # 自动钓鱼科技
            (1, "自动钓鱼", "可解锁自动钓鱼功能", 2, 1000, "[]", "auto_fishing", 1, "自动钓鱼", current_time),
            # 竹制鱼竿科技
            (2, "竹制鱼竿", "可解锁竹制鱼竿的购买权限", 3, 0, "[]", "unlock_rod", 2, "竹制鱼竿", current_time),
            # 鱼饵系统科技
            (3, "鱼饵系统", "可解锁鱼饵的购买和使用权限", 5, 0, "[]", "unlock_bait", 3, "鱼饵系统", current_time),
            # 长者之竿科技
            (4, "长者之竿", "可解锁长者之竿的购买权限", 8, 0, "[]", "unlock_rod", 4, "长者之竿", current_time),
            # 冷静之竿科技
            (5, "冷静之竿", "可解锁冷静之竿的购买权限", 12, 0, "[]", "unlock_rod", 5, "冷静之竿", current_time),
            # 碳素纤维竿科技
            (6, "碳素纤维竿", "可解锁碳素纤维竿的购买权限", 20, 0, "[]", "unlock_rod", 6, "碳素纤维竿", current_time),
]

        # 插入科技数据
        for tech in TECHNOLOGY_DATA:
            self.execute_query(
                """INSERT INTO technologies
                   (id, name, description, required_level, required_gold, required_tech_ids, effect_type, effect_value, display_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                tech
            )

    def _init_base_data(self):
        """初始化基础数据"""
        fish_count = self.fetch_one("SELECT COUNT(*) as count FROM fish_templates")
        if fish_count and fish_count['count'] > 0:
            # 如果已有数据就返回
            return
        # 插入鱼类数据
        for fish in FISH_DATA:
            self.execute_query(
                """INSERT INTO fish_templates
                   (name, description, rarity, base_value, min_weight, max_weight, icon_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                fish
            )

        # 插入鱼竿数据
        for rod in ROD_DATA:
            self.execute_query(
                """INSERT INTO rod_templates
                   (name, description, rarity, source, purchase_cost, quality_mod, quantity_mod, rare_mod, durability, icon_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rod
            )

        # 插入饰品数据
        for accessory in ACCESSORY_DATA:
            self.execute_query(
                """INSERT INTO accessory_templates
                   (name, description, rarity, slot_type, quality_mod, quantity_mod, rare_mod, coin_mod, other_desc, icon_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                accessory
            )

        # 插入鱼饵数据
        for bait in BAIT_DATA:
            self.execute_query(
                """INSERT INTO bait_templates
                   (name, description, rarity, effect_description, duration_minutes, cost, required_rod_rarity,
                    success_rate_modifier, rare_chance_modifier, garbage_reduction_modifier,
                    value_modifier, quantity_modifier, is_consumable)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                bait
            )

        # 插入卡池数据
        from ..data.initial_data import GACHA_POOL_DATA, GACHA_POOL_RARITY_WEIGHTS, GACHA_POOL_ITEMS
        from ..data.initial_data import ACHIEVEMENT_DATA, TITLE_DATA
        current_time = int(time.time())

        # 插入卡池基本信息
        for pool_data in GACHA_POOL_DATA:
            self.execute_query(
                """INSERT INTO gacha_pools
                   (name, description, cost_coins, cost_premium_currency, enabled, sort_order, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                pool_data + (True, 0, current_time, current_time)
            )

            # 获取刚插入的卡池ID
            pool_result = self.fetch_one("SELECT id FROM gacha_pools WHERE name = ?", (pool_data[0],))
            if pool_result:
                pool_id = pool_result['id']

                # 插入卡池稀有度权重
                for rarity, weight in GACHA_POOL_RARITY_WEIGHTS.items():
                    self.execute_query(
                        """INSERT INTO gacha_pool_rarity_weights
                           (pool_id, rarity, weight, created_at)
                           VALUES (?, ?, ?, ?)""",
                        (pool_id, rarity, weight, current_time)
                    )

                # 插入卡池物品
                for item_config in GACHA_POOL_ITEMS:
                    if item_config[0] == pool_data[0]:  # 匹配卡池名称
                        self.execute_query(
                            """INSERT INTO gacha_pool_items
                               (pool_id, item_type, item_template_id, rarity, weight, created_at)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (pool_id, item_config[1], item_config[2], item_config[3], 100, current_time)
                        )

        # 插入成就数据
        for achievement in ACHIEVEMENT_DATA:
            # 先检查是否已存在该ID的成就
            existing = self.fetch_one(
                "SELECT id FROM achievements WHERE id = ?",
                (achievement[0],)
            )
            if not existing:
                self.execute_query(
                    """INSERT INTO achievements
                       (id, name, description, condition_type, condition_value, reward_gold, reward_exp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    achievement
                )

        # 插入称号数据 (使用TITLE_DATA格式)
        for title in TITLE_DATA:
            # 先检查是否已存在该ID的称号
            existing = self.fetch_one(
                "SELECT id FROM titles WHERE id = ?",
                (title[0],)
            )
            if not existing:
                # TITLE_DATA格式: (id, name, description, display_format)
                # 数据库格式: (id, name, description, condition_type, condition_value)
                # 我们需要调整格式以匹配数据库表结构
                self.execute_query(
                    """INSERT INTO titles
                       (id, name, description, condition_type, condition_value)
                       VALUES (?, ?, ?, '', 0)""",
                    (title[0], title[1], title[2])
                )
        self._init_achievements_and_titles()
        self._init_technology_data()

    def execute_query(self, query: str, params: tuple = ()):
        """执行查询操作（SELECT）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

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

    def execute_update(self, query: str, params: tuple = ()):
        """执行更新操作（INSERT/UPDATE/DELETE）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        conn.commit()
        conn.close()
        return rowcount