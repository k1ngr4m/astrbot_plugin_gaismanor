from typing import List, Set
from ..achievements.base import BaseAchievement, UserContext
from ..achievements.fishing_achievements import (
    FirstFishCaught, TotalFishCount100, TotalFishCount1000, TenThousandFishCaught,
    TotalWeight10000kg, HeavyFishCaught
)
from ..achievements.collection_achievements import (
    UniqueFishSpecies10, UniqueFishSpecies25, UniqueFishSpecies50,
    GarbageCollector50, RareRodCollected, LegendaryAccessoryCollected
)
from ..achievements.economic_achievements import (
    TotalCoinsEarned1M, WipeBomb10xMultiplier
)
from ..models.database import DatabaseManager
from ..models.user import User
from ..dao.achievement_dao import AchievementDAO
import time


class AchievementService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_dao = AchievementDAO(db_manager)
        # 初始化所有成就
        self.achievements = [
            # 钓鱼成就
            FirstFishCaught(),
            TotalFishCount100(),
            TotalFishCount1000(),
            TenThousandFishCaught(),
            TotalWeight10000kg(),
            HeavyFishCaught(),

            # 收集成就
            UniqueFishSpecies10(),
            UniqueFishSpecies25(),
            UniqueFishSpecies50(),
            GarbageCollector50(),
            RareRodCollected(),
            LegendaryAccessoryCollected(),

            # 经济成就
            TotalCoinsEarned1M(),
            WipeBomb10xMultiplier(),
        ]

    def _get_user_context(self, user: User) -> UserContext:
        """为用户构建成就检查上下文"""
        user_id = user.user_id

        # 获取用户收集的不同鱼种数量
        unique_fish_count = self.achievement_dao.get_unique_fish_count(user_id)

        # 获取用户钓到的垃圾数量
        garbage_count = self.achievement_dao.get_garbage_count(user_id)

        # 获取用户获得的最大擦弹倍率
        max_wipe_bomb_multiplier = self.achievement_dao.get_max_wipe_multiplier(user_id)

        # 获取用户拥有的鱼竿稀有度
        owned_rod_rarities = self.achievement_dao.get_owned_rod_rarities(user_id)

        # 获取用户拥有的饰品稀有度
        owned_accessory_rarities = self.achievement_dao.get_owned_accessory_rarities(user_id)

        # 检查用户是否钓到过重鱼 (超过100kg)
        has_heavy_fish = self.achievement_dao.has_heavy_fish(user_id)

        return UserContext(
            user=user,
            unique_fish_count=unique_fish_count,
            garbage_count=garbage_count,
            max_wipe_bomb_multiplier=max_wipe_bomb_multiplier,
            owned_rod_rarities=owned_rod_rarities,
            owned_accessory_rarities=owned_accessory_rarities,
            has_heavy_fish=has_heavy_fish
        )

    def check_achievements(self, user: User) -> List[BaseAchievement]:
        """检查用户解锁了哪些成就，返回新解锁的成就列表"""
        context = self._get_user_context(user)
        newly_unlocked = []

        for achievement in self.achievements:
            # 检查用户是否已经解锁了这个成就
            existing_record = self.db.fetch_one(
                "SELECT completed FROM user_achievements WHERE user_id = ? AND achievement_id = ?",
                (user.user_id, achievement.id)
            )

            # 如果成就已经完成，跳过检查
            if existing_record and existing_record['completed']:
                continue

            # 检查成就条件
            if achievement.check(context):
                # 记录成就完成
                progress = achievement.get_progress(context)
                if self.achievement_dao.update_achievement_progress(user.user_id, achievement.id, progress, True):
                    newly_unlocked.append(achievement)

                    # 发放奖励
                    self._grant_reward(user, achievement.reward)

        return newly_unlocked

    def _grant_reward(self, user: User, reward: tuple):
        """发放成就奖励"""
        reward_type, reward_value, quantity = reward

        if reward_type == "coins":
            # 增加金币
            self.db.execute_query(
                "UPDATE users SET gold = gold + ? WHERE user_id = ?",
                (reward_value * quantity, user.user_id)
            )
        elif reward_type == "title":
            # 授予称号
            title_id = reward_value
            self.achievement_dao.grant_title_to_user(user.user_id, title_id)
        elif reward_type == "bait":
            # 增加鱼饵
            bait_id = reward_value
            # 检查是否已有该鱼饵
            existing_bait = self.db.fetch_one(
                "SELECT id, quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                (user.user_id, bait_id)
            )

            if existing_bait:
                self.db.execute_query(
                    "UPDATE user_bait_inventory SET quantity = quantity + ? WHERE id = ?",
                    (quantity, existing_bait['id'])
                )
            else:
                self.db.execute_query(
                    "INSERT INTO user_bait_inventory (user_id, bait_template_id, quantity) VALUES (?, ?, ?)",
                    (user.user_id, bait_id, quantity)
                )
        elif reward_type == "premium_currency":
            # 增加高级货币（如果系统支持）
            # 这里假设用户表中有premium_currency字段
            self.db.execute_query(
                "UPDATE users SET premium_currency = premium_currency + ? WHERE user_id = ?",
                (reward_value * quantity, user.user_id)
            )

    def get_user_achievements(self, user_id: str) -> List[dict]:
        """获取用户的成就进度"""
        # 获取所有成就
        all_achievements = {ach.id: ach for ach in self.achievements}

        # 获取用户成就记录
        user_records = self.achievement_dao.get_user_achievements_progress(user_id)

        # 整合成就信息
        result = []
        for record in user_records:
            achievement_id = record['achievement_id']
            if achievement_id in all_achievements:
                achievement = all_achievements[achievement_id]
                result.append({
                    'id': achievement_id,
                    'name': record['name'] or achievement.name,
                    'description': record['description'] or achievement.description,
                    'progress': record['progress'],
                    'target_value': achievement.target_value,
                    'completed': record['completed'],
                    'completed_at': record['completed_at'],
                    'reward': achievement.reward
                })

        # 添加未开始的成就
        user_achievement_ids = {record['achievement_id'] for record in user_records}
        for achievement in self.achievements:
            if achievement.id not in user_achievement_ids:
                result.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'progress': 0,
                    'target_value': achievement.target_value,
                    'completed': False,
                    'completed_at': None,
                    'reward': achievement.reward
                })

        return result

    def get_user_titles(self, user_id: str) -> List[dict]:
        """获取用户拥有的称号"""
        return self.achievement_dao.get_user_titles(user_id)

    def activate_title(self, user_id: str, title_id: int) -> bool:
        """激活用户称号"""
        return self.achievement_dao.activate_user_title(user_id, title_id)