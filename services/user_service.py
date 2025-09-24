from typing import Optional, List, Any, Generator
import time

from astrbot.core.message.message_event_result import MessageEventResult
from ..models.user import User
from ..models.database import DatabaseManager
from astrbot.api.event import AstrMessageEvent
from .achievement_service import AchievementService
from .technology_service import TechnologyService
from ..services.equipment_service import EquipmentService
from ..dao.user_dao import UserDAO
from ..enums.messages import Messages
from ..enums.constants import Constants
from ..utils.exp_utils import (
    calculate_level, get_exp_for_level, precompute_level_rewards,
    get_level_up_reward, check_and_unlock_technologies
)
from ..utils.sign_in_utils import get_current_date, get_yesterday_date, calculate_sign_in_rewards


class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.achievement_service = AchievementService(db_manager)
        self.user_dao = UserDAO(db_manager)
        self.tech_service = TechnologyService(db_manager)

        # 缓存数据，避免重复计算/查询
        self._level_rewards = precompute_level_rewards()
        self._all_technologies = self.tech_service.get_all_technologies()

    def _require_user(self, user_id: str, event: AstrMessageEvent) -> Generator[MessageEventResult, Any, User | None]:
        """校验用户是否存在，不存在直接返回提示"""
        user = self.get_user(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return None
        return user

    def _precompute_level_rewards(self) -> List[int]:
        """预计算各级别升级奖励"""
        return precompute_level_rewards()

    def _calculate_level(self, exp: int) -> int:
        """根据经验计算等级"""
        return calculate_level(exp)

    def _get_exp_for_level(self, level: int) -> int:
        """获取升级到指定等级所需的总经验"""
        return get_exp_for_level(level)

    def _get_level_up_reward(self, level: int) -> int:
        """根据等级获取升级奖励金币"""
        return get_level_up_reward(level, self._level_rewards)

    def check_and_unlock_technologies(self, user: User) -> List:
        """检查并自动解锁符合条件的科技"""
        user_tech_ids = {ut.tech_id for ut in self.tech_service.get_user_technologies(user.user_id)}
        unlocked = check_and_unlock_technologies(user, self._all_technologies, user_tech_ids)
        return [t for t in unlocked if self.tech_service.unlock_technology(user.user_id, t.id)]

    async def register_command(self, event: AstrMessageEvent):
        """用户注册命令"""
        user_id = event.get_sender_id()
        platform = event.get_platform_name() or "unknown"
        group_id = event.get_group_id() or ""
        nickname = event.get_sender_name() or f"用户{user_id[-4:]}"

        # 检查用户是否已存在
        if self.get_user(user_id):
            yield event.plain_result(Messages.ALREADY_REGISTERED.value)
            return

        # 创建新用户
        user = self.create_user(user_id, platform, group_id, nickname)

        # 为新用户发放新手木竿
        equipment_service = EquipmentService(self.db)
        rod_given = equipment_service.give_rod_to_user(user_id, Constants.STARTER_ROD_TEMPLATE_ID)

        # 构建欢迎消息
        if rod_given:
            welcome_message = (f"{Messages.REGISTRATION_SUCCESS.value}\n\n"
                               f"{Messages.BALANCE_INFO.value}: {user.gold}\n\n"
                               "您获得了一把新手木竿，可以开始钓鱼了！")
        else:
            welcome_message = (f"{Messages.REGISTRATION_SUCCESS.value}\n\n"
                               f"{Messages.BALANCE_INFO.value}: {user.gold}\n\n"
                               "（新手木竿发放失败，请联系管理员）")

        yield event.plain_result(welcome_message)

    async def sign_in_command(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        user = self.get_user(user_id)
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        today, yesterday = get_current_date(), get_yesterday_date()
        if self.user_dao.check_sign_in(user_id, today):
            yield event.plain_result(Messages.ALREADY_SIGNED_IN.value)
            return

        # 计算奖励
        yesterday_record = self.user_dao.yesterday_record(user_id, yesterday)
        streak = (yesterday_record['streak'] + 1) if yesterday_record else 1
        reward_gold, reward_exp = calculate_sign_in_rewards(streak)
        user.gold += reward_gold

        exp_result = self.handle_user_exp_gain(user, reward_exp)
        self.user_dao.record_sign_in(user_id, today, streak, reward_gold)

        message = self._build_sign_in_message(reward_gold, reward_exp, streak, exp_result)
        yield event.plain_result(message)

    def _build_sign_in_message(self, gold: int, exp: int, streak: int, exp_result: dict) -> str:
        parts = [
            "签到成功！",
            f"获得金币: {gold}",
            f"获得经验: {exp}点",
            f"连续签到: {streak}天"
        ]
        level_up_msg = self.handle_user_level_up(exp_result)
        if level_up_msg:
            parts.append(level_up_msg)
        return "\n\n".join(parts)

    async def gold_command(self, event: AstrMessageEvent):
        """查看金币命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        yield event.plain_result(f"{Messages.BALANCE_INFO.value}: {user.gold}")

    async def level_command(self, event: AstrMessageEvent):
        """查看等级和经验命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 计算升级相关数据
        if user.level >= Constants.MAX_LEVEL:
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
        return self.user_dao.get_user_by_id(user_id)

    def create_user(self, user_id: str, platform: str, group_id: str, nickname: str) -> User:
        """创建新用户"""
        now = int(time.time())
        user = User(
            user_id=user_id,
            platform=platform,
            group_id=group_id,
            nickname=nickname,
            created_at=now,
            updated_at=now
        )

        self.user_dao.create_user(user)
        return user

    def update_user(self, user: User) -> None:
        """更新用户信息"""
        self.user_dao.update_user(user)

    def add_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        if amount <= 0:
            return False

        return self.user_dao.add_gold(user_id, amount)

    def deduct_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        if amount <= 0:
            return False

        return self.user_dao.deduct_gold(user_id, amount)

    def handle_user_exp_gain(self, user: User, exp_amount: int) -> dict:
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

        user.exp += exp_amount
        old_level = user.level
        new_level = self._calculate_level(user.exp)

        if new_level > old_level:
            self._process_level_up(user, old_level, new_level, result)

        self.update_user(user)
        result['newly_achievements'] = self.achievement_service.check_achievements(user)
        return result

    def _process_level_up(self, user: User, old_level: int, new_level: int, result: dict):
        result.update({
            'leveled_up': True,
            'old_level': old_level,
            'new_level': new_level,
            'level_up_reward': sum(self._get_level_up_reward(l) for l in range(old_level + 1, new_level + 1))
        })
        user.gold += result['level_up_reward']
        user.level = new_level
        result['unlocked_techs'] = self.check_and_unlock_technologies(user)

    def handle_user_level_up(self, exp_result: dict) -> str:
        parts = []
        if exp_result['leveled_up']:
            parts.append(self._format_level_up_message(exp_result))
        if exp_result['newly_achievements']:
            ach_msg = "\n".join(f"  · {a.name}: {a.description}" for a in exp_result['newly_achievements'])
            parts.append(f"🎉 恭喜解锁新成就！\n{ach_msg}")
        return "\n\n".join(parts)

    def _format_level_up_message(self, exp_result: dict) -> str:
        parts = [f"🎉 恭喜升级到 {exp_result['new_level']} 级！"]
        if exp_result['level_up_reward']:
            parts.append(f"获得金币奖励: {exp_result['level_up_reward']}")
        if exp_result['new_level'] >= Constants.MAX_LEVEL:
            parts.append("您已达到最高等级！")
        if exp_result['unlocked_techs']:
            tech_msgs = [f"🎉 成功解锁科技: {t.display_name}！\n{t.description}" for t in exp_result['unlocked_techs']]
            parts.append("\n\n".join(tech_msgs))
        return "\n".join(parts)