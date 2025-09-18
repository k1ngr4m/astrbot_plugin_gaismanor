from typing import List, Optional
from astrbot.core.platform import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
from .fishing_service import FishingService
import time
import threading

class OtherService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.fishing_service = FishingService(db_manager)
        # 启动自动钓鱼检查线程
        self.auto_fishing_thread = threading.Thread(target=self._auto_fishing_loop, daemon=True)
        self.auto_fishing_thread.start()

    async def auto_fishing_command(self, event: AstrMessageEvent):
        """自动钓鱼命令"""
        user_id = event.get_sender_id()

        # 获取用户信息
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 切换自动钓鱼状态
        new_auto_fishing = not user['auto_fishing']

        self.db.execute_query(
            "UPDATE users SET auto_fishing = ? WHERE user_id = ?",
            (new_auto_fishing, user_id)
        )

        status = "开启" if new_auto_fishing else "关闭"
        yield event.plain_result(f"自动钓鱼功能已{status}！")

    def _auto_fishing_loop(self):
        """自动钓鱼检查循环"""
        while True:
            try:
                # 获取所有开启自动钓鱼的用户
                auto_fishing_users = self.db.fetch_all(
                    "SELECT * FROM users WHERE auto_fishing = TRUE"
                )

                for user_data in auto_fishing_users:
                    # 创建 User 对象
                    user = User(
                        user_id=user_data['user_id'],
                        platform=user_data['platform'],
                        nickname=user_data['nickname'],
                        gold=user_data['gold'],
                        exp=user_data['exp'],
                        level=user_data['level'],
                        fishing_count=user_data['fishing_count'],
                        total_fish_weight=user_data['total_fish_weight'],
                        total_income=user_data['total_income'],
                        last_fishing_time=user_data['last_fishing_time'],
                        auto_fishing=user_data['auto_fishing'],
                        created_at=user_data['created_at'],
                        updated_at=user_data['updated_at']
                    )

                    # 检查是否可以钓鱼
                    can_fish, _ = self.fishing_service.can_fish(user)
                    if can_fish:
                        # 执行钓鱼
                        result = self.fishing_service.fish(user)

                        # 更新用户数据
                        self.db.execute_query(
                            """UPDATE users SET
                               platform=?, gold=?, fishing_count=?, last_fishing_time=?, total_fish_weight=?, total_income=?
                               WHERE user_id=?""",
                            (user.platform, user.gold, user.fishing_count, user.last_fishing_time,
                             user.total_fish_weight, user.total_income, user.user_id)
                        )

                # 每30秒检查一次
                time.sleep(30)
            except Exception as e:
                print(f"自动钓鱼循环出错: {e}")
                time.sleep(30)

    async def leaderboard_command(self, event: AstrMessageEvent):
        """排行榜命令"""
        # 获取金币排行榜 (前10名)
        gold_leaderboard = self.db.fetch_all("""
            SELECT nickname, gold
            FROM users
            ORDER BY gold DESC
            LIMIT 10
        """)

        # 获取钓鱼次数排行榜 (前10名)
        fishing_count_leaderboard = self.db.fetch_all("""
            SELECT nickname, fishing_count
            FROM users
            ORDER BY fishing_count DESC
            LIMIT 10
        """)

        # 获取总收益排行榜 (前10名)
        income_leaderboard = self.db.fetch_all("""
            SELECT nickname, total_income
            FROM users
            ORDER BY total_income DESC
            LIMIT 10
        """)

        # 构造排行榜信息
        leaderboard_info = "=== 庄园钓鱼排行榜 ===\n\n"

        # 金币排行榜
        leaderboard_info += "💰 金币排行榜:\n"
        if gold_leaderboard:
            for i, user in enumerate(gold_leaderboard, 1):
                leaderboard_info += f"{i}. {user['nickname']}: {user['gold']}金币\n"
        else:
            leaderboard_info += "暂无数据\n"

        leaderboard_info += "\n"

        # 钓鱼次数排行榜
        leaderboard_info += "🎣 钓鱼次数排行榜:\n"
        if fishing_count_leaderboard:
            for i, user in enumerate(fishing_count_leaderboard, 1):
                leaderboard_info += f"{i}. {user['nickname']}: {user['fishing_count']}次\n"
        else:
            leaderboard_info += "暂无数据\n"

        leaderboard_info += "\n"

        # 总收益排行榜
        leaderboard_info += "📈 总收益排行榜:\n"
        if income_leaderboard:
            for i, user in enumerate(income_leaderboard, 1):
                leaderboard_info += f"{i}. {user['nickname']}: {user['total_income']}金币\n"
        else:
            leaderboard_info += "暂无数据\n"

        yield event.plain_result(leaderboard_info)

    async def fish_gallery_command(self, event: AstrMessageEvent):
        """鱼类图鉴命令"""
        # 获取所有鱼类模板
        fish_templates = self.db.fetch_all("""
            SELECT id, name, description, rarity, base_value
            FROM fish_templates
            ORDER BY rarity DESC, base_value DESC
        """)

        if not fish_templates:
            yield event.plain_result("暂无鱼类数据！")
            return

        # 构造鱼类图鉴信息
        gallery_info = "=== 鱼类图鉴 ===\n\n"

        # 按稀有度分组显示
        current_rarity = None
        for fish in fish_templates:
            if current_rarity != fish['rarity']:
                current_rarity = fish['rarity']
                stars = "★" * current_rarity
                gallery_info += f"{stars} ({current_rarity}星鱼类):\n"

            gallery_info += f"  · {fish['name']}\n"
            gallery_info += f"    描述: {fish['description']}\n"
            gallery_info += f"    基础价值: {fish['base_value']}金币\n\n"

        yield event.plain_result(gallery_info)