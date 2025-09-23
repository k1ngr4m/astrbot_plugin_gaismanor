"""
出售数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class SellDAO(BaseDAO):
    """出售数据访问对象，封装所有出售相关的数据库操作"""

    def get_user_fish_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼类库存"""
        return self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )

    def get_user_fish_by_rarity(self, user_id: str, rarity: int) -> List[Dict[str, Any]]:
        """根据稀有度获取用户鱼类"""
        return self.db.fetch_all(
            """SELECT ufi.* FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ? AND ft.rarity = ?""",
            (user_id, rarity)
        )

    def get_user_fish_by_id(self, user_id: str, fish_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户鱼类"""
        return self.db.fetch_one(
            "SELECT * FROM user_fish_inventory WHERE user_id = ? AND id = ?",
            (user_id, fish_id)
        )

    def delete_user_fish(self, user_id: str, fish_id: int) -> bool:
        """删除用户鱼类"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_fish_inventory WHERE user_id = ? AND id = ?",
                (user_id, fish_id)
            )
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"删除用户鱼类失败: {e}")
            return False

    def delete_all_user_fish(self, user_id: str) -> bool:
        """删除用户所有鱼类"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_fish_inventory WHERE user_id = ?",
                (user_id,)
            )
            return True
        except Exception as e:
            print(f"删除用户所有鱼类失败: {e}")
            return False

    def delete_user_fish_by_rarity(self, user_id: str, rarity: int) -> bool:
        """根据稀有度删除用户鱼类"""
        try:
            result = self.db.execute_query(
                """DELETE FROM user_fish_inventory WHERE user_id = ? AND id IN (
                    SELECT ufi.id FROM user_fish_inventory ufi
                    JOIN fish_templates ft ON ufi.fish_template_id = ft.id
                    WHERE ufi.user_id = ? AND ft.rarity = ?
                )""",
                (user_id, user_id, rarity)
            )
            return True
        except Exception as e:
            print(f"根据稀有度删除用户鱼类失败: {e}")
            return False

    def get_fish_template_by_id(self, fish_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取鱼类模板"""
        return self.db.fetch_one(
            "SELECT * FROM fish_templates WHERE id = ?",
            (fish_id,)
        )

    def get_user_rods(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有鱼竿"""
        return self.db.fetch_all(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )

    def get_user_rod_by_id(self, user_id: str, rod_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户鱼竿"""
        return self.db.fetch_one(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.id = ?""",
            (user_id, rod_id)
        )

    def delete_user_rod(self, user_id: str, rod_id: int) -> bool:
        """删除用户鱼竿"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_rod_instances WHERE user_id = ? AND id = ?",
                (user_id, rod_id)
            )
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"删除用户鱼竿失败: {e}")
            return False

    def delete_all_user_rods(self, user_id: str) -> bool:
        """删除用户所有鱼竿"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_rod_instances WHERE user_id = ?",
                (user_id,)
            )
            return True
        except Exception as e:
            print(f"删除用户所有鱼竿失败: {e}")
            return False

    def get_user_bait(self, user_id: str, bait_id: int) -> Optional[Dict[str, Any]]:
        """获取用户鱼饵"""
        return self.db.fetch_one(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND bt.id = ? AND ubi.quantity > 0""",
            (user_id, bait_id)
        )

    def get_user_bait_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼饵模板"""
        return self.db.fetch_all(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.quantity > 0""",
            (user_id,)
        )

    def delete_user_bait(self, user_id: str, bait_template_id: int, quantity: int) -> bool:
        """删除用户鱼饵"""
        try:
            existing = self.db.fetch_one(
                "SELECT quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                (user_id, bait_template_id)
            )

            if not existing:
                return False

            if existing['quantity'] <= quantity:
                # 删除记录
                self.db.execute_query(
                    "DELETE FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                    (user_id, bait_template_id)
                )
            else:
                # 更新数量
                new_quantity = existing['quantity'] - quantity
                self.db.execute_query(
                    "UPDATE user_bait_inventory SET quantity = ? WHERE user_id = ? AND bait_template_id = ?",
                    (new_quantity, user_id, bait_template_id)
                )
            return True
        except Exception as e:
            print(f"删除用户鱼饵失败: {e}")
            return False