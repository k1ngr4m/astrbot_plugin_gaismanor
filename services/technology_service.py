from typing import List, Optional, Tuple, Dict, Any, AsyncGenerator
import json
import time
from functools import lru_cache

from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.message_event_result import MessageEventResult
from ..dao.fishing_dao import FishingDAO
from ..dao.other_dao import OtherDAO
from ..dao.technology_dao import TechnologyDAO
from ..dao.user_dao import UserDAO
from ..models.user import User
from ..models.tech import Technology, UserTechnology
from ..models.database import DatabaseManager
from ..enums.messages import Messages


class TechnologyService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.tech_dao = TechnologyDAO(self.db)
        self.user_dao = UserDAO(self.db)
        self.fish_dao = FishingDAO(self.db)
        self.other_dao = OtherDAO(self.db)
        self._tech_cache: Dict[int, Technology] = {}  # 缓存科技数据，减少数据库查询

    def _load_tech_to_cache(self) -> None:
        """加载所有科技到缓存"""
        if not self._tech_cache:
            technologies = self.get_all_technologies()
            self._tech_cache = {tech.id: tech for tech in technologies}

    def get_all_technologies(self) -> List[Technology]:
        """获取所有科技"""
        return self.tech_dao.get_all_technologies()

    def get_user_technologies(self, user_id: str) -> List[UserTechnology]:
        """获取用户已解锁的科技"""
        return self.tech_dao.get_user_technologies(user_id)

    def get_technology_by_id(self, tech_id: int) -> Optional[Technology]:
        """根据ID获取科技"""
        return self.tech_dao.get_technology_by_id(tech_id)

    def get_technology_by_name(self, name: str) -> Optional[Technology]:
        """根据名称获取科技"""
        return self.tech_dao.get_technology_by_name(name)

    def is_technology_unlocked(self, user_id: str, tech_id: int) -> bool:
        """检查用户是否已解锁指定科技"""
        return self.tech_dao.is_technology_unlocked(user_id, tech_id)

    def get_user_unlocked_tech_ids(self, user_id: str) -> set[int]:
        """获取用户已解锁科技的ID集合"""
        return self.tech_dao.get_user_unlocked_tech_ids(user_id)

    def is_auto_fishing_unlocked(self, user_id: str, tech_name) -> bool:
        """检查用户是否已解锁指定科技名称的功能"""
        return self.tech_dao.is_tech_unlocked(user_id, tech_name)

    def can_unlock_technology(self, user: User, technology: Technology) -> Tuple[bool, str]:
        """检查用户是否可以解锁指定科技"""
        # 检查是否已解锁
        if self.is_technology_unlocked(user.user_id, technology.id):
            return False, Messages.TECHNOLOGY_ALREADY_UNLOCKED.value

        # 检查等级要求
        if user.level < technology.required_level:
            return False, Messages.TECHNOLOGY_UNLOCK_FAILED_REQUIRED_LEVEL.value.format(required_level=technology.required_level)

        # 检查金币要求
        if user.gold < technology.required_gold:
            return False, Messages.TECHNOLOGY_UNLOCK_FAILED_GOLD_NOT_ENOUGH.value.format(required_gold=technology.required_gold)

        # 检查前置科技要求
        user_tech_ids = self.get_user_unlocked_tech_ids(user.user_id)
        missing_techs = []

        for req_tech_id in technology.required_tech_ids:
            if req_tech_id not in user_tech_ids:
                req_tech = self.get_technology_by_id(req_tech_id)
                if req_tech:
                    missing_techs.append(req_tech.display_name)

        if missing_techs:
            return False, f"{Messages.TECHNOLOGY_UNLOCK_FAILED_REQUIRED_TECH.value}: {', '.join(missing_techs)}"

        return True, Messages.TECHNOLOGY_ALREADY_UNLOCKED.value

    def unlock_technology(self, user_id: str, tech_id: int, skip_checks: bool = False) -> Tuple[bool, str]:
        """
        解锁科技

        :param user_id: 用户ID
        :param tech_id: 科技ID
        :param skip_checks: 是否跳过解锁条件检查（用于自动解锁场景）
        :return: 是否解锁成功, 解锁失败的原因
        """
        # 检查是否已解锁
        if self.is_technology_unlocked(user_id, tech_id):
            return False, Messages.TECHNOLOGY_ALREADY_UNLOCKED.value

        # 获取科技信息
        technology = self.get_technology_by_id(tech_id)
        if not technology:
            return False, Messages.TECHNOLOGY_NOT_FOUND.value

        # 获取用户信息
        user = self.user_dao.get_user_by_id(user_id)
        if not user:
            return False, Messages.NOT_REGISTERED.value

        # 检查解锁条件（除非明确跳过）
        if not skip_checks:
            can_unlock, _ = self.can_unlock_technology(user, technology)
            if not can_unlock:
                return False, _

        # 扣除金币（如果有要求且不是自动解锁）
        if technology.required_gold > 0 and not skip_checks:
            if user.gold < technology.required_gold:
                return False, Messages.TECHNOLOGY_UNLOCK_FAILED_GOLD_NOT_ENOUGH.value.format(required_gold=technology.required_gold)

            # 原子操作更新金币，避免并发问题
            res = self.user_dao.deduct_gold(user_id, technology.required_gold)
            if not res:
                return False,Messages.GOLD_UPDATE_FAILED.value

        # 记录解锁时间
        res = self.tech_dao.record_unlock_time(user_id, tech_id)
        if not res:
            return False, Messages.SQL_FAILED.value

        # 应用科技效果
        self._apply_technology_effect(user_id, technology)

        return True, Messages.TECHNOLOGY_CAN_UNLOCK.value

    def _apply_technology_effect(self, user_id: str, technology: Technology) -> None:
        """应用科技效果"""
        if technology.effect_type == "auto_fishing":
            self.fish_dao.update_user_auto_fishing(user_id, True)

        elif technology.effect_type == "fish_pond_capacity":
            self.tech_dao.update_user_pond_capacity(user_id, technology.effect_value)

        # 其他科技效果可以在这里扩展
        # 如解锁鱼竿、鱼饵等类型的科技不需要特殊处理

    async def tech_tree_command(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, Any]:
        """科技树命令：展示所有科技及其解锁状态"""
        user_id = event.get_sender_id()
        user = self.user_dao.get_user_by_id(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 获取所有科技和用户已解锁科技
        technologies = self.get_all_technologies()
        user_tech_ids = self.get_user_unlocked_tech_ids(user_id)

        # 构建科技树信息
        tech_info = "=== 科技树 ===\n\n"
        for tech in technologies:
            status = "✅ 已解锁" if tech.id in user_tech_ids else "🔒 未解锁"
            req_level = f"等级要求: {tech.required_level}级"
            req_gold = f"金币消耗: {tech.required_gold}"

            # 处理前置科技
            req_techs = []
            for req_id in tech.required_tech_ids:
                req_tech = self.get_technology_by_id(req_id)
                if req_tech:
                    req_techs.append(req_tech.display_name)

            req_techs_str = f"前置科技: {', '.join(req_techs)}" if req_techs else "前置科技: 无"

            tech_info += f"【{tech.display_name}】{status}\n"
            tech_info += f"  {tech.description}\n"
            tech_info += f"  {req_level} | {req_gold} | {req_techs_str}\n\n"

        # 添加使用说明
        tech_info += "使用方法:\n"
        tech_info += "查看科技: /科技树\n"
        tech_info += "解锁科技: /解锁科技 科技名称\n"

        yield event.plain_result(tech_info)

    async def unlock_tech_command(self, event: AstrMessageEvent, tech_name: str) -> AsyncGenerator[
        MessageEventResult, Any]:
        """解锁科技命令：处理用户的科技解锁请求"""
        user_id = event.get_sender_id()
        user = self.user_dao.get_user_by_id(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 查找科技
        technology = self.get_technology_by_name(tech_name)
        if not technology:
            yield event.plain_result(Messages.TECHNOLOGY_NOT_FOUND.value)
            return

        # 检查是否可以解锁
        can_unlock, message = self.can_unlock_technology(user, technology)
        if not can_unlock:
            yield event.plain_result(message)
            return

        success, _msg = self.unlock_technology(user_id, technology.id)
        # 解锁科技
        if success:
            yield event.plain_result(f"{Messages.TECHNOLOGY_UNLOCK_SUCCESS.value}: {technology.display_name}！\n{technology.description}")
        else:
            yield event.plain_result(_msg)
