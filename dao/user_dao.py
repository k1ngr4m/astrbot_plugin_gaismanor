"""
用户数据访问对象
"""
from typing import Optional, List, Dict, Any
import time
from ..models.user import User
from ..models.database import DatabaseManager


class UserDAO:
    """用户数据访问对象，封装所有用户相关的数据库操作"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据用户ID获取用户信息"""
        result = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return User(
                user_id=result['user_id'],
                platform=result['platform'],
                group_id=result['group_id'] or "",
                nickname=result['nickname'],
                gold=result['gold'],
                exp=result['exp'],
                level=result['level'],
                fishing_count=result['fishing_count'],
                total_fish_weight=result['total_fish_weight'],
                total_income=result['total_income'],
                last_fishing_time=result['last_fishing_time'],
                auto_fishing=result['auto_fishing'],
                total_fishing_count=result['total_fishing_count'],
                total_coins_earned=result['total_coins_earned'],
                fish_pond_capacity=result['fish_pond_capacity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None

    def get_user_basic_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户基本信息（用于检查用户是否已注册）"""
        return self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    def create_user(self, user: User) -> bool:
        """创建新用户"""
        try:
            self.db.execute_query(
                """INSERT INTO users (user_id, platform, group_id, nickname, gold, exp, level, fishing_count,
                                      total_fish_weight, total_income, last_fishing_time,
                                      auto_fishing, total_fishing_count, total_coins_earned, fish_pond_capacity,
                                      created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user.user_id, user.platform, user.group_id, user.nickname, user.gold, user.exp, user.level,
                    user.fishing_count, user.total_fish_weight, user.total_income,
                    user.last_fishing_time, user.auto_fishing, user.total_fishing_count,
                    user.total_coins_earned, user.fish_pond_capacity, user.created_at, user.updated_at
                )
            )
            return True
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False

    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        try:
            user.updated_at = int(time.time())
            self.db.execute_query(
                """UPDATE users
                   SET platform=?,
                       group_id=?,
                       nickname=?,
                       gold=?,
                       exp=?,
                       level=?,
                       fishing_count=?,
                       total_fish_weight=?,
                       total_income=?,
                       last_fishing_time=?,
                       auto_fishing=?,
                       total_fishing_count=?,
                       total_coins_earned=?,
                       fish_pond_capacity=?,
                       updated_at=?
                   WHERE user_id = ?""",
                (
                    user.platform, user.group_id, user.nickname, user.gold, user.exp, user.level, user.fishing_count,
                    user.total_fish_weight, user.total_income, user.last_fishing_time,
                    user.auto_fishing, user.total_fishing_count, user.total_coins_earned,
                    user.fish_pond_capacity, user.updated_at, user.user_id
                )
            )
            return True
        except Exception as e:
            print(f"更新用户失败: {e}")
            return False

    def update_user_field(self, user_id: str, field: str, value) -> bool:
        """更新用户指定字段"""
        try:
            self.db.execute_query(
                f"UPDATE users SET {field} = ? WHERE user_id = ?",
                (value, user_id)
            )
            return True
        except Exception as e:
            print(f"更新用户字段 {field} 失败: {e}")
            return False

    def update_user_fields(self, user_id: str, fields: dict) -> bool:
        """更新用户多个字段"""
        try:
            if not fields:
                return True

            # 构建SET子句
            set_clause = ", ".join([f"{field} = ?" for field in fields.keys()])
            values = list(fields.values()) + [user_id]
            query = f"UPDATE users SET {set_clause}, updated_at = ? WHERE user_id = ?"
            values.append(int(time.time()))
            values = tuple(values)

            self.db.execute_query(query, values)
            return True
        except Exception as e:
            print(f"更新用户字段失败: {e}")
            return False

    def add_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        if amount <= 0:
            return False

        try:
            self.db.execute_query(
                "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                (amount, user_id)
            )
            return True
        except Exception as e:
            print(f"增加用户金币失败: {e}")
            return False

    def deduct_gold(self, user_id: str, amount: int) -> bool:
        """原子操作扣除用户金币"""
        if amount <= 0:
            return False

        try:
            result = self.db.execute_query(
                "UPDATE users SET gold = gold - ? WHERE user_id = ? AND gold >= ?",
                (amount, user_id, amount)
            )
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"扣除用户金币失败: {e}")
            return False

    def update_exp_and_level(self, user_id: str, exp: int, level: int) -> bool:
        """更新用户经验值和等级"""
        try:
            self.db.execute_query(
                "UPDATE users SET exp = ?, level = ? WHERE user_id = ?",
                (exp, level, user_id)
            )
            return True
        except Exception as e:
            print(f"更新用户经验值和等级失败: {e}")
            return False

    def update_fishing_stats(self, user_id: str, fishing_count: int, last_fishing_time: int,
                           total_fish_weight: float, total_income: int) -> bool:
        """更新用户钓鱼统计数据"""
        try:
            self.db.execute_query(
                """UPDATE users SET
                   fishing_count = ?,
                   last_fishing_time = ?,
                   total_fish_weight = ?,
                   total_income = ?
                   WHERE user_id = ?""",
                (fishing_count, last_fishing_time, total_fish_weight, total_income, user_id)
            )
            return True
        except Exception as e:
            print(f"更新用户钓鱼统计数据失败: {e}")
            return False

    def set_auto_fishing(self, user_id: str, auto_fishing: bool) -> bool:
        """设置自动钓鱼状态"""
        try:
            self.db.execute_query(
                "UPDATE users SET auto_fishing = ? WHERE user_id = ?",
                (auto_fishing, user_id)
            )
            return True
        except Exception as e:
            print(f"设置自动钓鱼状态失败: {e}")
            return False

    def check_sign_in(self, user_id: str, date: str) -> bool:
        """检查用户是否已签到"""
        try:
            existing_record = self.db.fetch_one(
                "SELECT * FROM sign_in_logs WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            return existing_record
        except Exception as e:
            print(f"设置自动钓鱼状态失败: {e}")
            return False

    def yesterday_record(self, user_id: str, date: str) -> Optional[dict]:
        """检查用户昨天是否签到"""
        try:
            yesterday_record = self.db.fetch_one(
            "SELECT streak FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, date)
        )
            return yesterday_record
        except Exception as e:
            print(f"检查用户昨天是否签到失败: {e}")
            return None

    def record_sign_in(self, user_id: str, today: str, streak: int, reward_gold: int) -> bool:
        """记录用户签到"""
        try:
            self.db.execute_query(
                """INSERT INTO sign_in_logs
                       (user_id, date, streak, reward_gold, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, today, streak, reward_gold, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"记录用户签到失败: {e}")
            return False
