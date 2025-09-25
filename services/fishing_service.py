from typing import Optional, List, Tuple
import math

from discord.ext.commands import cooldown

from astrbot import logger
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate, FishingResult
from ..models.database import DatabaseManager
from .achievement_service import AchievementService
from ..dao.fishing_dao import FishingDAO
from ..enums.messages import Messages
from ..utils.fishing_utils import (calculate_exp_gain, select_fish_by_rarity,
                                 calculate_fish_value_and_weight, calculate_catch_rate,
                                 calculate_rod_durability_cost)
from ..enums.constants import Constants
import random
import time

FISHING_COOLDOWN = Constants.FISHING_COOLDOWN

class FishingService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_service = AchievementService(db_manager)
        self.fishing_dao = FishingDAO(db_manager)

    def get_fish_templates(self) -> List[FishTemplate]:
        """获取所有鱼类模板"""
        return self.fishing_dao.get_fish_templates()

    def get_rod_templates(self) -> List[RodTemplate]:
        """获取所有鱼竿模板"""
        return self.fishing_dao.get_rod_templates()

    def get_accessory_templates(self) -> List[AccessoryTemplate]:
        """获取所有饰品模板"""
        return self.fishing_dao.get_accessory_templates()

    def get_bait_templates(self) -> List[BaitTemplate]:
        """获取所有鱼饵模板"""
        return self.fishing_dao.get_bait_templates()

    def can_fish(self, user: User) -> Tuple[bool, str]:
        """检查用户是否可以钓鱼"""
        # 检查冷却时间 (默认3分钟)
        current_time = int(time.time())
        cooldown = FISHING_COOLDOWN  # 3分钟冷却时间

        # 获取用户装备的鱼竿，用于计算冷却时间减成
        equipped_rod = self._get_equipped_rod(user.user_id)

        # 如果装备了"冷静之竿"，减少10%冷却时间
        if equipped_rod and equipped_rod.name == "冷静之竿":
            cooldown = int(cooldown * 0.9)  # 减少10%冷却时间

        if current_time - user.last_fishing_time < cooldown:
            remaining = cooldown - (current_time - user.last_fishing_time)
            return False, Messages.COOLDOWN_NOT_EXPIRED.value.format(remaining=remaining)

        # 检查金币 (默认10金币)
        if user.gold < 10:
            return False, Messages.FISHING_GOLD_NOT_ENOUGH.value

        return True, Messages.CAN_FISH.value

    def fish(self, user: User) -> FishingResult:
        """执行钓鱼操作"""
        # 检查是否可以钓鱼
        can_fish, message = self.can_fish(user)
        if not can_fish:
            return FishingResult(success=False, message=message)

        # 获取用户装备的鱼竿
        equipped_rod = self._get_equipped_rod(user.user_id)

        # 检查是否装备了鱼竿
        if not equipped_rod:
            return FishingResult(success=False, message=Messages.NO_ROD_EQUIPPED.value)

        # 获取用户装备的饰品
        equipped_accessory = self._get_equipped_accessory(user.user_id)

        # 计算钓鱼成功率加成
        catch_rate_bonus = 1.0
        if equipped_rod:
            catch_rate_bonus *= equipped_rod.quality_mod
        if equipped_accessory and equipped_accessory.quality_mod:
            catch_rate_bonus *= equipped_accessory.quality_mod

        # 随机决定是否钓到鱼 (基础成功率50%)
        base_catch_rate = 0.5
        final_catch_rate = calculate_catch_rate(base_catch_rate, catch_rate_bonus)

        if random.random() > final_catch_rate:
            # 钓鱼失败
            # 即使失败也扣除费用并更新冷却时间
            user.gold -= 10
            user.fishing_count += 1
            user.last_fishing_time = int(time.time())

            # 更新用户数据到数据库
            from ..dao.user_dao import UserDAO
            user_dao = UserDAO(self.db)
            user_dao.update_user_fields(user.user_id, {
                'gold': user.gold,
                'fishing_count': user.fishing_count,
                'last_fishing_time': user.last_fishing_time
            })

            return FishingResult(success=False, message=Messages.FISHING_FAILURE.value)

        # 钓鱼成功扣除费用并更新冷却时间
        user.gold -= 10
        user.fishing_count += 1
        user.last_fishing_time = int(time.time())

        # 获取用户装备的鱼竿
        equipped_rod_instance = self._get_equipped_rod_instance(user.user_id)

        # 检查鱼竿耐久度
        if equipped_rod_instance and equipped_rod_instance['durability'] is not None:
            if equipped_rod_instance['durability'] <= 0:
                return FishingResult(success=False, message=Messages.EQUIPMENT_ROD_BROKEN.value)

        # 钓鱼成功，随机选择一种鱼
        # 限制鱼竿只能钓到稀有度小于等于鱼竿稀有度的鱼
        all_fish_templates = self.get_fish_templates()
        if not all_fish_templates:
            return FishingResult(success=False, message=Messages.NO_FISH_TEMPLATES.value)

        # 根据鱼竿稀有度过滤可钓鱼类
        fish_templates = [fish for fish in all_fish_templates if fish.rarity <= equipped_rod.rarity]
        if not fish_templates:
            return FishingResult(success=False, message=Messages.FISHING_FAILED_NO_FISH.value)

        # 根据稀有度权重选择鱼类
        caught_fish = select_fish_by_rarity(fish_templates)

        # 计算鱼的重量和价值
        final_weight, final_value = calculate_fish_value_and_weight(caught_fish)

        # 消耗鱼竿耐久度（每次钓鱼消耗1-5点耐久度）
        if equipped_rod_instance:
            # 如果鱼竿有耐久度限制（不为None）且当前耐久度大于0
            if equipped_rod_instance['durability'] is not None and equipped_rod_instance['durability'] > 0:
                durability_cost = calculate_rod_durability_cost()
                new_durability = max(0, equipped_rod_instance['durability'] - durability_cost)

                # 更新鱼竿耐久度
                self.fishing_dao.update_rod_durability(equipped_rod_instance['id'], new_durability)

                # 如果鱼竿损坏，添加提示信息
                if new_durability <= 0:
                    message = f"{Messages.EQUIPMENT_ROD_BROKEN.value}\n\n"
                else:
                    message = ""
            # 如果鱼竿没有耐久度限制（为None），则不消耗耐久度
            elif equipped_rod_instance['durability'] is None:
                message = ""

        # 添加到用户鱼类库存
        self.fishing_dao.add_fish_to_inventory(user.user_id, caught_fish.id, final_weight, final_value)

        # 更新用户统计数据（不再直接增加金币）
        user.total_fish_weight += final_weight
        user.total_income += final_value

        # 增加经验（根据鱼的稀有度和价值）
        exp_gained = self._calculate_exp_gain(caught_fish, final_weight, final_value, user.level)

        # 获取用户装备的鱼竿，用于计算经验加成
        equipped_rod = self._get_equipped_rod(user.user_id)

        # 如果装备了"长者之竿"，增加5%经验
        if equipped_rod and equipped_rod.name == "长者之竿":
            exp_gained = int(exp_gained * 1.05)  # 增加5%经验

        # 使用UserService的handle_user_exp_gain函数处理经验值增加
        from ..services.user_service import UserService
        user_service = UserService(self.db)
        exp_result = user_service.handle_user_exp_gain(user, exp_gained)

        # 提取处理结果
        leveled_up = exp_result['leveled_up']
        old_level = exp_result['old_level']
        new_level = exp_result['new_level']
        level_up_reward = exp_result['level_up_reward']
        unlocked_techs = exp_result['unlocked_techs']
        newly_achievements = exp_result['newly_achievements']

        # 如果升级了，添加升级信息
        level_up_message = ""
        if leveled_up:
            if level_up_reward > 0:
                level_up_message = (f"\n{Messages.LEVEL_UP_CONGRATS.value.format(new_level=new_level)} \n\n"
                                    f"{Messages.LEVEL_UP_REWARD.value}: {level_up_reward}")
            else:
                if new_level >= 100:
                    level_up_message = f"\n{Messages.LEVEL_UP_CONGRATS_MAX.value.format(new_level=new_level)}"
                else:
                    level_up_message = f"\n{Messages.LEVEL_UP_CONGRATS.value.format(new_level=new_level)}"

            # 如果有新解锁的科技，添加到升级信息中
            if unlocked_techs:
                tech_messages = []
                for tech in unlocked_techs:
                    tech_messages.append(f"{Messages.TECH_UNLOCK.value}: {tech.display_name}！\n{tech.description}")
                tech_unlock_message = "\n\n".join(tech_messages)
                level_up_message += f"\n\n{tech_unlock_message}"

        # 记录钓鱼日志
        self.fishing_dao.add_fishing_log(user.user_id, caught_fish.id, final_weight, final_value, True)

        # 更新用户数据到数据库
        from ..dao.user_dao import UserDAO
        user_dao = UserDAO(self.db)
        user_dao.update_user_fields(user.user_id, {
            'gold': user.gold,
            'fishing_count': user.fishing_count,
            'last_fishing_time': user.last_fishing_time,
            'total_fish_weight': user.total_fish_weight,
            'total_income': user.total_income,
            'exp': user.exp,
            'level': user.level
        })

        # 检查成就
        newly_unlocked = self.achievement_service.check_achievements(user)

        # 构造返回消息，包含成就解锁信息
        # 如果鱼竿已损坏，在消息前添加损坏信息
        if 'message' not in locals():
            message = ""

        message += (f"{Messages.FISHING_CAUGHT_FISH.value.format(caught_fish_name=caught_fish.name, caught_fish_desc=caught_fish.description)}\n\n"
                    f"重量: {final_weight:.2f}kg\n\n"
                    f"价值: {final_value}金币\n\n"
                    f"获得经验: {exp_gained}点{level_up_message}")

        # 如果有新解锁的成就，添加到消息中
        if newly_unlocked:
            message += "\n\n🎉 恭喜解锁新成就！\n"
            for achievement in newly_unlocked:
                message += f"  · {achievement.name}: {achievement.description}\n"

        return FishingResult(success=True, fish=caught_fish, weight=final_weight, value=final_value, message=message)

    def _calculate_exp_gain(self, fish: FishTemplate, weight: float, value: int, user_level: int = 1) -> int:
        """计算钓鱼获得的经验值"""
        return calculate_exp_gain(fish, weight, value, user_level)

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
        return self.fishing_dao.get_equipped_rod(user_id)

    def _get_equipped_rod_instance(self, user_id: str) -> Optional[dict]:
        """获取用户装备的鱼竿实例（包含耐久度等实例信息）"""
        return self.fishing_dao.get_equipped_rod_instance(user_id)

    def _get_equipped_accessory(self, user_id: str) -> Optional[AccessoryTemplate]:
        """获取用户装备的饰品"""
        return self.fishing_dao.get_equipped_accessory(user_id)

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
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 执行钓鱼操作
        result = self.fish(user)

        # 返回结果
        yield event.plain_result(result.message)
