from typing import Optional
from ..models.user import User
from ..models.database import DatabaseManager
from astrbot.api.event import AstrMessageEvent
from .achievement_service import AchievementService
import time

class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_service = AchievementService(db_manager)

    async def register_command(self, event: AstrMessageEvent):
        """用户注册命令"""
        user_id = event.get_sender_id()
        platform = event.get_platform_name() or "unknown"
        nickname = event.get_sender_name() or f"用户{user_id[-4:]}"  # 如果没有昵称，使用ID后4位

        # 检查用户是否已存在
        existing_user = self.get_user(user_id)
        if existing_user:
            yield event.plain_result("您已经注册过了！")
            return

        # 创建新用户
        user = self.create_user(user_id, platform, nickname)
        yield event.plain_result(f"注册成功！欢迎 {nickname} 来到大gai庄园！\n\n您获得了初始金币: {user.gold}")

    async def sign_in_command(self, event: AstrMessageEvent):
        """签到命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查今日是否已签到
        today = time.strftime('%Y-%m-%d', time.localtime())
        existing_record = self.db.fetch_one(
            "SELECT * FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, today)
        )

        if existing_record:
            yield event.plain_result("您今天已经签到过了！")
            return

        # 计算连续签到天数
        yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))
        yesterday_record = self.db.fetch_one(
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
        self.update_user(user)

        # 记录签到
        self.db.execute_query(
            """INSERT INTO sign_in_logs
               (user_id, date, streak, reward_gold, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, today, streak, reward_gold, int(time.time()))
        )

        # 检查成就
        newly_unlocked = self.achievement_service.check_achievements(user)

        # 构造返回消息
        message = f"签到成功！\n\n获得金币: {reward_gold}\n\n连续签到: {streak}天"

        # 如果有新解锁的成就，添加到消息中
        if newly_unlocked:
            message += "\n\n🎉 恭喜解锁新成就！\n"
            for achievement in newly_unlocked:
                message += f"  · {achievement.name}: {achievement.description}\n"

        yield event.plain_result(message)

    async def gold_command(self, event: AstrMessageEvent):
        """查看金币命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        yield event.plain_result(f"您的金币余额: {user.gold}")

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        result = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return User(
                user_id=result['user_id'],
                platform=result['platform'],
                nickname=result['nickname'],
                gold=result['gold'],
                exp=result['exp'],
                level=result['level'],
                fishing_count=result['fishing_count'],
                total_fish_weight=result['total_fish_weight'],
                total_income=result['total_income'],
                last_fishing_time=result['last_fishing_time'],
                auto_fishing=result['auto_fishing'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None

    def create_user(self, user_id: str, platform: str, nickname: str) -> User:
        """创建新用户"""
        now = int(time.time())
        user = User(user_id=user_id, platform=platform, nickname=nickname, created_at=now, updated_at=now)

        self.db.execute_query(
            """INSERT INTO users (
                user_id, platform, nickname, gold, exp, level, fishing_count,
                total_fish_weight, total_income, last_fishing_time,
                auto_fishing, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user.user_id, user.platform, user.nickname, user.gold, user.exp, user.level,
                user.fishing_count, user.total_fish_weight, user.total_income,
                user.last_fishing_time, user.auto_fishing, user.created_at, user.updated_at
            )
        )
        return user

    def update_user(self, user: User) -> None:
        """更新用户信息"""
        user.updated_at = int(time.time())
        self.db.execute_query(
            """UPDATE users SET
                platform=?, nickname=?, gold=?, exp=?, level=?, fishing_count=?,
                total_fish_weight=?, total_income=?, last_fishing_time=?,
                auto_fishing=?, updated_at=?
            WHERE user_id=?""",
            (
                user.platform, user.nickname, user.gold, user.exp, user.level, user.fishing_count,
                user.total_fish_weight, user.total_income, user.last_fishing_time,
                user.auto_fishing, user.updated_at, user.user_id
            )
        )

    def add_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        user = self.get_user(user_id)
        if user:
            user.gold += amount
            self.update_user(user)
            return True
        return False

    def deduct_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        user = self.get_user(user_id)
        if user and user.gold >= amount:
            user.gold -= amount
            self.update_user(user)
            return True
        return False