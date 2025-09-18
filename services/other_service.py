from typing import List, Optional
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
from .fishing_service import FishingService
from .achievement_service import AchievementService
import time
import threading
from datetime import datetime

class OtherService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.fishing_service = FishingService(db_manager)
        self.achievement_service = AchievementService(db_manager)
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

    async def fishing_log_command(self, event: AstrMessageEvent):
        """钓鱼记录命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户的钓鱼记录（最近20条）
        fishing_logs = self.db.fetch_all("""
            SELECT fl.*, ft.name as fish_name, ft.rarity as fish_rarity,
                   uri.rod_template_id, rt.name as rod_name,
                   ubi.bait_template_id, bt.name as bait_name
            FROM fishing_logs fl
            LEFT JOIN fish_templates ft ON fl.fish_template_id = ft.id
            LEFT JOIN user_rod_instances uri ON fl.rod_id = uri.id
            LEFT JOIN rod_templates rt ON uri.rod_template_id = rt.id
            LEFT JOIN user_bait_inventory ubi ON fl.bait_id = ubi.id
            LEFT JOIN bait_templates bt ON ubi.bait_template_id = bt.id
            WHERE fl.user_id = ?
            ORDER BY fl.timestamp DESC
            LIMIT 20
        """, (user_id,))

        if not fishing_logs:
            yield event.plain_result("暂无钓鱼记录！")
            return

        # 构造钓鱼记录信息
        log_info = "=== 钓鱼记录 ===\n\n"

        for log in fishing_logs:
            # 格式化时间
            log_time = datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M')

            # 钓鱼结果
            if log['success']:
                if log['fish_name']:
                    stars = "★" * log['fish_rarity']
                    log_info += f"[{log_time}] 钓鱼成功\n"
                    log_info += f"  钓到: {log['fish_name']} {stars}\n"
                    log_info += f"  重量: {log['fish_weight']:.2f}kg\n"
                    log_info += f"  价值: {log['fish_value']}金币\n"
                else:
                    log_info += f"[{log_time}] 钓鱼成功\n"
                    log_info += f"  钓到: 未知鱼类\n"
            else:
                log_info += f"[{log_time}] 钓鱼失败\n"

            # 使用的装备
            if log['rod_name']:
                log_info += f"  鱼竿: {log['rod_name']}\n"
            if log['bait_name']:
                log_info += f"  鱼饵: {log['bait_name']}\n"

            log_info += "\n"

        yield event.plain_result(log_info)

    async def view_achievements_command(self, event: AstrMessageEvent):
        """查看成就命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户成就
        achievements = self.achievement_service.get_user_achievements(user_id)

        if not achievements:
            yield event.plain_result("暂无成就数据！")
            return

        # 构造成就信息
        completed_count = sum(1 for a in achievements if a['completed'])
        total_count = len(achievements)

        achievement_info = f"=== 成就系统 ===\n\n"
        achievement_info += f"成就完成度: {completed_count}/{total_count}\n\n"

        # 按完成状态分组显示
        completed_achievements = [a for a in achievements if a['completed']]
        in_progress_achievements = [a for a in achievements if not a['completed']]

        if completed_achievements:
            achievement_info += "✅ 已完成:\n"
            for achievement in completed_achievements:
                completed_time = datetime.fromtimestamp(achievement['completed_at']).strftime('%Y-%m-%d %H:%M')
                achievement_info += f"  · {achievement['name']}: {achievement['description']}\n"
                achievement_info += f"    完成时间: {completed_time}\n\n"

        if in_progress_achievements:
            achievement_info += "🔄 进行中:\n"
            for achievement in in_progress_achievements:
                # 处理不同的目标值类型
                if isinstance(achievement['target_value'], (int, float)):
                    progress_text = f"{achievement['progress']}/{achievement['target_value']}"
                else:
                    progress_text = f"{achievement['progress']}/1" if achievement['target_value'] else "0/1"

                achievement_info += f"  · {achievement['name']}: {achievement['description']}\n"
                achievement_info += f"    进度: {progress_text}\n\n"

        yield event.plain_result(achievement_info)

    async def view_titles_command(self, event: AstrMessageEvent):
        """查看称号命令"""
        user_id = event.get_sender_id()

        # 检查用户是否已注册
        user = self.db.fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取用户称号
        titles = self.achievement_service.get_user_titles(user_id)

        if not titles:
            yield event.plain_result("暂无称号数据！")
            return

        # 构造称号信息
        title_info = "=== 称号系统 ===\n\n"

        active_title = None
        inactive_titles = []

        for title in titles:
            if title['is_active']:
                active_title = title
            else:
                inactive_titles.append(title)

        if active_title:
            acquired_time = datetime.fromtimestamp(active_title['acquired_at']).strftime('%Y-%m-%d %H:%M')
            title_info += f"👑 当前称号: {active_title['name']}\n"
            title_info += f"  描述: {active_title['description']}\n"
            title_info += f"  获得时间: {acquired_time}\n\n"

        if inactive_titles:
            title_info += "📦 其他称号:\n"
            for title in inactive_titles:
                acquired_time = datetime.fromtimestamp(title['acquired_at']).strftime('%Y-%m-%d %H:%M')
                title_info += f"  · {title['name']}: {title['description']}\n"
                title_info += f"    获得时间: {acquired_time}\n\n"

        yield event.plain_result(title_info)