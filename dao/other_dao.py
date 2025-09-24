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

    def get_comprehensive_leaderboard(self, group_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取综合排行榜"""
        # 如果没有提供group_id，则获取所有用户的排行榜
        if not group_id:
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
                ORDER BY (u.gold + u.fishing_count * 10 + u.total_income) DESC
                LIMIT ?
            """, (limit,))
        else:
            # 如果提供了group_id，则按group_id过滤
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

    def get_user_current_title(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户当前称号"""
        return self.db.fetch_one("""
            SELECT t.name
            FROM user_titles ut
            JOIN titles t ON ut.title_id = t.id
            WHERE ut.user_id = ? AND ut.is_active = TRUE
        """, (user_id,))

    # =================擦弹相关=================
    def get_user_wipe_bomb_count(self, user_id: str, start_time: int, end_time: int) -> Optional[Dict[str, Any]]:
        """获取用户擦弹次数"""
        return self.db.fetch_one("""
            SELECT COUNT(*) as count
            FROM wipe_bomb_logs
            WHERE user_id = ? AND timestamp >= ? AND timestamp <= ?
        """, (user_id, start_time, end_time))

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