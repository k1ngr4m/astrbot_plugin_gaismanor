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

    def _calculate_level(self, exp: int) -> int:
        """根据经验计算等级"""
        # 每级所需经验 = 100 * 等级^2
        # 使用逆向计算：level = sqrt(exp / 100) + 1
        import math
        level = int(math.sqrt(exp / 100)) + 1

        # 最大等级限制为100级
        return min(level, 100)

    def _get_exp_for_level(self, level: int) -> int:
        """获取升级到指定等级所需的总经验"""
        # 每级所需经验 = 100 * 等级^2
        # 最大等级限制为100级
        capped_level = min(level, 100)
        return 100 * (capped_level ** 2)

    def _get_level_up_reward(self, level: int) -> int:
        """根据等级获取升级奖励金币"""
        if 1 <= level <= 10:
            return 50
        elif 11 <= level <= 20:
            return 100
        elif 21 <= level <= 30:
            return 200
        elif 31 <= level <= 40:
            return 400
        elif 41 <= level <= 50:
            return 800
        elif 51 <= level <= 60:
            return 1600
        elif 61 <= level <= 70:
            return 3200
        elif 71 <= level <= 80:
            return 6400
        elif 81 <= level <= 90:
            return 12800
        elif 91 <= level <= 100:
            return 25600
        else:
            return 0

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
        # 计算经验奖励 (基础10经验 + 连续签到奖励)
        reward_exp = 10 + (streak - 1) * 2

        # 添加金币和经验
        user.gold += reward_gold
        user.exp += reward_exp

        # 检查是否升级
        old_level = user.level
        new_level = self._calculate_level(user.exp)

        # 如果升级了，给予金币奖励
        level_up_reward = 0
        if new_level > old_level:
            for level in range(old_level + 1, new_level + 1):
                level_up_reward += self._get_level_up_reward(level)
            user.gold += level_up_reward

        user.level = new_level

        # 更新用户数据
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
        level_up_message = ""
        if user.level > old_level:
            if level_up_reward > 0:
                level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！获得金币奖励: {level_up_reward}"
            else:
                if user.level >= 100:
                    level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！您已达到最高等级！"
                else:
                    level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！"

        message = f"签到成功！\n\n获得金币: {reward_gold}\n获得经验: {reward_exp}点{level_up_message}\n\n连续签到: {streak}天"

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

    async def level_command(self, event: AstrMessageEvent):
        """查看等级和经验命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 计算升级到下一级所需的经验
        current_level_required_exp = self._get_exp_for_level(user.level - 1) if user.level > 1 else 0
        next_level_required_exp = self._get_exp_for_level(user.level)
        exp_in_current_level = user.exp - current_level_required_exp
        exp_needed = next_level_required_exp - user.exp
        exp_for_current_level = next_level_required_exp - current_level_required_exp

        message = f"📊 等级信息\n\n"
        message += f"当前等级: {user.level}\n\n"
        message += f"当前经验: {user.exp}\n\n"

        if user.level >= 100:
            message += "恭喜您已达到最高等级！\n\n"
            message += "您已解锁所有等级特权！"
        else:
            message += f"升级进度: {exp_in_current_level}/{exp_for_current_level}\n\n"
            if exp_needed > 0:
                message += f"距离升级还需: {exp_needed} 经验\n\n"

                # 显示下一级升级奖励
                next_reward = self._get_level_up_reward(user.level + 1)
                message += f"下一等级奖励: {next_reward} 金币"
            else:
                message += "恭喜您已达到最高等级！\n\n"

        yield event.plain_result(message)

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
                total_fishing_count=result['total_fishing_count'],
                total_coins_earned=result['total_coins_earned'],
                fish_pond_capacity=result['fish_pond_capacity'],
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
                auto_fishing, total_fishing_count, total_coins_earned, fish_pond_capacity, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user.user_id, user.platform, user.nickname, user.gold, user.exp, user.level,
                user.fishing_count, user.total_fish_weight, user.total_income,
                user.last_fishing_time, user.auto_fishing, user.total_fishing_count,
                user.total_coins_earned, user.fish_pond_capacity, user.created_at, user.updated_at
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
                auto_fishing=?, total_fishing_count=?, total_coins_earned=?, fish_pond_capacity=?, updated_at=?
            WHERE user_id=?""",
            (
                user.platform, user.nickname, user.gold, user.exp, user.level, user.fishing_count,
                user.total_fish_weight, user.total_income, user.last_fishing_time,
                user.auto_fishing, user.total_fishing_count, user.total_coins_earned, user.fish_pond_capacity, user.updated_at, user.user_id
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