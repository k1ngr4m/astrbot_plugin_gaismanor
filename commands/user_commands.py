from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.fishing_service import FishingService
from ..services.equipment_service import EquipmentService
from ..services.shop_service import ShopService
from ..models.database import DatabaseManager
import time

class UserCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.fishing_service = FishingService(db_manager)
        self.equipment_service = EquipmentService(db_manager)
        self.shop_service = ShopService(db_manager)

    async def register_command(self, event: AstrMessageEvent):
        """用户注册命令"""
        user_id = event.get_sender_id()
        nickname = event.get_sender_name() or f"用户{user_id[-4:]}"  # 如果没有昵称，使用ID后4位

        # 检查用户是否已存在
        existing_user = self.user_service.get_user(user_id)
        if existing_user:
            yield event.plain_result("您已经注册过了！")
            return

        # 创建新用户
        user = self.user_service.create_user(user_id, nickname)
        yield event.plain_result(f"注册成功！欢迎 {nickname} 来到庄园钓鱼世界！\n您获得了初始金币: {user.gold}枚")

    async def status_command(self, event: AstrMessageEvent):
        """查看用户状态命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取装备信息
        equipped_rod = self.equipment_service.get_equipped_rod(user_id)
        equipped_accessory = self.equipment_service.get_equipped_accessory(user_id)

        # 构建状态信息
        status_info = f"""=== {user.nickname} 的状态 ===
金币: {user.gold}
经验值: {user.exp}
等级: {user.level}
钓鱼次数: {user.fishing_count}
累计鱼重: {user.total_fish_weight:.2f}kg
累计收入: {user.total_income}金币
自动钓鱼: {'开启' if user.auto_fishing else '关闭'}
上次钓鱼: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(user.last_fishing_time)) if user.last_fishing_time else '从未'}
"""

        if equipped_rod:
            status_info += f"\n装备鱼竿: {equipped_rod.name}(+{equipped_rod.catch_bonus}捕获率, +{equipped_rod.weight_bonus}重量)"

        if equipped_accessory:
            status_info += f"\n装备饰品: {equipped_accessory.name}(+{equipped_accessory.effect_value}{equipped_accessory.effect_type})"

        yield event.plain_result(status_info)

    async def fish_command(self, event: AstrMessageEvent):
        """钓鱼命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 执行钓鱼
        result = self.fishing_service.fish(user)

        # 更新用户信息
        if result.success or "冷却中" not in result.message:
            self.user_service.update_user(user)

        yield event.plain_result(result.message)

    async def sign_in_command(self, event: AstrMessageEvent):
        """签到命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查今日是否已签到
        today = time.strftime('%Y-%m-%d', time.localtime())
        existing_record = self.db_manager.fetch_one(
            "SELECT * FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, today)
        )

        if existing_record:
            yield event.plain_result("您今天已经签到过了！")
            return

        # 计算连续签到天数
        yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))
        yesterday_record = self.db_manager.fetch_one(
            "SELECT streak FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, yesterday)
        )

        streak = 1
        if yesterday_record:
            streak = yesterday_record['streak'] + 1

        # 计算奖励 (基础100金币 + 连续签到奖励)
        reward_gold = 100 + (streak - 1) * 20

        # 添加金币
        user.gold += reward_gold
        self.user_service.update_user(user)

        # 记录签到
        self.db_manager.execute_query(
            """INSERT INTO sign_in_logs
               (user_id, date, streak, reward_gold, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, today, streak, reward_gold, int(time.time()))
        )

        yield event.plain_result(f"签到成功！\n获得金币: {reward_gold}枚\n连续签到: {streak}天")

    async def inventory_command(self, event: AstrMessageEvent):
        """查看背包命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取鱼类库存
        fish_inventory = self.user_service.get_user_fish_inventory(user_id)

        # 获取装备库存
        rods = self.equipment_service.get_user_rods(user_id)
        accessories = self.equipment_service.get_user_accessories(user_id)
        bait = self.equipment_service.get_user_bait(user_id)

        # 构建背包信息
        inventory_info = f"=== {user.nickname} 的背包 ===\n\n"

        # 鱼类库存
        if fish_inventory:
            inventory_info += "🐟 鱼类库存:\n"
            for fish in fish_inventory:
                fish_template = self.db_manager.fetch_one(
                    "SELECT name FROM fish_templates WHERE id = ?",
                    (fish.fish_template_id,)
                )
                if fish_template:
                    inventory_info += f"  • {fish_template['name']} - {fish.weight:.2f}kg - {fish.value}金币\n"
        else:
            inventory_info += "🐟 鱼类库存: 暂无\n"

        inventory_info += "\n"

        # 鱼竿库存
        if rods:
            inventory_info += "🎣 鱼竿库存:\n"
            for rod in rods:
                equip_status = " [装备中]" if rod.is_equipped else ""
                inventory_info += f"  • {rod.name}(+{rod.catch_bonus}捕获率) - 等级:{rod.level}{equip_status}\n"
        else:
            inventory_info += "🎣 鱼竿库存: 暂无\n"

        inventory_info += "\n"

        # 饰品库存
        if accessories:
            inventory_info += "💎 饰品库存:\n"
            for accessory in accessories:
                equip_status = " [装备中]" if accessory.is_equipped else ""
                inventory_info += f"  • {accessory.name}(+{accessory.effect_value}{accessory.effect_type}){equip_status}\n"
        else:
            inventory_info += "💎 饰品库存: 暂无\n"

        inventory_info += "\n"

        # 鱼饵库存
        if bait:
            inventory_info += "🍖 鱼饵库存:\n"
            for b in bait:
                inventory_info += f"  • {b.name}(+{b.catch_rate_bonus}捕获率) - 持续:{b.duration}秒\n"
        else:
            inventory_info += "🍖 鱼饵库存: 暂无\n"

        yield event.plain_result(inventory_info)