from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from .models.database import DatabaseManager
from .commands.user_commands import UserCommands
from .commands.inventory_commands import InventoryCommands
from .commands.shop_commands import ShopCommands
from .commands.market_commands import MarketCommands
from .commands.sell_commands import SellCommands
from .commands.gacha_commands import GachaCommands
from .commands.other_commands import OtherCommands

@register("gaismanor", "k1ngr4m", "集成农场渔场的游戏", "1.0.0")
class GaismanorPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context
        # 初始化数据库和服务
        self.db_manager = DatabaseManager()
        self.user_commands = UserCommands(self.db_manager)
        self.inventory_commands = InventoryCommands(self.db_manager)
        self.shop_commands = ShopCommands(self.db_manager)
        self.market_commands = MarketCommands(self.db_manager)
        self.sell_commands = SellCommands(self.db_manager)
        self.gacha_commands = GachaCommands(self.db_manager)
        self.other_commands = OtherCommands(self.db_manager)
        logger.info("庄园插件初始化完成")

    async def initialize(self):
        """插件初始化方法"""
        logger.info("庄园插件已加载")

    async def terminate(self):
        """插件销毁方法"""
        logger.info("庄园插件已卸载")

    # 🌟 基础命令
    @filter.command("注册")
    async def register_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.register_command(event):
            yield result

    @filter.command("钓鱼")
    async def fish_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.fish_command(event):
            yield result

    @filter.command("签到")
    async def sign_in_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.sign_in_command(event):
            yield result

    @filter.command("金币")
    async def gold_command(self, event: AstrMessageEvent):
        async for result in self.user_commands.gold_command(event):
            yield result

    # 🎒 背包相关
    @filter.command("鱼塘")
    async def fish_pond_command(self, event: AstrMessageEvent):
        async for result in self.inventory_commands.fish_pond_command(event):
            yield result

    @filter.command("鱼塘容量")
    async def fish_pond_capacity_command(self, event: AstrMessageEvent):
        async for result in self.inventory_commands.fish_pond_capacity_command(event):
            yield result

    @filter.command("升级鱼塘")
    async def upgrade_fish_pond_command(self, event: AstrMessageEvent):
        async for result in self.inventory_commands.upgrade_fish_pond_command(event):
            yield result

    @filter.command("鱼饵")
    async def bait_command(self, event: AstrMessageEvent):
        async for result in self.inventory_commands.bait_command(event):
            yield result

    @filter.command("鱼竿")
    async def rod_command(self, event: AstrMessageEvent):
        async for result in self.inventory_commands.rod_command(event):
            yield result

    # 🛒 商店与购买
    @filter.command("商店")
    async def shop_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_command(event):
            yield result

    @filter.command("商店 鱼竿")
    async def shop_rods_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_rods_command(event):
            yield result

    @filter.command("商店 鱼饵")
    async def shop_bait_command(self, event: AstrMessageEvent):
        async for result in self.shop_commands.shop_bait_command(event):
            yield result

    @filter.command("购买鱼饵")
    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        async for result in self.shop_commands.buy_bait_command(event, bait_id, quantity):
            yield result

    @filter.command("购买鱼竿")
    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.shop_commands.buy_rod_command(event, rod_id):
            yield result

    @filter.command("使用鱼饵")
    async def use_bait_command(self, event: AstrMessageEvent, bait_id: int):
        async for result in self.shop_commands.use_bait_command(event, bait_id):
            yield result

    @filter.command("使用鱼竿")
    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.shop_commands.use_rod_command(event, rod_id):
            yield result

    # 🛒 市场与购买
    @filter.command("市场")
    async def market_command(self, event: AstrMessageEvent):
        async for result in self.market_commands.market_command(event):
            yield result

    @filter.command("上架鱼饵")
    async def list_bait_command(self, event: AstrMessageEvent, bait_id: int, price: int):
        async for result in self.market_commands.list_bait_command(event, bait_id, price):
            yield result

    @filter.command("上架鱼竿")
    async def list_rod_command(self, event: AstrMessageEvent, rod_id: int, price: int):
        async for result in self.market_commands.list_rod_command(event, rod_id, price):
            yield result

    @filter.command("购买")
    async def buy_item_command(self, event: AstrMessageEvent, item_id: int):
        async for result in self.market_commands.buy_item_command(event, item_id):
            yield result

    # 💰 出售鱼类
    @filter.command("全部卖出")
    async def sell_all_command(self, event: AstrMessageEvent):
        async for result in self.sell_commands.sell_all_command(event):
            yield result

    @filter.command("保留卖出")
    async def sell_keep_one_command(self, event: AstrMessageEvent):
        async for result in self.sell_commands.sell_keep_one_command(event):
            yield result

    @filter.command("出售稀有度")
    async def sell_by_rarity_command(self, event: AstrMessageEvent, rarity: int):
        async for result in self.sell_commands.sell_by_rarity_command(event, rarity):
            yield result

    @filter.command("出售鱼竿")
    async def sell_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.sell_commands.sell_rod_command(event, rod_id):
            yield result

    @filter.command("出售鱼饵")
    async def sell_bait_command(self, event: AstrMessageEvent, bait_id: int):
        async for result in self.sell_commands.sell_bait_command(event, bait_id):
            yield result

    # ✨ 抽卡系统
    @filter.command("抽卡")
    async def gacha_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_commands.gacha_command(event, pool_id):
            yield result

    @filter.command("十连")
    async def ten_gacha_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_commands.ten_gacha_command(event, pool_id):
            yield result

    @filter.command("查看卡池")
    async def view_gacha_pool_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_commands.view_gacha_pool_command(event, pool_id):
            yield result

    # ⚙️ 其他功能
    @filter.command("自动钓鱼")
    async def auto_fishing_command(self, event: AstrMessageEvent):
        async for result in self.other_commands.auto_fishing_command(event):
            yield result

    @filter.command("排行榜")
    async def leaderboard_command(self, event: AstrMessageEvent):
        async for result in self.other_commands.leaderboard_command(event):
            yield result

    @filter.command("鱼类图鉴")
    async def fish_gallery_command(self, event: AstrMessageEvent):
        async for result in self.other_commands.fish_gallery_command(event):
            yield result