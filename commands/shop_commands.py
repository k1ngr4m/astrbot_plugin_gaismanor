from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.shop_service import ShopService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager

class ShopCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.shop_service = ShopService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

    async def shop_command(self, event: AstrMessageEvent):
        """商店主命令"""
        shop_info = """=== 庄园商店 ===
欢迎来到庄园商店！您可以在这里购买各种钓鱼装备。

可用命令:
/商店 鱼竿  - 查看可购买的鱼竿
/商店 鱼饵  - 查看可购买的鱼饵
/购买鱼饵 <ID> [数量]  - 购买指定ID的鱼饵
/购买鱼竿 <ID>  - 购买指定ID的鱼竿
"""
        yield event.plain_result(shop_info)

    async def shop_rods_command(self, event: AstrMessageEvent):
        """查看鱼竿商店商品"""
        rods = self.shop_service.get_rod_shop_items()

        if not rods:
            yield event.plain_result("暂无鱼竿商品")
            return

        rod_info = "=== 鱼竿商店 ===\n"
        for rod in rods:
            rarity_stars = "★" * rod.rarity
            rod_info += f"ID: {rod.id} - {rod.name} {rarity_stars}\n"
            rod_info += f"  价格: {rod.price}金币  品质加成: +{rod.quality_mod}  数量加成: +{rod.quantity_mod}\n"
            rod_info += f"  描述: {rod.description}\n\n"

        yield event.plain_result(rod_info)

    async def shop_bait_command(self, event: AstrMessageEvent):
        """查看鱼饵商店商品"""
        bait_list = self.shop_service.get_bait_shop_items()

        if not bait_list:
            yield event.plain_result("暂无鱼饵商品")
            return

        bait_info = "=== 鱼饵商店 ===\n"
        for bait in bait_list:
            rarity_stars = "★" * bait.rarity
            bait_info += f"ID: {bait.id} - {bait.name} {rarity_stars}\n"
            bait_info += f"  价格: {bait.price}金币  效果: {bait.effect_description}\n"
            bait_info += f"  描述: {bait.description}\n\n"

        yield event.plain_result(bait_info)

    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        """购买鱼饵"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买鱼饵
        success = self.shop_service.buy_bait(user_id, bait_id, quantity)

        if success:
            bait_template = self.db_manager.fetch_one(
                "SELECT name FROM bait_templates WHERE id = ?",
                (bait_id,)
            )
            bait_name = bait_template['name'] if bait_template else "未知鱼饵"
            yield event.plain_result(f"成功购买鱼饵: {bait_name} x{quantity}")
        else:
            yield event.plain_result("购买鱼饵失败，请检查金币是否足够或商品是否存在")

    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """购买鱼竿"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买鱼竿
        success = self.shop_service.buy_rod(user_id, rod_id)

        if success:
            rod_template = self.db_manager.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功购买鱼竿: {rod_name}")
        else:
            yield event.plain_result("购买鱼竿失败，请检查金币是否足够或商品是否存在")

    async def use_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """使用鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼饵是否存在
        bait_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ? AND quantity > 0",
            (user_id, bait_id)
        )

        if not bait_instance:
            yield event.plain_result("您没有该鱼饵或数量不足")
            return

        # 使用鱼饵（这里简化处理，实际应该应用鱼饵效果）
        yield event.plain_result("鱼饵使用功能正在开发中，敬请期待！")

    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """装备鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在
        rod_instance = self.db_manager.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND rod_template_id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("您没有该鱼竿")
            return

        # 装备鱼竿
        success = self.equipment_service.equip_rod(user_id, rod_instance['id'])

        if success:
            rod_template = self.db_manager.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功装备鱼竿: {rod_name}")
        else:
            yield event.plain_result("装备鱼竿失败")