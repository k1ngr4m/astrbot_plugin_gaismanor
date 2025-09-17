from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.shop_service import ShopService
from ..models.database import DatabaseManager

class ShopCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.shop_service = ShopService(db_manager)

    async def shop_command(self, event: AstrMessageEvent):
        """商店主命令"""
        shop_info = """=== 庄园商店 ===
欢迎来到庄园商店！您可以在这里购买各种钓鱼装备。

可用命令:
/商店 鱼竿  - 查看鱼竿商品
/商店 饰品  - 查看饰品商品
/商店 鱼饵  - 查看鱼饵商品
/购买 鱼竿 <ID>  - 购买鱼竿
/购买 饰品 <ID>  - 购买饰品
/购买 鱼饵 <ID> [数量]  - 购买鱼饵
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
            rod_info += f"ID: {rod.id} - {rod.name} - 稀有度:{rod.rarity}星\n"
            rod_info += f"  价格: {rod.price}金币  捕获加成: +{rod.catch_bonus}  重量加成: +{rod.weight_bonus}\n"
            rod_info += f"  描述: {rod.description}\n\n"

        yield event.plain_result(rod_info)

    async def shop_accessories_command(self, event: AstrMessageEvent):
        """查看饰品商店商品"""
        accessories = self.shop_service.get_accessory_shop_items()

        if not accessories:
            yield event.plain_result("暂无饰品商品")
            return

        accessory_info = "=== 饰品商店 ===\n"
        for accessory in accessories:
            accessory_info += f"ID: {accessory.id} - {accessory.name} - 稀有度:{accessory.rarity}星\n"
            accessory_info += f"  价格: {accessory.price}金币  效果: +{accessory.effect_value}{accessory.effect_type}\n"
            accessory_info += f"  描述: {accessory.description}\n\n"

        yield event.plain_result(accessory_info)

    async def shop_bait_command(self, event: AstrMessageEvent):
        """查看鱼饵商店商品"""
        bait_list = self.shop_service.get_bait_shop_items()

        if not bait_list:
            yield event.plain_result("暂无鱼饵商品")
            return

        bait_info = "=== 鱼饵商店 ===\n"
        for bait in bait_list:
            bait_info += f"ID: {bait.id} - {bait.name} - 稀有度:{bait.rarity}星\n"
            bait_info += f"  价格: {bait.price}金币  捕获率加成: +{bait.catch_rate_bonus}  持续时间: {bait.duration}秒\n"
            bait_info += f"  描述: {bait.description}\n\n"

        yield event.plain_result(bait_info)

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

    async def buy_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        """购买饰品"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买饰品
        success = self.shop_service.buy_accessory(user_id, accessory_id)

        if success:
            accessory_template = self.db_manager.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (accessory_id,)
            )
            accessory_name = accessory_template['name'] if accessory_template else "未知饰品"
            yield event.plain_result(f"成功购买饰品: {accessory_name}")
        else:
            yield event.plain_result("购买饰品失败，请检查金币是否足够或商品是否存在")

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