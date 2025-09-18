from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from .models.database import DatabaseManager
from .services.user_service import UserService
from .services.inventory_service import InventoryService
from .services.shop_service import ShopService
from .services.market_service import MarketService
from .services.sell_service import SellService
from .services.gacha_service import GachaService
from .services.other_service import OtherService
from .services.fishing_service import FishingService
from .services.equipment_service import EquipmentService
import threading
import time
import os

@register("gaismanor", "k1ngr4m", "集成农场渔场的游戏", "1.0.0")
class GaismanorPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        # 初始化数据库和服务
        self.db_manager = DatabaseManager()
        self.user_service = UserService(self.db_manager)
        self.inventory_service = InventoryService(self.db_manager)
        self.shop_service = ShopService(self.db_manager)
        self.market_service = MarketService(self.db_manager)
        self.sell_service = SellService(self.db_manager)
        self.gacha_service = GachaService(self.db_manager)
        self.other_service = OtherService(self.db_manager)
        self.fishing_service = FishingService(self.db_manager)
        self.equipment_service = EquipmentService(self.db_manager)

        # 获取配置
        self.secret_key = config.get("secret_key", "SecretKey")
        self.port = config.get("port", 6200)

        # 启动WebUI
        self.start_webui()

        logger.info("庄园插件初始化完成")

    def start_webui(self):
        """启动WebUI"""
        try:
            from .webui import start_webui, init_webui
            # 初始化WebUI
            init_webui(self.db_manager, self.secret_key)

            # 在单独的线程中启动Web服务器
            webui_thread = threading.Thread(target=start_webui, args=(self.port,), daemon=True)
            webui_thread.start()
            logger.info(f"庄园插件WebUI已启动，访问地址: http://localhost:{self.port}")
        except Exception as e:
            logger.error(f"启动WebUI失败: {e}")

    async def initialize(self):
        """插件初始化方法"""
        logger.info("庄园插件已加载")

    async def terminate(self):
        """插件销毁方法"""
        logger.info("庄园插件已卸载")

    # 🌟 基础命令
    @filter.command("注册")
    async def register_command(self, event: AstrMessageEvent):
        async for result in self.user_service.register_command(event):
            yield result

    @filter.command("钓鱼")
    async def fish_command(self, event: AstrMessageEvent):
        async for result in self.fishing_service.fish_command(event):
            yield result

    @filter.command("签到")
    async def sign_in_command(self, event: AstrMessageEvent):
        async for result in self.user_service.sign_in_command(event):
            yield result

    @filter.command("金币")
    async def gold_command(self, event: AstrMessageEvent):
        async for result in self.user_service.gold_command(event):
            yield result

    # 🎒 背包相关
    @filter.command("鱼塘")
    async def fish_pond_command(self, event: AstrMessageEvent):
        async for result in self.inventory_service.fish_pond_command(event):
            yield result

    @filter.command("鱼塘容量")
    async def fish_pond_capacity_command(self, event: AstrMessageEvent):
        async for result in self.inventory_service.fish_pond_capacity_command(event):
            yield result

    @filter.command("升级鱼塘")
    async def upgrade_fish_pond_command(self, event: AstrMessageEvent):
        async for result in self.inventory_service.upgrade_fish_pond_command(event):
            yield result

    @filter.command("鱼饵")
    async def bait_command(self, event: AstrMessageEvent):
        async for result in self.inventory_service.bait_command(event):
            yield result

    @filter.command("鱼竿")
    async def rod_command(self, event: AstrMessageEvent):
        async for result in self.equipment_service.rod_command(event):
            yield result

    # 🛒 商店与购买
    @filter.command("商店")
    async def shop_command(self, event: AstrMessageEvent):
        async for result in self.shop_service.shop_command(event):
            yield result

    @filter.command("商店 鱼竿")
    async def shop_rods_command(self, event: AstrMessageEvent):
        async for result in self.shop_service.shop_rods_command(event):
            yield result

    @filter.command("商店 鱼饵")
    async def shop_bait_command(self, event: AstrMessageEvent):
        async for result in self.shop_service.shop_bait_command(event):
            yield result

    @filter.command("购买鱼饵")
    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        async for result in self.shop_service.buy_bait_command(event, bait_id, quantity):
            yield result

    @filter.command("购买鱼竿")
    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.shop_service.buy_rod_command(event, rod_id):
            yield result

    @filter.command("使用鱼饵")
    async def use_bait_command(self, event: AstrMessageEvent, bait_id: int):
        async for result in self.shop_service.use_bait_command(event, bait_id):
            yield result

    @filter.command("使用鱼竿")
    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.equipment_service.use_rod_command(event, rod_id):
            yield result

    # 🛒 市场与购买
    @filter.command("市场")
    async def market_command(self, event: AstrMessageEvent):
        async for result in self.market_service.market_command(event):
            yield result

    @filter.command("上架鱼饵")
    async def list_bait_command(self, event: AstrMessageEvent, bait_id: int, price: int):
        async for result in self.market_service.list_bait_command(event, bait_id, price):
            yield result

    @filter.command("上架鱼竿")
    async def list_rod_command(self, event: AstrMessageEvent, rod_id: int, price: int):
        async for result in self.market_service.list_rod_command(event, rod_id, price):
            yield result

    @filter.command("购买")
    async def buy_item_command(self, event: AstrMessageEvent, item_id: int):
        async for result in self.market_service.buy_item_command(event, item_id):
            yield result

    # 💰 出售鱼类
    @filter.command("全部卖出")
    async def sell_all_command(self, event: AstrMessageEvent):
        async for result in self.sell_service.sell_all_command(event):
            yield result

    @filter.command("保留卖出")
    async def sell_keep_one_command(self, event: AstrMessageEvent):
        async for result in self.sell_service.sell_keep_one_command(event):
            yield result

    @filter.command("出售稀有度")
    async def sell_by_rarity_command(self, event: AstrMessageEvent, rarity: int):
        async for result in self.sell_service.sell_by_rarity_command(event, rarity):
            yield result

    @filter.command("出售鱼竿")
    async def sell_rod_command(self, event: AstrMessageEvent, rod_id: int):
        async for result in self.sell_service.sell_rod_command(event, rod_id):
            yield result

    @filter.command("出售鱼饵")
    async def sell_bait_command(self, event: AstrMessageEvent, bait_id: int):
        async for result in self.sell_service.sell_bait_command(event, bait_id):
            yield result

    # ✨ 抽卡系统
    @filter.command("抽卡")
    async def gacha_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_service.gacha_command(event, pool_id):
            yield result

    @filter.command("十连")
    async def ten_gacha_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_service.ten_gacha_command(event, pool_id):
            yield result

    @filter.command("查看卡池")
    async def view_gacha_pool_command(self, event: AstrMessageEvent, pool_id: int):
        async for result in self.gacha_service.view_gacha_pool_command(event, pool_id):
            yield result

    # ⚙️ 其他功能
    @filter.command("自动钓鱼")
    async def auto_fishing_command(self, event: AstrMessageEvent):
        async for result in self.other_service.auto_fishing_command(event):
            yield result

    @filter.command("排行榜")
    async def leaderboard_command(self, event: AstrMessageEvent):
        async for result in self.other_service.leaderboard_command(event):
            yield result

    @filter.command("鱼类图鉴")
    async def fish_gallery_command(self, event: AstrMessageEvent):
        async for result in self.other_service.fish_gallery_command(event):
            yield result

    # 帮助命令
    @filter.command("钓鱼帮助")
    async def help_command(self, event: AstrMessageEvent):
        """显示所有可用命令"""
        commands = [
            "🌟 基础命令:",
            "  /注册 - 注册账号",
            "  /钓鱼 - 开始钓鱼",
            "  /签到 - 每日签到",
            "  /金币 - 查看金币余额",
            "",
            "🎒 背包相关:",
            "  /鱼塘 - 查看鱼塘",
            "  /鱼塘容量 - 查看鱼塘容量",
            "  /升级鱼塘 - 升级鱼塘容量",
            "  /鱼饵 - 查看鱼饵背包",
            "  /鱼竿 - 查看鱼竿背包",
            "",
            "🛒 商店与购买:",
            "  /商店 - 查看商店",
            "  /商店 鱼竿 - 查看鱼竿商店",
            "  /商店 鱼饵 - 查看鱼饵商店",
            "  /购买鱼饵 <鱼饵ID> [数量] - 购买鱼饵",
            "  /购买鱼竿 <鱼竿ID> - 购买鱼竿",
            "  /使用鱼饵 <鱼饵ID> - 使用鱼饵",
            "  /使用鱼竿 <鱼竿ID> - 装备鱼竿",
            "",
            "🏪 市场与交易:",
            "  /市场 - 查看市场",
            "  /上架鱼饵 <鱼饵ID> <价格> - 上架鱼饵",
            "  /上架鱼竿 <鱼竿ID> <价格> - 上架鱼竿",
            "  /购买 <商品ID> - 购买商品",
            "",
            "💰 出售鱼类:",
            "  /全部卖出 - 出售所有鱼类",
            "  /保留卖出 - 保留每种鱼各一条，其余卖出",
            "  /出售稀有度 <稀有度> - 按稀有度出售鱼类",
            "  /出售鱼竿 <鱼竿ID> - 出售鱼竿",
            "  /出售鱼饵 <鱼饵ID> - 出售鱼饵",
            "",
            "✨ 抽卡系统:",
            "  /抽卡 <卡池ID> - 单次抽卡",
            "  /十连 <卡池ID> - 十连抽卡",
            "  /查看卡池 <卡池ID> - 查看卡池详情",
            "",
            "⚙️ 其他功能:",
            "  /自动钓鱼 - 开启/关闭自动钓鱼",
            "  /排行榜 - 查看金币排行榜",
            "  /鱼类图鉴 - 查看已捕获鱼类图鉴",
            "  /帮助 - 显示此帮助信息"
        ]

        help_text = "🎮 Gaismanor 庄园插件命令列表:\n\n" + "\n".join(commands)
        yield event.plain_result(help_text)