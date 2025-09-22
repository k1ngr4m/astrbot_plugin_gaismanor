from typing import Optional, List, Tuple
import math

from astrbot import logger
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate, FishingResult
from ..models.database import DatabaseManager
from .achievement_service import AchievementService
import random
import time

class FishingService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_service = AchievementService(db_manager)

    def get_fish_templates(self) -> List[FishTemplate]:
        """获取所有鱼类模板"""
        results = self.db.fetch_all("SELECT * FROM fish_templates")
        return [
            FishTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                base_value=row['base_value'],
                min_weight=row['min_weight'],
                max_weight=row['max_weight'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_rod_templates(self) -> List[RodTemplate]:
        """获取所有鱼竿模板"""
        results = self.db.fetch_all("SELECT * FROM rod_templates")
        return [
            RodTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                source=row['source'],
                purchase_cost=row['purchase_cost'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                durability=row['durability'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_accessory_templates(self) -> List[AccessoryTemplate]:
        """获取所有饰品模板"""
        results = self.db.fetch_all("SELECT * FROM accessory_templates")
        return [
            AccessoryTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                slot_type=row['slot_type'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_bait_templates(self) -> List[BaitTemplate]:
        """获取所有鱼饵模板"""
        results = self.db.fetch_all("SELECT * FROM bait_templates")
        return [
            BaitTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                cost=row['cost'],
                required_rod_rarity=row['required_rod_rarity'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=row['is_consumable']
            ) for row in results
        ]

    def can_fish(self, user: User) -> Tuple[bool, str]:
        """检查用户是否可以钓鱼"""
        # 检查冷却时间 (默认3分钟)
        current_time = int(time.time())
        cooldown = 10  # 3分钟冷却时间
        if current_time - user.last_fishing_time < cooldown:
            remaining = cooldown - (current_time - user.last_fishing_time)
            return False, f"还在冷却中，请等待 {remaining} 秒后再钓鱼"

        # 检查金币 (默认10金币)
        if user.gold < 10:
            return False, "金币不足，无法钓鱼"

        return True, "可以钓鱼"

    def fish(self, user: User) -> FishingResult:
        """执行钓鱼操作"""
        # 检查是否可以钓鱼
        can_fish, message = self.can_fish(user)
        if not can_fish:
            return FishingResult(success=False, message=message)

        # 获取用户装备的鱼竿和饰品
        equipped_rod = self._get_equipped_rod(user.user_id)
        equipped_accessory = self._get_equipped_accessory(user.user_id)

        # 计算钓鱼成功率加成
        catch_rate_bonus = 1.0
        if equipped_rod:
            catch_rate_bonus *= equipped_rod.quality_mod
        if equipped_accessory and equipped_accessory.quality_mod:
            catch_rate_bonus *= equipped_accessory.quality_mod

        # 随机决定是否钓到鱼 (基础成功率50%)
        base_catch_rate = 0.5
        final_catch_rate = min(base_catch_rate * catch_rate_bonus, 0.95)  # 最高95%成功率

        if random.random() > final_catch_rate:
            # 钓鱼失败
            # 即使失败也扣除费用并更新冷却时间
            user.gold -= 10
            user.fishing_count += 1
            user.last_fishing_time = int(time.time())

            # 更新用户数据到数据库
            self.db.execute_query(
                """UPDATE users SET
                    gold=?, fishing_count=?, last_fishing_time=?
                    WHERE user_id=?""",
                (user.gold, user.fishing_count, user.last_fishing_time, user.user_id)
            )

            return FishingResult(success=False, message="这次没有钓到鱼，再试试看吧！")

        # 钓鱼成功才扣除费用并更新冷却时间
        user.gold -= 10
        user.fishing_count += 1
        user.last_fishing_time = int(time.time())

        # 钓鱼成功，随机选择一种鱼
        fish_templates = self.get_fish_templates()
        if not fish_templates:
            return FishingResult(success=False, message="暂无鱼类数据")

        # 根据稀有度权重选择鱼类
        # 稀有度越高，权重越低（越难钓到）
        weights = [1.0 / (fish.rarity ** 2) for fish in fish_templates]
        caught_fish = random.choices(fish_templates, weights=weights)[0]

        # 计算鱼的重量和价值
        final_weight = random.uniform(caught_fish.min_weight / 1000.0, caught_fish.max_weight / 1000.0)
        final_value = int(caught_fish.base_value * (final_weight * 2))

        # 添加到用户鱼类库存
        self.db.execute_query(
            """INSERT INTO user_fish_inventory
               (user_id, fish_template_id, weight, value, caught_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user.user_id, caught_fish.id, final_weight, final_value, int(time.time()))
        )

        # 更新用户统计数据（不再直接增加金币）
        user.total_fish_weight += final_weight
        user.total_income += final_value

        # 增加经验（根据鱼的稀有度和价值）
        exp_gained = self._calculate_exp_gain(caught_fish, final_weight, final_value, user.level)
        user.exp += exp_gained

        # 检查是否升级
        old_level = user.level
        new_level = self._calculate_level(user.exp)

        # 如果升级了，给予金币奖励
        level_up_reward = 0
        if new_level > old_level:
            # 从用户服务导入奖励计算函数
            from ..services.user_service import UserService
            user_service = UserService(self.db)
            for level in range(old_level + 1, new_level + 1):
                level_up_reward += user_service._get_level_up_reward(level)
            user.gold += level_up_reward

        user.level = new_level

        # 如果升级了，添加升级信息
        level_up_message = ""
        if user.level > old_level:
            if level_up_reward > 0:
                level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！获得金币奖励: {level_up_reward}"
            else:
                if user.level >= 100:
                    level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！您已达到最高等级！"
                else:
                    level_up_message = f"\n🎉 恭喜升级到 {user.level} 级！"

        # 记录钓鱼日志
        self.db.execute_query(
            """INSERT INTO fishing_logs
               (user_id, fish_template_id, fish_weight, fish_value, success, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user.user_id, caught_fish.id, final_weight, final_value, True, int(time.time()))
        )

        # 更新用户数据到数据库
        self.db.execute_query(
            """UPDATE users SET
                gold=?, fishing_count=?, last_fishing_time=?, total_fish_weight=?, total_income=?, exp=?, level=?
                WHERE user_id=?""",
            (user.gold, user.fishing_count, user.last_fishing_time,
             user.total_fish_weight, user.total_income, user.exp, user.level, user.user_id)
        )

        # 检查成就
        newly_unlocked = self.achievement_service.check_achievements(user)

        # 构造返回消息，包含成就解锁信息
        message = f"恭喜！你钓到了一条 {caught_fish.name} ({caught_fish.description})\n\n重量: {final_weight:.2f}kg\n\n价值: {final_value}金币\n\n获得经验: {exp_gained}点{level_up_message}"

        # 如果有新解锁的成就，添加到消息中
        if newly_unlocked:
            message += "\n\n🎉 恭喜解锁新成就！\n"
            for achievement in newly_unlocked:
                message += f"  · {achievement.name}: {achievement.description}\n"

        return FishingResult(success=True, fish=caught_fish, weight=final_weight, value=final_value, message=message)

    def _calculate_exp_gain(self, fish: FishTemplate, weight: float, value: int, user_level: int = 1) -> int:
        """计算钓鱼获得的经验值"""
        # 基础经验 = 鱼的稀有度 * 10 + 价值 / 10 + 重量 / 10
        base_exp = fish.rarity * 10 + value // 10 + int(weight * 10)

        # 等级加成：每级增加1%经验
        level_bonus = 1 + (user_level - 1) * 0.01

        # 计算最终经验
        final_exp = int(base_exp * level_bonus)

        # 最小经验值为1
        return max(1, final_exp)

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

    def _get_equipped_rod(self, user_id: str) -> Optional[RodTemplate]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.* FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return RodTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                source=result['source'],
                purchase_cost=result['purchase_cost'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                durability=result['durability'],
                icon_url=result['icon_url']
            )
        return None

    def _get_equipped_accessory(self, user_id: str) -> Optional[AccessoryTemplate]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return AccessoryTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                slot_type=result['slot_type'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                coin_mod=result['coin_mod'],
                other_desc=result['other_desc'],
                icon_url=result['icon_url']
            )
        return None

    async def fish_command(self, event):
        """处理钓鱼命令"""
        # 获取用户信息
        user_id = event.get_sender_id()
        username = event.get_sender_name()

        # 从数据库获取用户（需要先注册）
        from ..services.user_service import UserService
        user_service = UserService(self.db)
        user = user_service.get_user(user_id)

        # 如果用户不存在，提示需要先注册
        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 执行钓鱼操作
        result = self.fish(user)

        # 返回结果
        yield event.plain_result(result.message)
