"""
签到相关的工具函数
"""
from ..enums.constants import Constants
import time


# 签到常量
SIGN_IN_BASE_GOLD = Constants.SIGN_IN_BASE_GOLD
SIGN_IN_BASE_EXP = Constants.SIGN_IN_BASE_EXP
SIGN_IN_STREAK_GOLD_INCREMENT = Constants.SIGN_IN_STREAK_GOLD_INCREMENT
SIGN_IN_STREAK_EXP_INCREMENT = Constants.SIGN_IN_STREAK_EXP_INCREMENT


def calculate_sign_in_rewards(streak: int) -> tuple:
    """计算签到奖励"""
    reward_gold = SIGN_IN_BASE_GOLD + (streak - 1) * SIGN_IN_STREAK_GOLD_INCREMENT
    reward_exp = SIGN_IN_BASE_EXP + (streak - 1) * SIGN_IN_STREAK_EXP_INCREMENT
    return reward_gold, reward_exp


def get_current_date() -> str:
    """获取当前日期字符串"""
    return time.strftime('%Y-%m-%d', time.localtime())


def get_yesterday_date() -> str:
    """获取昨天日期字符串"""
    return time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))