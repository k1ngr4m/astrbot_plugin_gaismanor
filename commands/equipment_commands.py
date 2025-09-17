from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager

class EquipmentCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

    async def rod_command(self, event: AstrMessageEvent):
        """查看鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户所有鱼竿
        rods = self.equipment_service.get_user_rods(user_id)

        if not rods:
            yield event.plain_result("您还没有鱼竿，请先到商店购买")
            return

        # 构建鱼竿信息
        rod_info = "=== 您的鱼竿 ===\n"
        for i, rod in enumerate(rods, 1):
            equip_status = " [装备中]" if rod.is_equipped else ""
            rod_info += f"{i}. {rod.name} - 稀有度:{rod.rarity}星 - 等级:{rod.level} - 经验:{rod.exp}\n"
            rod_info += f"   捕获加成: +{rod.catch_bonus}  重量加成: +{rod.weight_bonus}{equip_status}\n\n"

        yield event.plain_result(rod_info)

    async def accessory_command(self, event: AstrMessageEvent):
        """查看饰品命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户所有饰品
        accessories = self.equipment_service.get_user_accessories(user_id)

        if not accessories:
            yield event.plain_result("您还没有饰品，请先到商店购买")
            return

        # 构建饰品信息
        accessory_info = "=== 您的饰品 ===\n"
        for i, accessory in enumerate(accessories, 1):
            equip_status = " [装备中]" if accessory.is_equipped else ""
            accessory_info += f"{i}. {accessory.name} - 稀有度:{accessory.rarity}星\n"
            accessory_info += f"   效果: +{accessory.effect_value}{accessory.effect_type}{equip_status}\n\n"

        yield event.plain_result(accessory_info)

    async def bait_command(self, event: AstrMessageEvent):
        """查看鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户所有鱼饵
        bait_list = self.equipment_service.get_user_bait(user_id)

        if not bait_list:
            yield event.plain_result("您还没有鱼饵，请先到商店购买")
            return

        # 构建鱼饵信息
        bait_info = "=== 您的鱼饵 ===\n"
        for i, bait in enumerate(bait_list, 1):
            bait_info += f"{i}. {bait.name} - 稀有度:{bait.rarity}星\n"
            bait_info += f"   捕获率加成: +{bait.catch_rate_bonus}  持续时间: {bait.duration}秒\n\n"

        yield event.plain_result(bait_info)

    async def equip_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """装备鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在
        rod_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到指定的鱼竿")
            return

        # 装备鱼竿
        success = self.equipment_service.equip_rod(user_id, rod_id)

        if success:
            rod_template = self.db_manager.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_instance['rod_template_id'],)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功装备鱼竿: {rod_name}")
        else:
            yield event.plain_result("装备鱼竿失败")

    async def equip_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        """装备饰品命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查饰品是否存在
        accessory_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_accessory_instances WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )

        if not accessory_instance:
            yield event.plain_result("未找到指定的饰品")
            return

        # 装备饰品
        success = self.equipment_service.equip_accessory(user_id, accessory_id)

        if success:
            accessory_template = self.db_manager.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (accessory_instance['accessory_template_id'],)
            )
            accessory_name = accessory_template['name'] if accessory_template else "未知饰品"
            yield event.plain_result(f"成功装备饰品: {accessory_name}")
        else:
            yield event.plain_result("装备饰品失败")

    async def unequip_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """卸下鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在且已装备
        rod_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND id = ? AND is_equipped = TRUE",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到已装备的指定鱼竿")
            return

        # 卸下鱼竿
        success = self.equipment_service.unequip_rod(user_id, rod_id)

        if success:
            rod_template = self.db_manager.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_instance['rod_template_id'],)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功卸下鱼竿: {rod_name}")
        else:
            yield event.plain_result("卸下鱼竿失败")

    async def unequip_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        """卸下饰品命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查饰品是否存在且已装备
        accessory_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_accessory_instances WHERE user_id = ? AND id = ? AND is_equipped = TRUE",
            (user_id, accessory_id)
        )

        if not accessory_instance:
            yield event.plain_result("未找到已装备的指定饰品")
            return

        # 卸下饰品
        success = self.equipment_service.unequip_accessory(user_id, accessory_id)

        if success:
            accessory_template = self.db_manager.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (accessory_instance['accessory_template_id'],)
            )
            accessory_name = accessory_template['name'] if accessory_template else "未知饰品"
            yield event.plain_result(f"成功卸下饰品: {accessory_name}")
        else:
            yield event.plain_result("卸下饰品失败")