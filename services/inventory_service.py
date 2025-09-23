from typing import Optional, List

from astrbot.api.event import AstrMessageEvent
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
from ..dao.inventory_dao import InventoryDAO
from ..dao.user_dao import UserDAO
import time

class InventoryService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inventory_dao = InventoryDAO(db_manager)
        self.user_dao = UserDAO(db_manager)

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
        total_value = 0

        for i, fish in enumerate(fish_inventory, 1):
            fish_template = self.db.fetch_one(
                "SELECT name, rarity FROM fish_templates WHERE id = ?",
                (fish.fish_template_id,)
            )
            if fish_template:
                rarity_stars = "★" * fish_template['rarity']
                fish_info += f"{i}. {fish_template['name']} {rarity_stars} - {fish.weight:.2f}kg - {fish.value}金币\n"
                total_weight += fish.weight
                total_value += fish.value

        fish_info += f"\n⚖️总重量: {total_weight:.2f}kg\n"
        fish_info += f"💰总价值: {total_value}金币\n"
        fish_info += f"🐟鱼塘容量: {len(fish_inventory)}/{user.fish_pond_capacity}"

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

        yield event.plain_result(f"您的鱼塘容量: {len(fish_inventory)}/{user.fish_pond_capacity}")

    async def upgrade_fish_pond_command(self, event: AstrMessageEvent):
        """升级鱼塘命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 定义升级价格和容量增加量
        upgrade_costs = [500, 1000, 2000, 5000, 10000]  # 每级升级费用
        capacity_increases = [50, 100, 150, 200, 250]   # 每级扩容数量

        # 计算当前等级（基于容量，基础容量50）
        base_capacity = 50
        current_level = (user.fish_pond_capacity - base_capacity) // 50
        max_level = len(upgrade_costs)

        # 检查是否已满级
        if current_level >= max_level:
            yield event.plain_result("您的鱼塘已达到最高等级，无法继续升级！")
            return

        # 获取升级费用和扩容数量
        upgrade_cost = upgrade_costs[current_level]
        capacity_increase = capacity_increases[current_level]

        # 检查金币是否足够
        if user.gold < upgrade_cost:
            yield event.plain_result(f"金币不足！升级需要 {upgrade_cost} 金币，您当前只有 {user.gold} 金币。")
            return

        # 扣除金币并升级鱼塘
        if not self.user_dao.deduct_gold(user_id, upgrade_cost):
            yield event.plain_result("扣除金币失败，请稍后重试！")
            return

        new_capacity = user.fish_pond_capacity + capacity_increase
        if not self.inventory_dao.upgrade_user_fish_pond(user_id, new_capacity):
            yield event.plain_result("升级鱼塘失败，请稍后重试！")
            return

        yield event.plain_result(f"鱼塘升级成功！\n消耗金币: {upgrade_cost}\n鱼塘容量增加: {capacity_increase}\n当前容量: {new_capacity}")

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
                fish_pond_capacity=result['fish_pond_capacity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None

    def get_user_fish_inventory(self, user_id: str) -> List[FishInventory]:
        """获取用户鱼类库存"""
        results = self.inventory_dao.get_user_fish_inventory(user_id)
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
        results = self.inventory_dao.get_user_rods(user_id)
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
        results = self.inventory_dao.get_user_accessories(user_id)
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
        results = self.inventory_dao.get_user_bait(user_id)
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
        result = self.inventory_dao.get_equipped_rod(user_id)
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
        # 先获取所有饰品，然后筛选已装备的
        results = self.inventory_dao.get_user_accessories(user_id)
        equipped_accessories = [row for row in results if row.get('is_equipped')]

        if equipped_accessories:
            result = equipped_accessories[0]
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