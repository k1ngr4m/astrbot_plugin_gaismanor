from typing import Optional, List

from astrbot.core.platform import AstrMessageEvent
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
import time

class InventoryService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def fish_pond_command(self, event: AstrMessageEvent):
        """鱼塘命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户鱼类库存
        fish_inventory = self.get_user_fish_inventory(user_id)

        if not fish_inventory:
            yield event.plain_result("您的鱼塘还是空的呢，快去钓鱼吧！")
            return

        # 构建鱼类信息
        fish_info = f"=== {user.nickname} 的鱼塘 ===\n"
        total_weight = 0

        for i, fish in enumerate(fish_inventory, 1):
            fish_template = self.db.fetch_one(
                "SELECT name, rarity FROM fish_templates WHERE id = ?",
                (fish.fish_template_id,)
            )
            if fish_template:
                rarity_stars = "★" * fish_template['rarity']
                fish_info += f"{i}. {fish_template['name']} {rarity_stars} - {fish.weight:.2f}kg - {fish.value}金币\n"
                total_weight += fish.weight

        fish_info += f"\n总重量: {total_weight:.2f}kg\n"
        fish_info += f"鱼塘容量: {len(fish_inventory)}/{self.default_fish_capacity}"

        yield event.plain_result(fish_info)

    async def fish_pond_capacity_command(self, event: AstrMessageEvent):
        """鱼塘容量命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户鱼类库存
        fish_inventory = self.get_user_fish_inventory(user_id)

        yield event.plain_result(f"您的鱼塘容量: {len(fish_inventory)}/{self.default_fish_capacity}")

    async def upgrade_fish_pond_command(self, event: AstrMessageEvent):
        """升级鱼塘命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查是否已满级（这里简化处理，实际可以有多个等级）
        yield event.plain_result("鱼塘升级功能正在开发中，敬请期待！")

    async def bait_command(self, event: AstrMessageEvent):
        """鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户鱼饵库存
        bait_list = self.get_user_bait(user_id)

        if not bait_list:
            yield event.plain_result("您的鱼饵背包是空的，快去商店购买一些鱼饵吧！")
            return

        # 构建鱼饵信息
        bait_info = "=== 您的鱼饵背包 ===\n"
        for i, bait in enumerate(bait_list, 1):
            rarity_stars = "★" * bait.rarity
            bait_info += f"{i}. {bait.name} {rarity_stars} - 数量: {bait.quantity}\n"
            bait_info += f"   效果: {bait.effect_description}\n\n"

        yield event.plain_result(bait_info)

    async def rod_command(self, event: AstrMessageEvent):
        """鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

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

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
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

    def get_user_fish_inventory(self, user_id: str) -> List[FishInventory]:
        """获取用户鱼类库存"""
        results = self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )
        return [
            FishInventory(
                id=row['id'],
                user_id=row['user_id'],
                fish_template_id=row['fish_template_id'],
                weight=row['weight'],
                value=row['value'],
                caught_at=row['caught_at']
            ) for row in results
        ]

    def get_user_rods(self, user_id: str) -> List[RodTemplate]:
        """获取用户鱼竿库存"""
        results = self.db.fetch_all(
            """SELECT rt.*, uri.level, uri.exp, uri.is_equipped, uri.acquired_at, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )
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
                icon_url=row['icon_url'],
                level=row['level'],
                exp=row['exp'],
                is_equipped=row['is_equipped'],
                acquired_at=row['acquired_at']
            ) for row in results
        ]

    def get_user_accessories(self, user_id: str) -> List[AccessoryTemplate]:
        """获取用户饰品库存"""
        results = self.db.fetch_all(
            """SELECT at.*, uai.is_equipped, uai.acquired_at FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ?""",
            (user_id,)
        )
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
                icon_url=row['icon_url'],
                is_equipped=row['is_equipped'],
                acquired_at=row['acquired_at']
            ) for row in results
        ]

    def get_user_bait(self, user_id: str) -> List[BaitTemplate]:
        """获取用户鱼饵库存"""
        results = self.db.fetch_all(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ?""",
            (user_id,)
        )
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
                is_consumable=row['is_consumable'],
                quantity=row['quantity']
            ) for row in results
        ]

    def get_equipped_rod(self, user_id: str) -> Optional[RodTemplate]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.*, uri.level, uri.exp, uri.is_equipped, uri.acquired_at, uri.durability FROM user_rod_instances uri
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
                icon_url=result['icon_url'],
                level=result['level'],
                exp=result['exp'],
                is_equipped=result['is_equipped'],
                acquired_at=result['acquired_at']
            )
        return None

    def get_equipped_accessory(self, user_id: str) -> Optional[AccessoryTemplate]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.*, uai.is_equipped, uai.acquired_at FROM user_accessory_instances uai
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
                icon_url=result['icon_url'],
                is_equipped=result['is_equipped'],
                acquired_at=result['acquired_at']
            )
        return None