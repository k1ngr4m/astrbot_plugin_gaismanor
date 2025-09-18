from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager
import time

class OtherCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

    async def auto_fishing_command(self, event: AstrMessageEvent):
        """自动钓鱼命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 切换自动钓鱼状态
        user.auto_fishing = not user.auto_fishing
        self.user_service.update_user(user)

        status = "开启" if user.auto_fishing else "关闭"
        yield event.plain_result(f"自动钓鱼功能已{status}")

    async def leaderboard_command(self, event: AstrMessageEvent):
        """排行榜命令"""
        # 获取钓鱼次数排行榜（前10名）
        top_fishers = self.db_manager.fetch_all(
            """SELECT nickname, fishing_count, total_fish_weight, total_income
               FROM users
               ORDER BY fishing_count DESC
               LIMIT 10"""
        )

        if not top_fishers:
            yield event.plain_result("暂无排行榜数据")
            return

        # 构建排行榜信息
        leaderboard_info = "=== 钓鱼排行榜 ===\n"
        for i, user in enumerate(top_fishers, 1):
            leaderboard_info += f"{i}. {user['nickname']}\n"
            leaderboard_info += f"   钓鱼次数: {user['fishing_count']}  总重量: {user['total_fish_weight']:.2f}kg  总收入: {user['total_income']}金币\n\n"

        yield event.plain_result(leaderboard_info)

    async def fish_gallery_command(self, event: AstrMessageEvent):
        """鱼类图鉴命令"""
        # 获取所有鱼类模板
        fish_templates = self.db_manager.fetch_all(
            "SELECT * FROM fish_templates ORDER BY rarity, id"
        )

        if not fish_templates:
            yield event.plain_result("暂无鱼类图鉴数据")
            return

        # 构建图鉴信息
        gallery_info = "=== 鱼类图鉴 ===\n"
        current_rarity = 0

        for fish in fish_templates:
            # 按稀有度分组
            if fish['rarity'] != current_rarity:
                current_rarity = fish['rarity']
                rarity_stars = "★" * current_rarity
                gallery_info += f"\n{rarity_stars} 稀有度 {current_rarity}:\n"

            gallery_info += f"  {fish['name']} - {fish['description']}\n"
            gallery_info += f"    基础价值: {fish['base_value']}金币  重量范围: {fish['min_weight']/1000:.1f}-{fish['max_weight']/1000:.1f}kg\n\n"

        yield event.plain_result(gallery_info)