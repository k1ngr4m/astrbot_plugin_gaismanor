from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .models.database import DatabaseManager
from .commands.user_commands import UserCommands
from .commands.equipment_commands import EquipmentCommands
from .commands.shop_commands import ShopCommands

@register("gaismanor", "k1ngr4m", "集成农场渔场的游戏", "1.0.0")
class GaismanorPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context
        # 初始化数据库和服务
        self.db_manager = DatabaseManager()
        self.user_commands = UserCommands(self.db_manager)
        self.equipment_commands = EquipmentCommands(self.db_manager)
        self.shop_commands = ShopCommands(self.db_manager)
        logger.info("庄园插件初始化完成")

    async def initialize(self):
        """插件初始化方法"""
        logger.info("庄园插件已加载")

    async def terminate(self):
        """插件销毁方法"""
        logger.info("庄园插件已卸载")

    # 用户相关命令
    @filter.command("注册")
    async def register_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.register_command(event):
            yield result

    @filter.command("状态")
    async def status_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.status_command(event):
            yield result

    @filter.command("钓鱼")
    async def fish_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.fish_command(event):
            yield result

    @filter.command("签到")
    async def sign_in_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.sign_in_command(event):
            yield result

    @filter.command("背包")
    async def inventory_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.inventory_command(event):
            yield result

    # 装备相关命令
    @filter.command("鱼竿")
    async def rod_command(self, event: AstrMessageEvent):
        async for result in self.equipment_commands.rod_command(event):
            yield result

    @filter.command("饰品")
    async def accessory_command(self, event: AstrMessageEvent):
        async for result in self.equipment_commands.accessory_command(event):
            yield result

    @filter.command("鱼饵")
    async def bait_command(self, event: AstrMessageEvent):
        async for result in self.equipment_commands.bait_command(event):
            yield result

    @filter.command("装备鱼竿")
    async def equip_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.equipment_commands.equip_rod_command(event, rod_id):
            yield result

    @filter.command("装备饰品")
    async def equip_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        async for result in self.equipment_commands.equip_accessory_command(event, accessory_id):
            yield result

    @filter.command("卸下鱼竿")
    async def unequip_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.equipment_commands.unequip_rod_command(event, rod_id):
            yield result

    @filter.command("卸下饰品")
    async def unequip_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        async for result in self.equipment_commands.unequip_accessory_command(event, accessory_id):
            yield result

    # 商店相关命令
    @filter.command("商店")
    async def shop_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_command(event):
            yield result

    @filter.command("商店 鱼竿")
    async def shop_rods_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_rods_command(event):
            yield result

    @filter.command("商店 饰品")
    async def shop_accessories_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_accessories_command(event):
            yield result

    @filter.command("商店 鱼饵")
    async def shop_bait_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_bait_command(event):
            yield result

    @filter.command("购买 鱼竿")
    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.shop_commands.buy_rod_command(event, rod_id):
            yield result

    @filter.command("购买 饰品")
    async def buy_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        async for result in self.shop_commands.buy_accessory_command(event, accessory_id):
            yield result

    @filter.command("购买 鱼饵")
    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        async for result in self.shop_commands.buy_bait_command(event, bait_id, quantity):
            yield result