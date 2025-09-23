from enum import Enum
from datetime import datetime, timedelta

from ..models import User
from ..data.constants import Constants


class Messages(Enum):
    # 通用
    NOT_REGISTERED = "您还未注册，请先使用 /注册 命令注册账号"
    ALREADY_REGISTERED = "您已经注册过了！"
    REGISTRATION_SUCCESS = "注册成功！欢迎来到大Gai庄园！"
    BALANCE_INFO = "当前金币余额"

    # 签到
    ALREADY_SIGNED_IN = "您今天已经签到过了！"
    SIGN_IN_SUCCESS = "签到成功！"
    SIGN_IN_GOLD = "获得金币"
    SIGN_IN_EXP = "获得经验"
    SIGN_IN_STREAK = "连续签到"

    # 等级相关
    LEVEL_INFO_HEADER = "📊 等级信息"
    LEVEL_CURRENT = "当前等级"
    LEVEL_EXP = "当前经验"
    LEVEL_PROGRESS = "升级进度"
    LEVEL_NEEDED = "距离升级还需"
    LEVEL_NEXT_REWARD = "下一等级奖励"
    LEVEL_MAX = "恭喜您已达到最高等级！"
    LEVEL_MAX_PRIVILEGE = "您已解锁所有等级特权！"

    # 升级/科技/成就
    LEVEL_UP_CONGRATS = "🎉 恭喜升级到"
    LEVEL_UP_REWARD = "获得金币奖励"
    LEVEL_UP_MAX = "您已达到最高等级！"
    TECH_UNLOCK = "🎉 成功解锁科技"
    ACHIEVEMENT_UNLOCK = "🎉 恭喜解锁新成就！"


