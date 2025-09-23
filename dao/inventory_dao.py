"""
库存数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.user import FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class InventoryDAO(BaseDAO):
    """库存数据访问对象，封装所有库存相关的数据库操作"""

    def get_user_fish_inventory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼类库存"""
        return self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )

    def get_user_fish_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼类模板信息"""
        return self.db.fetch_all(
            """SELECT ufi.*, ft.name as fish_name, ft.description as fish_description,
                      ft.rarity as fish_rarity, ft.base_value as fish_base_value,
                      ft.min_weight, ft.max_weight
               FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ?
               ORDER BY ufi.caught_at DESC""",
            (user_id,)
        )

    def get_user_rods(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼竿库存"""
        return self.db.fetch_all(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped,
                      uri.acquired_at, uri.durability
               FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )

    def get_user_accessories(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户饰品库存"""
        return self.db.fetch_all(
            """SELECT at.*, uai.is_equipped, uai.acquired_at
               FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ?""",
            (user_id,)
        )

    def get_user_bait(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户鱼饵库存"""
        return self.db.fetch_all(
            """SELECT bt.*, ubi.quantity
               FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.quantity > 0""",
            (user_id,)
        )

    def get_equipped_rod(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户装备的鱼竿"""
        return self.db.fetch_one(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped,
                      uri.acquired_at, uri.durability
               FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )

    def upgrade_user_fish_pond(self, user_id: str, new_capacity: int) -> bool:
        """升级用户鱼塘容量"""
        try:
            self.db.execute_query(
                "UPDATE users SET fish_pond_capacity = ? WHERE user_id = ?",
                (new_capacity, user_id)
            )
            return True
        except Exception as e:
            print(f"升级用户鱼塘容量失败: {e}")
            return False

    def deduct_user_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        try:
            result = self.db.execute_query(
                "UPDATE users SET gold = gold - ? WHERE user_id = ? AND gold >= ?",
                (amount, user_id, amount)
            )
            return result and getattr(result, 'rowcount', 0) > 0
        except Exception as e:
            print(f"扣除用户金币失败: {e}")
            return False