"""
成就数据访问对象
"""
import time
import json
from typing import List, Optional, Dict, Any
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class AchievementDAO(BaseDAO):
    """成就数据访问对象，封装所有成就相关的数据库操作"""

    def get_user_achievements_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户成就进度"""
        return self.db.fetch_all(
            """SELECT ua.achievement_id, ua.progress, ua.completed, ua.completed_at, a.name, a.description
               FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id = a.id
               WHERE ua.user_id = ?""",
            (user_id,)
        )

    def get_user_titles(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户拥有的称号"""
        return self.db.fetch_all(
            """SELECT ut.title_id, ut.acquired_at, ut.is_active, t.name, t.description
               FROM user_titles ut
               JOIN titles t ON ut.title_id = t.id
               WHERE ut.user_id = ?""",
            (user_id,)
        )

    def update_achievement_progress(self, user_id: str, achievement_id: int, progress: int, completed: bool) -> bool:
        """更新用户成就进度"""
        try:
            now = int(time.time())
            existing_record = self.db.fetch_one(
                "SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?",
                (user_id, achievement_id)
            )

            if existing_record:
                # 更新现有记录
                self.db.execute_query(
                    "UPDATE user_achievements SET progress = ?, completed = ?, completed_at = ? WHERE id = ?",
                    (progress, completed, now if completed else None, existing_record['id'])
                )
            else:
                # 创建新记录
                self.db.execute_query(
                    "INSERT INTO user_achievements (user_id, achievement_id, progress, completed, completed_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, achievement_id, progress, completed, now if completed else None)
                )
            return True
        except Exception as e:
            print(f"更新用户成就进度失败: {e}")
            return False

    def grant_title_to_user(self, user_id: str, title_id: int) -> bool:
        """授予用户称号"""
        try:
            now = int(time.time())
            # 检查是否已经有这个称号
            existing_title = self.db.fetch_one(
                "SELECT id FROM user_titles WHERE user_id = ? AND title_id = ?",
                (user_id, title_id)
            )

            if not existing_title:
                self.db.execute_query(
                    "INSERT INTO user_titles (user_id, title_id, acquired_at) VALUES (?, ?, ?)",
                    (user_id, title_id, now)
                )
                return True
            return False
        except Exception as e:
            print(f"授予用户称号失败: {e}")
            return False

    def activate_user_title(self, user_id: str, title_id: int) -> bool:
        """激活用户称号"""
        try:
            # 先检查用户是否拥有该称号
            title_exists = self.db.fetch_one(
                "SELECT id FROM user_titles WHERE user_id = ? AND title_id = ?",
                (user_id, title_id)
            )

            if not title_exists:
                return False

            # 取消其他称号的激活状态
            self.db.execute_query(
                "UPDATE user_titles SET is_active = FALSE WHERE user_id = ?",
                (user_id,)
            )

            # 激活指定称号
            self.db.execute_query(
                "UPDATE user_titles SET is_active = TRUE WHERE user_id = ? AND title_id = ?",
                (user_id, title_id)
            )

            return True
        except Exception as e:
            print(f"激活用户称号失败: {e}")
            return False

    def get_unique_fish_count(self, user_id: str) -> int:
        """获取用户收集的不同鱼种数量"""
        result = self.db.fetch_one(
            "SELECT COUNT(DISTINCT fish_template_id) as count FROM fishing_logs WHERE user_id = ? AND success = TRUE",
            (user_id,)
        )
        return result['count'] if result else 0

    def get_garbage_count(self, user_id: str) -> int:
        """获取用户钓到的垃圾数量"""
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM fishing_logs WHERE user_id = ? AND fish_template_id = 0 AND success = TRUE",
            (user_id,)
        )
        return result['count'] if result else 0

    def get_max_wipe_multiplier(self, user_id: str) -> float:
        """获取用户获得的最大擦弹倍率"""
        try:
            result = self.db.fetch_one(
                "SELECT MAX(wipe_multiplier) as max_multiplier FROM fishing_logs WHERE user_id = ? AND wipe_multiplier > 1",
                (user_id,)
            )
            return result['max_multiplier'] if result and result['max_multiplier'] else 0.0
        except Exception:
            # 如果列不存在，返回0.0
            return 0.0

    def get_owned_rod_rarities(self, user_id: str) -> set:
        """获取用户拥有的鱼竿稀有度"""
        results = self.db.fetch_all(
            "SELECT DISTINCT rt.rarity FROM user_rod_instances uri JOIN rod_templates rt ON uri.rod_template_id = rt.id WHERE uri.user_id = ?",
            (user_id,)
        )
        return {r['rarity'] for r in results} if results else set()

    def get_owned_accessory_rarities(self, user_id: str) -> set:
        """获取用户拥有的饰品稀有度"""
        results = self.db.fetch_all(
            "SELECT DISTINCT at.rarity FROM user_accessory_instances uai JOIN accessory_templates at ON uai.accessory_template_id = at.id WHERE uai.user_id = ?",
            (user_id,)
        )
        return {r['rarity'] for r in results} if results else set()

    def has_heavy_fish(self, user_id: str) -> bool:
        """检查用户是否钓到过重鱼 (超过100kg)"""
        result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM fishing_logs WHERE user_id = ? AND fish_weight >= 100 AND success = TRUE",
            (user_id,)
        )
        return result and result['count'] > 0