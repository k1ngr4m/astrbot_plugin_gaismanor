from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager
import time

class InventoryCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

        # 鱼塘默认容量
        self.default_fish_capacity = 480

    async def fish_pond_command(self, event: AstrMessageEvent):
        """查看鱼类背包命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取鱼类库存
        fish_inventory = self.user_service.get_user_fish_inventory(user_id)

        if not fish_inventory:
            yield event.plain_result("您的鱼塘还是空的呢，快去钓鱼吧！")
            return

        # 构建鱼类信息
        fish_info = f"=== {user.nickname} 的鱼塘 ===\n"
        total_weight = 0

        for i, fish in enumerate(fish_inventory, 1):
            fish_template = self.db_manager.fetch_one(
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
        """查看鱼塘容量命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取鱼类库存
        fish_inventory = self.user_service.get_user_fish_inventory(user_id)

        yield event.plain_result(f"您的鱼塘容量: {len(fish_inventory)}/{self.default_fish_capacity}")

    async def upgrade_fish_pond_command(self, event: AstrMessageEvent):
        """升级鱼塘命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查是否已满级（这里简化处理，实际可以有多个等级）
        yield event.plain_result("鱼塘升级功能正在开发中，敬请期待！")

    async def bait_command(self, event: AstrMessageEvent):
        """查看鱼饵背包命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取鱼饵库存
        bait_list = self.equipment_service.get_user_bait(user_id)

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
        """查看鱼竿背包命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取鱼竿库存
        rods = self.equipment_service.get_user_rods(user_id)

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