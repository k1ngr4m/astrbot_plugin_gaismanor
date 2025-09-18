from typing import Optional, List
from astrbot.api.event import AstrMessageEvent
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
            """SELECT rt.*, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
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
                price=row['purchase_cost'] or 0,
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                durability=row['durability'] or 0,
                level=row['level'],
                exp=row['exp'],
                is_equipped=bool(row['is_equipped'])
            ) for row in results
        ]

    def get_user_accessories(self, user_id: str) -> List[Accessory]:
        """获取用户所有饰品"""
        results = self.db.fetch_all(
            """SELECT at.*, uai.is_equipped FROM user_accessory_instances uai
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
                price=100,  # 默认价格
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc'],
                is_equipped=bool(row['is_equipped'])
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
                price=row['cost'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=bool(row['is_consumable']),
                quantity=row['quantity']
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
            """SELECT rt.*, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
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
                price=result['purchase_cost'] or 0,
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                durability=result['durability'] or 0,
                level=result['level'],
                exp=result['exp'],
                is_equipped=bool(result['is_equipped'])
            )
        return None

    def get_equipped_accessory(self, user_id: str) -> Optional[Accessory]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.*, uai.is_equipped FROM user_accessory_instances uai
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
                price=100,  # 默认价格
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                coin_mod=result['coin_mod'],
                other_desc=result['other_desc'],
                is_equipped=bool(result['is_equipped'])
            )
        return None

    async def rod_command(self, event: AstrMessageEvent):
        """鱼竿命令"""
        user_id = event.get_sender_id()
        # 获取用户鱼竿库存
        rods = self.get_user_rods(user_id)

        if not rods:
            yield event.plain_result("您的鱼竿背包是空的，快去商店购买一些鱼竿吧！")
            return

        # 构建鱼竿信息
        rod_info = "=== 您的鱼竿背包 ===\n"
        for i, rod in enumerate(rods, 1):
            rarity_stars = "★" * rod.rarity
            equip_status = " [装备中]" if rod.is_equipped else ""
            rod_info += f"{i}. {rod.name} {rarity_stars} - 等级:{rod.level} - 经验:{rod.exp}{equip_status}\n"
            rod_info += f"   品质加成: +{rod.quality_mod}  数量加成: +{rod.quantity_mod}\n\n"

        yield event.plain_result(rod_info)

    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """使用/装备鱼竿命令"""
        user_id = event.get_sender_id()

        # 检查鱼竿是否存在
        rod_instance = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到指定的鱼竿")
            return

        # 装备鱼竿
        success = self.equip_rod(user_id, rod_id)

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_instance['rod_template_id'],)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功装备鱼竿: {rod_name}")
        else:
            yield event.plain_result("装备鱼竿失败")
