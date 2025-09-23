"""
其他服务数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.database import DatabaseManager
from ..models.user import User
from .base_dao import BaseDAO


class OtherDAO(BaseDAO):
    """其他服务数据访问对象，封装所有其他服务相关的数据库操作"""

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
                nickname=result['nickname'],
                gold=result['gold'],
                exp=result['exp'],
                level=result['level'],
                fishing_count=result['fishing_count'],
                total_fish_weight=result['total_fish_weight'],
                total_income=result['total_income'],
                last_fishing_time=result['last_fishing_time'],
                auto_fishing=result['auto_fishing'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None

    def get_user_basic_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户基本信息（用于检查用户是否已注册）"""
        return self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    def update_user_auto_fishing(self, user_id: str, auto_fishing: bool) -> bool:
        """更新用户自动钓鱼状态"""
        try:
            self.db.execute_query(
                "UPDATE users SET auto_fishing = ? WHERE user_id = ?",
                (auto_fishing, user_id)
            )
            return True
        except Exception as e:
            print(f"更新用户自动钓鱼状态失败: {e}")
            return False

    def get_auto_fishing_users(self) -> List[Dict[str, Any]]:
        """获取所有开启自动钓鱼的用户"""
        return self.db.fetch_all("SELECT * FROM users WHERE auto_fishing = TRUE")

    def update_user_data(self, user: User) -> bool:
        """更新用户数据"""
        try:
            self.db.execute_query(
                """UPDATE users SET
                   platform=?, gold=?, fishing_count=?, last_fishing_time=?, total_fish_weight=?, total_income=?
                   WHERE user_id=?""",
                (user.platform, user.gold, user.fishing_count, user.last_fishing_time,
                 user.total_fish_weight, user.total_income, user.user_id)
            )
            return True
        except Exception as e:
            print(f"更新用户数据失败: {e}")
            return False

    def get_comprehensive_leaderboard(self, group_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取综合排行榜"""
        return self.db.fetch_all("""
            SELECT u.nickname, u.gold, u.fishing_count, u.total_income,
                   uri.rod_template_id, rt.name as rod_name,
                   uai.accessory_template_id, at.name as accessory_name,
                   t.name as title_name
            FROM users u
            LEFT JOIN user_rod_instances uri ON u.user_id = uri.user_id AND uri.is_equipped = TRUE
            LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
            LEFT JOIN user_accessory_instances uai ON u.user_id = uai.user_id AND uai.is_equipped = TRUE
            LEFT JOIN accessory_templates at ON uai.accessory_template_id = at.id
            LEFT JOIN user_titles ut ON u.user_id = ut.user_id AND ut.is_active = TRUE
            LEFT JOIN titles t ON ut.title_id = t.id
            WHERE u.group_id = ?
            ORDER BY (u.gold + u.fishing_count * 10 + u.total_income) DESC
            LIMIT ?
        """, (group_id, limit))

    def get_all_fish_templates(self) -> List[Dict[str, Any]]:
        """获取所有鱼类模板"""
        return self.db.fetch_all("""
            SELECT id, name, description, rarity, base_value
            FROM fish_templates
            ORDER BY rarity DESC, base_value DESC
        """)

    def get_fishing_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的钓鱼记录"""
        return self.db.fetch_all("""
            SELECT fl.*, ft.name as fish_name, ft.rarity as fish_rarity,
                   uri.rod_template_id, rt.name as rod_name,
                   ubi.bait_template_id, bt.name as bait_name
            FROM fishing_logs fl
            LEFT JOIN fish_templates ft ON fl.fish_template_id = ft.id
            LEFT JOIN user_rod_instances uri ON fl.rod_id = uri.id
            LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
            LEFT JOIN user_bait_inventory ubi ON fl.bait_id = ubi.id
            LEFT JOIN bait_templates bt ON ubi.bait_template_id = bt.id
            WHERE fl.user_id = ?
            ORDER BY fl.timestamp DESC
            LIMIT ?
        """, (user_id, limit))

    def get_user_equipped_rod(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户装备的鱼竿"""
        return self.db.fetch_one("""
            SELECT rt.name, rt.rarity, uri.level as refine_level
            FROM user_rod_instances uri
            JOIN rod_templates rt ON uri.rod_template_id = rt.id
            WHERE uri.user_id = ? AND uri.is_equipped = TRUE
        """, (user_id,))

    def get_user_equipped_accessory(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户装备的饰品"""
        return self.db.fetch_one("""
            SELECT at.name, at.rarity
            FROM user_accessory_instances uai
            JOIN accessory_templates at ON uai.accessory_template_id = at.id
            WHERE uai.user_id = ? AND uai.is_equipped = TRUE
        """, (user_id,))

    def get_user_current_bait(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户当前使用的鱼饵"""
        return self.db.fetch_one("""
            SELECT bt.name, bt.rarity, ubi.quantity
            FROM user_bait_inventory ubi
            JOIN bait_templates bt ON ubi.bait_template_id = bt.id
            WHERE ubi.user_id = ? AND ubi.id = (
                SELECT current_bait_id FROM users WHERE user_id = ?
            )
        """, (user_id, user_id))

    def get_user_current_title(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户当前称号"""
        return self.db.fetch_one("""
            SELECT t.name
            FROM user_titles ut
            JOIN titles t ON ut.title_id = t.id
            WHERE ut.user_id = ? AND ut.is_active = TRUE
        """, (user_id,))

    def get_user_pond_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户鱼塘信息"""
        return self.db.fetch_one("""
            SELECT COUNT(*) as total_count, COALESCE(SUM(value), 0) as total_value
            FROM user_fish_inventory
            WHERE user_id = ?
        """, (user_id,))

    def get_user_wipe_bomb_count(self, user_id: str, start_time: int, end_time: int) -> Optional[Dict[str, Any]]:
        """获取用户擦弹次数"""
        return self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM wipe_bomb_logs
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
        """, (user_id, start_time, end_time))

    def deduct_user_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        try:
            self.db.execute_query(
                "UPDATE users SET gold = gold - ? WHERE user_id = ?",
                (amount, user_id)
            )
            return True
        except Exception as e:
            print(f"扣除用户金币时出错: {e}")
            return False

    def add_user_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        try:
            self.db.execute_query(
                "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                (amount, user_id)
            )
            return True
        except Exception as e:
            print(f"增加用户金币时出错: {e}")
            return False

    def add_wipe_bomb_log(self, user_id: str, bet_amount: int, multiplier: float, earned_amount: int, timestamp: int) -> bool:
        """添加擦弹日志"""
        try:
            self.db.execute_query(
                """INSERT INTO wipe_bomb_logs
                   (user_id, bet_amount, multiplier, earned_amount, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, bet_amount, multiplier, earned_amount, timestamp)
            )
            return True
        except Exception as e:
            print(f"添加擦弹日志时出错: {e}")
            return False

    def get_wipe_bomb_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的擦弹记录"""
        return self.db.fetch_all("""
            SELECT *
            FROM wipe_bomb_logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))