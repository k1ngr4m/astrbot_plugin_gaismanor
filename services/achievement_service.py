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
import time


class AchievementService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
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
        unique_fish_count = self.db.fetch_one(
            "SELECT COUNT(DISTINCT fish_template_id) as count FROM fishing_logs WHERE user_id = ? AND success = TRUE",
            (user_id,)
        )['count'] if self.db.fetch_one(
            "SELECT COUNT(DISTINCT fish_template_id) as count FROM fishing_logs WHERE user_id = ? AND success = TRUE",
            (user_id,)
        ) else 0

        # 获取用户钓到的垃圾数量
        garbage_count = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM fishing_logs WHERE user_id = ? AND fish_template_id = 0 AND success = TRUE",
            (user_id,)
        )['count'] if self.db.fetch_one(
            "SELECT COUNT(*) as count FROM fishing_logs WHERE user_id = ? AND fish_template_id = 0 AND success = TRUE",
            (user_id,)
        ) else 0

        # 获取用户获得的最大擦弹倍率 (假设在fishing_logs中存储)
        max_wipe_result = self.db.fetch_one(
            "SELECT MAX(wipe_multiplier) as max_multiplier FROM fishing_logs WHERE user_id = ? AND wipe_multiplier > 1",
            (user_id,)
        )
        max_wipe_bomb_multiplier = max_wipe_result['max_multiplier'] if max_wipe_result and max_wipe_result['max_multiplier'] else 0.0

        # 获取用户拥有的鱼竿稀有度
        rod_rarities_result = self.db.fetch_all(
            "SELECT DISTINCT rt.rarity FROM user_rod_instances uri JOIN rod_templates rt ON uri.rod_template_id = rt.id WHERE uri.user_id = ?",
            (user_id,)
        )
        owned_rod_rarities = {r['rarity'] for r in rod_rarities_result} if rod_rarities_result else set()

        # 获取用户拥有的饰品稀有度
        accessory_rarities_result = self.db.fetch_all(
            "SELECT DISTINCT at.rarity FROM user_accessory_instances uai JOIN accessory_templates at ON uai.accessory_template_id = at.id WHERE uai.user_id = ?",
            (user_id,)
        )
        owned_accessory_rarities = {r['rarity'] for r in accessory_rarities_result} if accessory_rarities_result else set()

        # 检查用户是否钓到过重鱼 (超过100kg)
        heavy_fish_result = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM fishing_logs WHERE user_id = ? AND fish_weight >= 100 AND success = TRUE",
            (user_id,)
        )
        has_heavy_fish = heavy_fish_result and heavy_fish_result['count'] > 0

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
                now = int(time.time())
                if existing_record:
                    # 更新现有记录
                    self.db.execute_query(
                        "UPDATE user_achievements SET completed = TRUE, completed_at = ?, progress = ? WHERE user_id = ? AND achievement_id = ?",
                        (now, achievement.get_progress(context), user.user_id, achievement.id)
                    )
                else:
                    # 创建新记录
                    self.db.execute_query(
                        "INSERT INTO user_achievements (user_id, achievement_id, progress, completed, completed_at) VALUES (?, ?, ?, TRUE, ?)",
                        (user.user_id, achievement.id, achievement.get_progress(context), now)
                    )

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
            now = int(time.time())
            # 检查是否已经有这个称号
            existing_title = self.db.fetch_one(
                "SELECT id FROM user_titles WHERE user_id = ? AND title_id = ?",
                (user.user_id, title_id)
            )

            if not existing_title:
                self.db.execute_query(
                    "INSERT INTO user_titles (user_id, title_id, acquired_at) VALUES (?, ?, ?)",
                    (user.user_id, title_id, now)
                )
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
        user_records = self.db.fetch_all(
            """SELECT ua.achievement_id, ua.progress, ua.completed, ua.completed_at, a.name, a.description
               FROM user_achievements ua
               JOIN achievements a ON ua.achievement_id = a.id
               WHERE ua.user_id = ?""",
            (user_id,)
        )

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
        titles = self.db.fetch_all(
            """SELECT ut.title_id, ut.acquired_at, ut.is_active, t.name, t.description
               FROM user_titles ut
               JOIN titles t ON ut.title_id = t.id
               WHERE ut.user_id = ?""",
            (user_id,)
        )
        return titles or []

    def activate_title(self, user_id: str, title_id: int) -> bool:
        """激活用户称号"""
        # 先检查用户是否拥有该称号
        title_exists = self.db.fetch_one(
            "SELECT id FROM user_titles WHERE user_id = ? AND title_id = ?",
            (user_id, title_id)
        )

        if not title_exists:
            return False

        # 取消其他称号的激活状态
        self.db.execute_query(
            "UPDATE user_titles SET is_active = FALSE WHERE user_id = ?",
            (user_id,)
        )

        # 激活指定称号
        self.db.execute_query(
            "UPDATE user_titles SET is_active = TRUE WHERE user_id = ? AND title_id = ?",
            (user_id, title_id)
        )

        return True