class UserService:
    def __init__(self, db):
        self.db = db

    # ========== 用户注册 ==========

    def register_user(self, user_id: int) -> str:
        """注册新用户"""
        existing = self.get_user(user_id)
        if existing:
            return Messages.ALREADY_REGISTERED.value
        self.db.insert_user(user_id)
        return Messages.REGISTRATION_SUCCESS.value

    # ========== 获取用户信息 ==========

    def get_user(self, user_id: int) -> User | None:
        row = self.db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        return User.from_row(row) if row else None

    # ========== 金币余额查询 ==========

    def get_balance_message(self, user: User) -> str:
        return f"{Messages.BALANCE_INFO.value}: {user.gold}"

    # ========== 签到 ==========

    def sign_in(self, user: User) -> str:
        today = datetime.now().date()
        if user.last_sign_in and user.last_sign_in.date() == today:
            return Messages.ALREADY_SIGNED_IN.value

        # 计算连续签到
        streak = 1
        if user.last_sign_in and user.last_sign_in.date() == today - timedelta(days=1):
            streak = user.streak + 1

        # 计算奖励
        gold_reward = 100 + streak * 10
        exp_reward = 10 + streak * 2

        # 更新数据库
        self.db.update_user_sign_in(user.id, today, streak, gold_reward, exp_reward)

        exp_result = self.add_exp(user.id, exp_reward)
        return self._build_sign_in_message(gold_reward, exp_reward, streak, exp_result)

    def _build_sign_in_message(self, gold: int, exp: int, streak: int, exp_result: dict) -> str:
        parts = [
            Messages.SIGN_IN_SUCCESS.value,
            f"{Messages.SIGN_IN_GOLD.value}: {gold}",
            f"{Messages.SIGN_IN_EXP.value}: {exp}点",
            f"{Messages.SIGN_IN_STREAK.value}: {streak}天",
        ]
        if extra := self.handle_user_level_up(exp_result):
            parts.append(extra)
        return "\n\n".join(parts)

    # ========== 经验与升级 ==========

    def add_exp(self, user_id: int, amount: int) -> dict:
        """增加经验并检查是否升级"""
        user = self.get_user(user_id)
        new_exp = user.exp + amount
        self.db.update_user_exp(user_id, new_exp)

        result = {
            "leveled_up": False,
            "new_level": user.level,
            "level_up_reward": None,
            "unlocked_techs": [],
            "newly_achievements": [],
        }

        while user.level < Constants.MAX_LEVEL and new_exp >= self._get_exp_for_level(user.level):
            user.level += 1
            result["leveled_up"] = True
            result["new_level"] = user.level
            reward = self._get_level_up_reward(user.level)
            result["level_up_reward"] = reward
            self.db.reward_user_gold(user_id, reward)
            result["unlocked_techs"].extend(self._unlock_techs_for_level(user.level))
            result["newly_achievements"].extend(self._check_achievements(user_id, user.level))

        return result

    def handle_user_level_up(self, exp_result: dict) -> str:
        parts = []
        if exp_result["leveled_up"]:
            parts.append(self._format_level_up_message(exp_result))
        if exp_result["newly_achievements"]:
            ach_text = "\n".join(f"  · {a.name}: {a.description}" for a in exp_result["newly_achievements"])
            parts.append(f"{Messages.ACHIEVEMENT_UNLOCK.value}\n{ach_text}")
        return "\n\n".join(parts)

    def _format_level_up_message(self, exp_result: dict) -> str:
        lines = [f"{Messages.LEVEL_UP_CONGRATS.value} {exp_result['new_level']} 级！"]
        if exp_result["level_up_reward"]:
            lines.append(f"{Messages.LEVEL_UP_REWARD.value}: {exp_result['level_up_reward']}")
        if exp_result["new_level"] >= Constants.MAX_LEVEL:
            lines.append(Messages.LEVEL_UP_MAX.value)
        if exp_result["unlocked_techs"]:
            tech_msgs = [
                f"{Messages.TECH_UNLOCK.value}: {t.display_name}！\n{t.description}"
                for t in exp_result["unlocked_techs"]
            ]
            lines.append("\n\n".join(tech_msgs))
        return "\n".join(lines)

    # ========== 等级查询命令 ==========

    async def level_command(self, event):
        user = self.get_user(event.get_sender_id())
        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        if user.level >= Constants.MAX_LEVEL:
            msg = [
                Messages.LEVEL_INFO_HEADER.value,
                f"{Messages.LEVEL_CURRENT.value}: {user.level}",
                f"{Messages.LEVEL_EXP.value}: {user.exp}",
                Messages.LEVEL_MAX.value,
                Messages.LEVEL_MAX_PRIVILEGE.value,
            ]
        else:
            current_exp = self._get_exp_for_level(user.level - 1) if user.level > 1 else 0
            next_exp = self._get_exp_for_level(user.level)
            exp_in_level = user.exp - current_exp
            exp_needed = next_exp - user.exp
            next_reward = self._get_level_up_reward(user.level + 1)

            msg = [
                Messages.LEVEL_INFO_HEADER.value,
                f"{Messages.LEVEL_CURRENT.value}: {user.level}",
                f"{Messages.LEVEL_EXP.value}: {user.exp}",
                f"{Messages.LEVEL_PROGRESS.value}: {exp_in_level}/{next_exp - current_exp}",
                f"{Messages.LEVEL_NEEDED.value}: {exp_needed} 经验",
                f"{Messages.LEVEL_NEXT_REWARD.value}: {next_reward} 金币",
            ]
        yield event.plain_result("\n\n".join(msg))

    # ========== 内部辅助方法 ==========

    def _get_exp_for_level(self, level: int) -> int:
        return 100 * level * (level + 1) // 2  # 示例公式

    def _get_level_up_reward(self, level: int) -> int:
        return 50 * level

    def _unlock_techs_for_level(self, level: int):
        return self.db.fetch_techs_for_level(level)

    def _check_achievements(self, user_id: int, level: int):
        return self.db.check_and_unlock_achievements(user_id, level)
