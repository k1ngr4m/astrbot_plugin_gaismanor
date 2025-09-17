from typing import Optional, List
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
import time

class EquipmentService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_user_rods(self, user_id: str) -> List[Rod]:
        """获取用户所有鱼竿"""
        results = self.db.fetch_all(
            """SELECT rt.*, uri.level, uri.exp FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )
        return [
            Rod(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                catch_bonus=row['catch_bonus'],
                weight_bonus=row['weight_bonus'],
                level=row['level'],
                exp=row['exp']
            ) for row in results
        ]

    def get_user_accessories(self, user_id: str) -> List[Accessory]:
        """获取用户所有饰品"""
        results = self.db.fetch_all(
            """SELECT at.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ?""",
            (user_id,)
        )
        return [
            Accessory(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                effect_type=row['effect_type'],
                effect_value=row['effect_value']
            ) for row in results
        ]

    def get_user_bait(self, user_id: str) -> List[Bait]:
        """获取用户所有鱼饵"""
        results = self.db.fetch_all(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ?""",
            (user_id,)
        )
        return [
            Bait(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                catch_rate_bonus=row['catch_rate_bonus'],
                duration=row['duration']
            ) for row in results
        ]

    def equip_rod(self, user_id: str, rod_id: int) -> bool:
        """装备鱼竿"""
        # 先取消当前装备的鱼竿
        self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )

        # 装备新的鱼竿
        result = self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )
        return result is not None

    def equip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """装备饰品"""
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
        return result is not None

    def unequip_rod(self, user_id: str, rod_id: int) -> bool:
        """卸下鱼竿"""
        result = self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )
        return result is not None

    def unequip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """卸下饰品"""
        result = self.db.execute_query(
            "UPDATE user_accessory_instances SET is_equipped = FALSE WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )
        return result is not None

    def get_equipped_rod(self, user_id: str) -> Optional[Rod]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.*, uri.level, uri.exp FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return Rod(
                id=result['id'],
                name=result['name'],
                rarity=result['rarity'],
                description=result['description'],
                price=result['price'],
                catch_bonus=result['catch_bonus'],
                weight_bonus=result['weight_bonus'],
                level=result['level'],
                exp=result['exp']
            )
        return None

    def get_equipped_accessory(self, user_id: str) -> Optional[Accessory]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return Accessory(
                id=result['id'],
                name=result['name'],
                rarity=result['rarity'],
                description=result['description'],
                price=result['price'],
                effect_type=result['effect_type'],
                effect_value=result['effect_value']
            )
        return None