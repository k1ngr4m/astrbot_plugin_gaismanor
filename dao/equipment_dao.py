"""
装备数据访问对象
"""
import json
import time
from typing import List, Optional, Dict, Any
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class EquipmentDAO(BaseDAO):
    """装备数据访问对象，封装所有装备相关的数据库操作"""

    def get_user_rods(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有鱼竿"""
        return self.db.fetch_all(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )

    def get_user_accessories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有饰品"""
        return self.db.fetch_all(
            """SELECT at.*, uai.is_equipped FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ?""",
            (user_id,)
        )

    def get_user_bait(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼饵"""
        return self.db.fetch_all(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.quantity > 0""",
            (user_id,)
        )

    def get_rod_instance(self, user_id: str, rod_id: int) -> Optional[Dict[str, Any]]:
        """获取用户指定的鱼竿实例"""
        return self.db.fetch_one(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.id = ?""",
            (user_id, rod_id)
        )

    def get_equipped_rod(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户装备的鱼竿"""
        return self.db.fetch_one(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )

    def equip_rod(self, user_id: str, rod_id: int) -> bool:
        """装备鱼竿"""
        try:
            # 先取消装备当前装备的鱼竿
            self.db.execute_update(
                "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
                (user_id,)
            )

            # 装备指定鱼竿
            result = self.db.execute_update(
                "UPDATE user_rod_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
                (user_id, rod_id)
            )
            return result and result > 0
        except Exception as e:
            print(f"装备鱼竿失败: {e}")
            return False

    def unequip_rod(self, user_id: str) -> bool:
        """卸下鱼竿"""
        try:
            result = self.db.execute_update(
                "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
                (user_id,)
            )
            return result and result > 0
        except Exception as e:
            print(f"卸下鱼竿失败: {e}")
            return False

    def update_rod_durability(self, rod_instance_id: int, durability: int) -> bool:
        """更新鱼竿耐久度"""
        try:
            self.db.execute_query(
                "UPDATE user_rod_instances SET durability = ? WHERE id = ?",
                (durability, rod_instance_id)
            )
            return True
        except Exception as e:
            print(f"更新鱼竿耐久度失败: {e}")
            return False

    def repair_rod(self, rod_instance_id: int, cost: int) -> bool:
        """维修鱼竿"""
        try:
            self.db.execute_query(
                "UPDATE user_rod_instances SET durability = 100 WHERE id = ?",
                (rod_instance_id,)
            )
            return True
        except Exception as e:
            print(f"维修鱼竿失败: {e}")
            return False

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

    def remove_rod_from_user(self, user_id: str, rod_id: int) -> bool:
        """从用户移除鱼竿"""
        try:
            result = self.db.execute_query(
                "DELETE FROM user_rod_instances WHERE user_id = ? AND id = ?",
                (user_id, rod_id)
            )
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"从用户移除鱼竿失败: {e}")
            return False

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

    def remove_bait_from_user(self, user_id: str, bait_template_id: int, quantity: int) -> bool:
        """从用户移除鱼饵"""
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
            print(f"从用户移除鱼饵失败: {e}")
            return False

    def use_bait(self, user_id: str, bait_template_id: int) -> bool:
        """使用鱼饵（减少1个）"""
        return self.remove_bait_from_user(user_id, bait_template_id, 1)

    def equip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """装备饰品"""
        try:
            # 先取消当前装备的饰品
            self.db.execute_query(
                "UPDATE user_accessory_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
                (user_id,)
            )

            # 装备新的饰品
            result = self.db.execute_query(
                "UPDATE user_accessory_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
                (user_id, accessory_id)
            )
            # execute_query方法不返回结果，我们通过检查影响的行数来判断是否成功
            # 这里假设如果能执行到这一步，就认为是成功的
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"装备饰品失败: {e}")
            return False

    def unequip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """卸下饰品"""
        try:
            self.db.execute_query(
                "UPDATE user_accessory_instances SET is_equipped = FALSE WHERE user_id = ? AND id = ?",
                (user_id, accessory_id)
            )
            # execute_query方法不返回结果，我们通过检查影响的行数来判断是否成功
            # 这里假设如果能执行到这一步，就认为是成功的
            return True
        except Exception as e:
            print(f"卸下饰品失败: {e}")
            return False