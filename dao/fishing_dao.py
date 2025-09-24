"""
钓鱼数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.user import FishInventory
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class FishingDAO(BaseDAO):
    """钓鱼数据访问对象，封装所有钓鱼相关的数据库操作"""

    def get_fish_templates(self) -> List[FishTemplate]:
        """获取所有鱼类模板"""
        results = self.db.fetch_all("SELECT * FROM fish_templates")
        return [
            FishTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                base_value=row['base_value'],
                min_weight=row['min_weight'],
                max_weight=row['max_weight'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_rod_templates(self) -> List[RodTemplate]:
        """获取所有鱼竿模板"""
        results = self.db.fetch_all("SELECT * FROM rod_templates")
        return [
            RodTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                source=row['source'],
                purchase_cost=row['purchase_cost'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                durability=row['durability'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_accessory_templates(self) -> List[AccessoryTemplate]:
        """获取所有饰品模板"""
        results = self.db.fetch_all("SELECT * FROM accessory_templates")
        return [
            AccessoryTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                slot_type=row['slot_type'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_bait_templates(self) -> List[BaitTemplate]:
        """获取所有鱼饵模板"""
        results = self.db.fetch_all("SELECT * FROM bait_templates")
        return [
            BaitTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                cost=row['cost'],
                required_rod_rarity=row['required_rod_rarity'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=row['is_consumable']
            ) for row in results
        ]

    def get_equipped_rod(self, user_id: str) -> Optional[RodTemplate]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.* FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return RodTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                source=result['source'],
                purchase_cost=result['purchase_cost'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                durability=result['durability'],
                icon_url=result['icon_url']
            )
        return None

    def get_equipped_rod_instance(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户装备的鱼竿实例（包含耐久度等实例信息）"""
        result = self.db.fetch_one(
            """SELECT uri.* FROM user_rod_instances uri
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        return result

    def get_equipped_accessory(self, user_id: str) -> Optional[AccessoryTemplate]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return AccessoryTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                slot_type=result['slot_type'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                coin_mod=result['coin_mod'],
                other_desc=result['other_desc'],
                icon_url=result['icon_url']
            )
        return None

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

    def add_fish_to_inventory(self, user_id: str, fish_template_id: int,
                            weight: float, value: int) -> bool:
        """添加鱼到用户库存"""
        try:
            self.db.execute_query(
                """INSERT INTO user_fish_inventory
                   (user_id, fish_template_id, weight, value, caught_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, fish_template_id, weight, value, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"添加鱼到库存失败: {e}")
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

    def get_user_pond_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户鱼塘信息"""
        return self.db.fetch_one("""
            SELECT COUNT(*) as total_count, COALESCE(SUM(value), 0) as total_value
            FROM user_fish_inventory
            WHERE user_id = ?
        """, (user_id,))


    # ==================自动钓鱼相关==================
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

    # ==================钓鱼日志相关==================
    def add_fishing_log(self, user_id: str, fish_template_id: int,
                        fish_weight: float, fish_value: int, success: bool) -> bool:
        """添加钓鱼日志"""
        try:
            self.db.execute_query(
                """INSERT INTO fishing_logs
                   (user_id, fish_template_id, fish_weight, fish_value, success, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, fish_template_id, fish_weight, fish_value, success, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"添加钓鱼日志失败: {e}")
            return False

    def get_fishing_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的钓鱼记录"""
        return self.db.fetch_all("""
                                 SELECT fl.*,
                                        ft.name   as fish_name,
                                        ft.rarity as fish_rarity,
                                        uri.rod_template_id,
                                        rt.name   as rod_name,
                                        ubi.bait_template_id,
                                        bt.name   as bait_name
                                 FROM fishing_logs fl
                                          LEFT JOIN fish_templates ft ON fl.fish_template_id = ft.id
                                          LEFT JOIN user_rod_instances uri ON fl.rod_id = uri.id
                                          LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
                                          LEFT JOIN user_bait_inventory ubi ON fl.bait_id = ubi.id
                                          LEFT JOIN bait_templates bt ON ubi.bait_template_id = bt.id
                                 WHERE fl.user_id = ?
                                 ORDER BY fl.timestamp DESC LIMIT ?
                                 """, (user_id, limit))