"""
商店数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.equipment import Rod, Accessory, Bait
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class ShopDAO(BaseDAO):
    """商店数据访问对象，封装所有商店相关的数据库操作"""

    def get_rod_templates(self) -> List[Dict[str, Any]]:
        """获取所有鱼竿模板"""
        return self.db.fetch_all("SELECT * FROM rod_templates ORDER BY rarity, purchase_cost")

    def get_bait_templates(self) -> List[Dict[str, Any]]:
        """获取所有鱼饵模板"""
        return self.db.fetch_all("SELECT * FROM bait_templates ORDER BY rarity, cost")

    def get_accessory_templates(self) -> List[Dict[str, Any]]:
        """获取所有饰品模板"""
        return self.db.fetch_all("SELECT * FROM accessory_templates ORDER BY rarity, id")

    def get_rod_template_by_id(self, rod_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取鱼竿模板"""
        return self.db.fetch_one(
            "SELECT * FROM rod_templates WHERE id = ?",
            (rod_id,)
        )

    def get_bait_template_by_id(self, bait_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取鱼饵模板"""
        return self.db.fetch_one(
            "SELECT * FROM bait_templates WHERE id = ?",
            (bait_id,)
        )

    def get_accessory_template_by_id(self, accessory_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取饰品模板"""
        return self.db.fetch_one(
            "SELECT * FROM accessory_templates WHERE id = ?",
            (accessory_id,)
        )

    def add_rod_to_user(self, user_id: str, rod_template_id: int) -> Optional[int]:
        """为用户添加鱼竿"""
        try:
            result = self.db.execute_query(
                """INSERT INTO user_rod_instances
                   (user_id, rod_template_id, level, exp, is_equipped, durability, acquired_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, rod_template_id, 1, 0, False, 100, int(time.time()))
            )

            # 获取插入的记录ID
            if result and hasattr(result, 'lastrowid'):
                return result.lastrowid
            return None
        except Exception as e:
            print(f"为用户添加鱼竿失败: {e}")
            return None

    def add_bait_to_user(self, user_id: str, bait_template_id: int, quantity: int) -> bool:
        """为用户添加鱼饵"""
        try:
            # 先检查是否已存在该鱼饵
            existing = self.db.fetch_one(
                "SELECT quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                (user_id, bait_template_id)
            )

            if existing:
                # 更新数量
                new_quantity = existing['quantity'] + quantity
                self.db.execute_query(
                    "UPDATE user_bait_inventory SET quantity = ? WHERE user_id = ? AND bait_template_id = ?",
                    (new_quantity, user_id, bait_template_id)
                )
            else:
                # 插入新记录
                self.db.execute_query(
                    """INSERT INTO user_bait_inventory
                       (user_id, bait_template_id, quantity)
                       VALUES (?, ?, ?)""",
                    (user_id, bait_template_id, quantity)
                )
            return True
        except Exception as e:
            print(f"为用户添加鱼饵失败: {e}")
            return False

    def add_accessory_to_user(self, user_id: str, accessory_template_id: int) -> bool:
        """为用户添加饰品"""
        try:
            # 检查是否已拥有该饰品
            existing = self.db.fetch_one(
                "SELECT id FROM user_accessory_instances WHERE user_id = ? AND accessory_template_id = ?",
                (user_id, accessory_template_id)
            )

            if existing:
                # 已拥有该饰品
                return False

            # 插入新记录
            self.db.execute_query(
                """INSERT INTO user_accessory_instances
                   (user_id, accessory_template_id, is_equipped, acquired_at)
                   VALUES (?, ?, ?, ?)""",
                (user_id, accessory_template_id, False, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"为用户添加饰品失败: {e}")
            return False

    def deduct_user_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        try:
            result = self.db.execute_update(
                "UPDATE users SET gold = gold - ? WHERE user_id = ? AND gold >= ?",
                (amount, user_id, amount)
            )
            return result and result > 0
        except Exception as e:
            print(f"扣除用户金币失败: {e}")
            return False