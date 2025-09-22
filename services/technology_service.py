from typing import List, Optional
import json
import time

from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.tech import Technology, UserTechnology
from ..models.database import DatabaseManager

class TechnologyService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_all_technologies(self) -> List[Technology]:
        """获取所有科技"""
        results = self.db.fetch_all("SELECT * FROM technologies ORDER BY id")
        technologies = []
        for row in results:
            tech = Technology(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                required_level=row['required_level'],
                required_gold=row['required_gold'],
                required_tech_ids=json.loads(row['required_tech_ids'] or "[]"),
                effect_type=row['effect_type'],
                effect_value=row['effect_value'],
                display_name=row['display_name']
            )
            technologies.append(tech)
        return technologies

    def get_user_technologies(self, user_id: str) -> List[UserTechnology]:
        """获取用户已解锁的科技"""
        results = self.db.fetch_all(
            "SELECT * FROM user_technologies WHERE user_id = ?",
            (user_id,)
        )
        return [
            UserTechnology(
                id=row['id'],
                user_id=row['user_id'],
                tech_id=row['tech_id'],
                unlocked_at=row['unlocked_at']
            ) for row in results
        ]

    def get_technology_by_id(self, tech_id: int) -> Optional[Technology]:
        """根据ID获取科技"""
        result = self.db.fetch_one(
            "SELECT * FROM technologies WHERE id = ?",
            (tech_id,)
        )
        if result:
            return Technology(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                required_level=result['required_level'],
                required_gold=result['required_gold'],
                required_tech_ids=json.loads(result['required_tech_ids'] or "[]"),
                effect_type=result['effect_type'],
                effect_value=result['effect_value'],
                display_name=result['display_name']
            )
        return None

    def get_technology_by_name(self, name: str) -> Optional[Technology]:
        """根据名称获取科技"""
        result = self.db.fetch_one(
            "SELECT * FROM technologies WHERE name = ?",
            (name,)
        )
        if result:
            return Technology(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                required_level=result['required_level'],
                required_gold=result['required_gold'],
                required_tech_ids=json.loads(result['required_tech_ids'] or "[]"),
                effect_type=result['effect_type'],
                effect_value=result['effect_value'],
                display_name=result['display_name']
            )
        return None

    def is_technology_unlocked(self, user_id: str, tech_id: int) -> bool:
        """检查用户是否已解锁指定科技"""
        result = self.db.fetch_one(
            "SELECT id FROM user_technologies WHERE user_id = ? AND tech_id = ?",
            (user_id, tech_id)
        )
        return result is not None

    def is_auto_fishing_unlocked(self, user_id: str) -> bool:
        """检查用户是否已解锁自动钓鱼功能"""
        result = self.db.fetch_one(
            """SELECT ut.id FROM user_technologies ut
               JOIN technologies t ON ut.tech_id = t.id
               WHERE ut.user_id = ? AND t.name = '自动钓鱼'""",
            (user_id,)
        )
        return result is not None

    def can_unlock_technology(self, user: User, technology: Technology) -> tuple[bool, str]:
        """检查用户是否可以解锁指定科技"""
        # 检查等级要求
        if user.level < technology.required_level:
            return False, f"需要达到{technology.required_level}级才能解锁此科技"

        # 检查金币要求
        if user.gold < technology.required_gold:
            return False, f"金币不足，需要{technology.required_gold}金币"

        # 检查前置科技要求
        user_tech_ids = [ut.tech_id for ut in self.get_user_technologies(user.user_id)]
        missing_techs = []
        for req_tech_id in technology.required_tech_ids:
            if req_tech_id not in user_tech_ids:
                req_tech = self.get_technology_by_id(req_tech_id)
                if req_tech:
                    missing_techs.append(req_tech.display_name)

        if missing_techs:
            return False, f"需要先解锁以下科技: {', '.join(missing_techs)}"

        # 检查是否已解锁
        if self.is_technology_unlocked(user.user_id, technology.id):
            return False, "您已经解锁了此科技"

        return True, "可以解锁"

    def unlock_technology(self, user_id: str, tech_id: int) -> bool:
        """解锁科技"""
        # 检查是否已解锁
        if self.is_technology_unlocked(user_id, tech_id):
            return False

        technology = self.get_technology_by_id(tech_id)
        if not technology:
            return False

        user = self._get_user(user_id)
        if not user:
            return False

        # 检查是否可以解锁
        can_unlock, _ = self.can_unlock_technology(user, technology)
        if not can_unlock:
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (technology.required_gold, user_id)
        )

        # 记录解锁时间
        self.db.execute_query(
            """INSERT INTO user_technologies
               (user_id, tech_id, unlocked_at)
               VALUES (?, ?, ?)""",
            (user_id, tech_id, int(time.time()))
        )

        # 应用科技效果
        self._apply_technology_effect(user_id, technology)

        return True

    def _apply_technology_effect(self, user_id: str, technology: Technology):
        """应用科技效果"""
        if technology.effect_type == "auto_fishing":
            self.db.execute_query(
                "UPDATE users SET auto_fishing = TRUE WHERE user_id = ?",
                (user_id,)
            )
        elif technology.effect_type == "fish_pond_capacity":
            self.db.execute_query(
                "UPDATE users SET fish_pond_capacity = fish_pond_capacity + ? WHERE user_id = ?",
                (technology.effect_value, user_id)
            )

    def _get_user(self, user_id: str) -> Optional[User]:
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

    async def tech_tree_command(self, event: AstrMessageEvent):
        """科技树命令"""
        user_id = event.get_sender_id()
        user = self._get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        technologies = self.get_all_technologies()
        user_tech_ids = [ut.tech_id for ut in self.get_user_technologies(user_id)]

        tech_info = "=== 科技树 ===\n\n"
        for tech in technologies:
            status = "✅ 已解锁" if tech.id in user_tech_ids else "🔒 未解锁"
            req_level = f"等级要求: {tech.required_level}级"
            req_gold = f"金币消耗: {tech.required_gold}"
            req_techs = []
            for req_id in tech.required_tech_ids:
                req_tech = self.get_technology_by_id(req_id)
                if req_tech:
                    req_techs.append(req_tech.display_name)

            req_techs_str = f"前置科技: {', '.join(req_techs)}" if req_techs else "前置科技: 无"

            tech_info += f"【{tech.display_name}】{status}\n"
            tech_info += f"  {tech.description}\n"
            tech_info += f"  {req_level} | {req_gold} | {req_techs_str}\n\n"

        tech_info += "使用方法:\n"
        tech_info += "查看科技: /科技树\n"
        tech_info += "当您达到科技的等级要求时，科技将自动解锁\n"
        yield event.plain_result(tech_info)

    async def unlock_tech_command(self, event: AstrMessageEvent, tech_name: str):
        """解锁科技命令"""
        user_id = event.get_sender_id()
        user = self._get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        technology = self.get_technology_by_name(tech_name)
        if not technology:
            yield event.plain_result("未找到指定的科技")
            return

        # 检查是否可以解锁
        can_unlock, message = self.can_unlock_technology(user, technology)
        if not can_unlock:
            yield event.plain_result(message)
            return

        # 解锁科技
        if self.unlock_technology(user_id, technology.id):
            yield event.plain_result(f"🎉 成功解锁科技: {technology.display_name}！\n{technology.description}")
        else:
            yield event.plain_result("解锁科技失败")

    def unlock_technology(self, user_id: str, tech_id: int) -> bool:
        """解锁科技"""
        # 检查是否已解锁
        if self.is_technology_unlocked(user_id, tech_id):
            return False

        technology = self.get_technology_by_id(tech_id)
        if not technology:
            return False

        user = self._get_user(user_id)
        if not user:
            return False

        # 对于自动解锁的科技，不需要检查是否可以解锁
        # 但为了兼容手动调用的情况，仍然保留检查逻辑
        # 如果用户等级不足或金币不足，则不进行手动解锁
        if user.level < technology.required_level:
            return False

        # 扣除金币（如果有要求）
        if technology.required_gold > 0:
            if user.gold < technology.required_gold:
                return False
            self.db.execute_query(
                "UPDATE users SET gold = gold - ? WHERE user_id = ?",
                (technology.required_gold, user_id)
            )

        # 记录解锁时间
        self.db.execute_query(
            """INSERT INTO user_technologies
               (user_id, tech_id, unlocked_at)
               VALUES (?, ?, ?)""",
            (user_id, tech_id, int(time.time()))
        )

        # 应用科技效果
        self._apply_technology_effect(user_id, technology)

        return True