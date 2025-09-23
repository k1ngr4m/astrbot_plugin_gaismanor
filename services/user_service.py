from typing import Optional, List, Tuple
import math
import time
from ..models.user import User
from ..models.database import DatabaseManager
from astrbot.api.event import AstrMessageEvent
from .achievement_service import AchievementService
from .technology_service import TechnologyService
from ..services.equipment_service import EquipmentService

# 常量定义
MAX_LEVEL = 100
BASE_EXP_PER_LEVEL = 100
SIGN_IN_BASE_GOLD = 100
SIGN_IN_BASE_EXP = 10
SIGN_IN_STREAK_GOLD_INCREMENT = 20
SIGN_IN_STREAK_EXP_INCREMENT = 2
STARTER_ROD_TEMPLATE_ID = 1


class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_service = AchievementService(db_manager)

        # 预计算等级奖励，避免重复计算
        self._level_rewards = self._precompute_level_rewards()

    def _precompute_level_rewards(self) -> List[int]:
        """预计算各级别升级奖励"""
        rewards = [0] * (MAX_LEVEL + 2)  # 索引从0到101

        # 1-10级
        for level in range(1, 11):
            rewards[level] = 50

        # 11-20级
        for level in range(11, 21):
            rewards[level] = 100

        # 21-30级
        for level in range(21, 31):
            rewards[level] = 200

        # 31-40级
        for level in range(31, 41):
            rewards[level] = 400

        # 41-50级
        for level in range(41, 51):
            rewards[level] = 800

        # 51-60级
        for level in range(51, 61):
            rewards[level] = 1600

        # 61-70级
        for level in range(61, 71):
            rewards[level] = 3200

        # 71-80级
        for level in range(71, 81):
            rewards[level] = 6400

        # 81-90级
        for level in range(81, 91):
            rewards[level] = 12800

        # 91-100级
        for level in range(91, 101):
            rewards[level] = 25600

        return rewards

    def _calculate_level(self, exp: int) -> int:
        """根据经验计算等级"""
        if exp <= 0:
            return 1

        # 每级所需经验 = 100 * 等级^2
        level = int(math.sqrt(exp / BASE_EXP_PER_LEVEL)) + 1
        return min(level, MAX_LEVEL)

    def _get_exp_for_level(self, level: int) -> int:
        """获取升级到指定等级所需的总经验"""
        capped_level = max(1, min(level, MAX_LEVEL))
        return BASE_EXP_PER_LEVEL * (capped_level ** 2)

    def _get_level_up_reward(self, level: int) -> int:
        """根据等级获取升级奖励金币"""
        if 1 <= level <= MAX_LEVEL:
            return self._level_rewards[level]
        return 0

    def check_and_unlock_technologies(self, user: User) -> List:
        """检查并自动解锁符合条件的科技"""
        tech_service = TechnologyService(self.db)

        # 获取所有科技和用户已解锁科技
        all_technologies = tech_service.get_all_technologies()
        user_tech_ids = {ut.tech_id for ut in tech_service.get_user_technologies(user.user_id)}

        unlocked_techs = []

        # 检查每个科技是否满足解锁条件
        for tech in all_technologies:
            if tech.id in user_tech_ids:
                continue  # 已解锁，跳过

            # 检查等级要求和前置科技
            if (user.level >= tech.required_level and
                    all(req_id in user_tech_ids for req_id in tech.required_tech_ids)):

                # 自动解锁科技
                if tech_service.unlock_technology(user.user_id, tech.id):
                    unlocked_techs.append(tech)

        return unlocked_techs

    async def register_command(self, event: AstrMessageEvent):
        """用户注册命令"""
        user_id = event.get_sender_id()
        platform = event.get_platform_name() or "unknown"
        nickname = event.get_sender_name() or f"用户{user_id[-4:]}"

        # 检查用户是否已存在
        if self.get_user(user_id):
            yield event.plain_result("您已经注册过了！")
            return

        # 创建新用户
        user = self.create_user(user_id, platform, nickname)

        # 为新用户发放新手木竿
        equipment_service = EquipmentService(self.db)
        rod_given = equipment_service.give_rod_to_user(user_id, STARTER_ROD_TEMPLATE_ID)

        # 构建欢迎消息
        if rod_given:
            welcome_message = (f"注册成功！欢迎 {nickname} 来到大gai庄园！\n\n"
                               f"您获得了初始金币: {user.gold}\n\n"
                               "您获得了一把新手木竿，可以开始钓鱼了！")
        else:
            welcome_message = (f"注册成功！欢迎 {nickname} 来到大gai庄园！\n\n"
                               f"您获得了初始金币: {user.gold}\n\n"
                               "（新手木竿发放失败，请联系管理员）")

        yield event.plain_result(welcome_message)

    async def sign_in_command(self, event: AstrMessageEvent):
        """签到命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取当前日期和昨天日期
        today = time.strftime('%Y-%m-%d', time.localtime())
        yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))

        # 检查今日是否已签到
        existing_record = self.db.fetch_one(
            "SELECT * FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, today)
        )

        if existing_record:
            yield event.plain_result("您今天已经签到过了！")
            return

        # 计算连续签到天数
        yesterday_record = self.db.fetch_one(
            "SELECT streak FROM sign_in_logs WHERE user_id = ? AND date = ?",
            (user_id, yesterday)
        )
        streak = yesterday_record['streak'] + 1 if yesterday_record else 1

        # 计算奖励
        reward_gold = SIGN_IN_BASE_GOLD + (streak - 1) * SIGN_IN_STREAK_GOLD_INCREMENT
        reward_exp = SIGN_IN_BASE_EXP + (streak - 1) * SIGN_IN_STREAK_EXP_INCREMENT

        # 更新用户金币
        user.gold += reward_gold

        # 使用handle_user_exp_gain函数处理经验值增加
        exp_result = self.handle_user_exp_gain(user, reward_exp)

        # 提取处理结果
        leveled_up = exp_result['leveled_up']
        new_level = exp_result['new_level']
        level_up_reward = exp_result['level_up_reward']
        unlocked_techs = exp_result['unlocked_techs']
        newly_achievements = exp_result['newly_achievements']

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
        if leveled_up:
            if level_up_reward > 0:
                level_up_message = f"\n🎉 恭喜升级到 {new_level} 级！获得金币奖励: {level_up_reward}"
            else:
                level_up_message = f"\n🎉 恭喜升级到 {new_level} 级！"

            if new_level >= MAX_LEVEL:
                level_up_message += " 您已达到最高等级！"

            # 如果有新解锁的科技，添加到升级信息中
            if unlocked_techs:
                tech_messages = [f"🎉 成功解锁科技: {tech.display_name}！\n{tech.description}"
                                 for tech in unlocked_techs]
                tech_unlock_message = "\n\n".join(tech_messages)
                level_up_message += f"\n\n{tech_unlock_message}"

        # 基础消息
        message = (f"签到成功！\n\n"
                   f"获得金币: {reward_gold}\n"
                   f"获得经验: {reward_exp}点{level_up_message}\n\n"
                   f"连续签到: {streak}天")

        # 添加成就解锁信息
        if newly_unlocked:
            message += "\n\n🎉 恭喜解锁新成就！\n"
            message += "\n".join([f"  · {a.name}: {a.description}" for a in newly_unlocked])

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

        # 计算升级相关数据
        if user.level >= MAX_LEVEL:
            message = (f"📊 等级信息\n\n"
                       f"当前等级: {user.level}\n\n"
                       f"当前经验: {user.exp}\n\n"
                       "恭喜您已达到最高等级！\n\n"
                       "您已解锁所有等级特权！")
        else:
            current_level_required_exp = self._get_exp_for_level(user.level - 1) if user.level > 1 else 0
            next_level_required_exp = self._get_exp_for_level(user.level)
            exp_in_current_level = user.exp - current_level_required_exp
            exp_for_current_level = next_level_required_exp - current_level_required_exp
            exp_needed = next_level_required_exp - user.exp

            # 下一级奖励
            next_reward = self._get_level_up_reward(user.level + 1)

            message = (f"📊 等级信息\n\n"
                       f"当前等级: {user.level}\n\n"
                       f"当前经验: {user.exp}\n\n"
                       f"升级进度: {exp_in_current_level}/{exp_for_current_level}\n\n"
                       f"距离升级还需: {exp_needed} 经验\n\n"
                       f"下一等级奖励: {next_reward} 金币")

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
        user = User(
            user_id=user_id,
            platform=platform,
            nickname=nickname,
            created_at=now,
            updated_at=now
        )

        self.db.execute_query(
            """INSERT INTO users (user_id, platform, nickname, gold, exp, level, fishing_count,
                                  total_fish_weight, total_income, last_fishing_time,
                                  auto_fishing, total_fishing_count, total_coins_earned, fish_pond_capacity,
                                  created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
            """UPDATE users
               SET platform=?,
                   nickname=?,
                   gold=?,
                   exp=?,
                   level=?,
                   fishing_count=?,
                   total_fish_weight=?,
                   total_income=?,
                   last_fishing_time=?,
                   auto_fishing=?,
                   total_fishing_count=?,
                   total_coins_earned=?,
                   fish_pond_capacity=?,
                   updated_at=?
               WHERE user_id = ?""",
            (
                user.platform, user.nickname, user.gold, user.exp, user.level, user.fishing_count,
                user.total_fish_weight, user.total_income, user.last_fishing_time,
                user.auto_fishing, user.total_fishing_count, user.total_coins_earned,
                user.fish_pond_capacity, user.updated_at, user.user_id
            )
        )

    def add_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        if amount <= 0:
            return False

        user = self.get_user(user_id)
        if user:
            user.gold += amount
            self.update_user(user)
            return True
        return False

    def deduct_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        if amount <= 0:
            return False

        user = self.get_user(user_id)
        if user and user.gold >= amount:
            user.gold -= amount
            self.update_user(user)
            return True
        return False

    def handle_user_exp_gain(self, user: User, exp_amount: int) -> dict:
        """
        处理用户获得经验值后的一系列操作，包括升级、奖励和科技解锁

        Args:
            user: 用户对象
            exp_amount: 获得的经验值数量

        Returns:
            dict: 包含处理结果的字典
                - leveled_up: 是否升级
                - old_level: 升级前等级
                - new_level: 升级后等级
                - level_up_reward: 升级奖励金币
                - unlocked_techs: 解锁的科技列表
                - newly_achievements: 新解锁的成就列表
        """
        result = {
            'leveled_up': False,
            'old_level': user.level,
            'new_level': user.level,
            'level_up_reward': 0,
            'unlocked_techs': [],
            'newly_achievements': []
        }

        if exp_amount <= 0:
            return result

        # 增加经验值
        user.exp += exp_amount

        # 检查是否升级
        old_level = user.level
        new_level = self._calculate_level(user.exp)

        if new_level > old_level:
            result['leveled_up'] = True
            result['old_level'] = old_level
            result['new_level'] = new_level

            # 计算升级奖励总和
            level_up_reward = sum(
                self._get_level_up_reward(level)
                for level in range(old_level + 1, new_level + 1)
            )

            result['level_up_reward'] = level_up_reward
            user.gold += level_up_reward
            user.level = new_level

        # 保存用户数据更新
        self.update_user(user)

        # 检查并自动解锁科技
        if result['leveled_up']:
            unlocked_techs = self.check_and_unlock_technologies(user)
            result['unlocked_techs'] = unlocked_techs

        # 检查成就
        newly_unlocked = self.achievement_service.check_achievements(user)
        result['newly_achievements'] = newly_unlocked

        return result
