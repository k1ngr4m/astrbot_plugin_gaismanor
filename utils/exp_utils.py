"""
经验值相关的工具函数
"""
import math
from typing import List
from ..models.user import User
from ..models.tech import Technology
from ..enums.constants import Constants


# 常量定义
MAX_LEVEL = Constants.MAX_LEVEL
BASE_EXP_PER_LEVEL = Constants.BASE_EXP_PER_LEVEL


def calculate_level(exp: int) -> int:
    """根据经验计算等级"""
    if exp <= 0:
        return 1

    # 每级所需经验 = 100 * 等级^2
    level = int(math.sqrt(exp / BASE_EXP_PER_LEVEL)) + 1
    return min(level, MAX_LEVEL)


def get_exp_for_level(level: int) -> int:
    """获取升级到指定等级所需的总经验"""
    capped_level = max(1, min(level, MAX_LEVEL))
    return BASE_EXP_PER_LEVEL * (capped_level ** 2)


def precompute_level_rewards() -> List[int]:
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


def get_level_up_reward(level: int, level_rewards: List[int]) -> int:
    """根据等级获取升级奖励金币"""
    if 1 <= level <= MAX_LEVEL:
        return level_rewards[level]
    return 0


def check_and_unlock_technologies(user: User, all_technologies: List[Technology],
                                user_tech_ids: set) -> List[Technology]:
    """检查并自动解锁符合条件的科技"""
    unlocked_techs = []

    # 检查每个科技是否满足解锁条件
    for tech in all_technologies:
        if tech.id in user_tech_ids:
            continue  # 已解锁，跳过

        # 检查等级要求和前置科技
        if (user.level >= tech.required_level and
                all(req_id in user_tech_ids for req_id in tech.required_tech_ids)):

            unlocked_techs.append(tech)

    return unlocked_techs