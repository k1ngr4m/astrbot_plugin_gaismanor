"""
钓鱼相关的工具函数
"""
import random
from typing import List
from ..models.fishing import FishTemplate


def calculate_exp_gain(fish: FishTemplate, weight: float, value: int, user_level: int = 1) -> int:
    """计算钓鱼获得的经验值"""
    # 基础经验 = 鱼的稀有度 * 10 + 价值 / 10 + 重量 / 10
    base_exp = fish.rarity * 10 + value // 10 + int(weight * 10)

    # 等级加成：每级增加1%经验
    level_bonus = 1 + (user_level - 1) * 0.01

    # 计算最终经验
    final_exp = int(base_exp * level_bonus)

    # 最小经验值为1
    return max(1, final_exp)


def select_fish_by_rarity(filtered_fish_templates: List[FishTemplate]) -> FishTemplate:
    """根据稀有度权重选择鱼类"""
    # 根据稀有度权重选择鱼类
    # 稀有度越高，权重越低（越难钓到）
    weights = [1.0 / (fish.rarity ** 2) for fish in filtered_fish_templates]
    return random.choices(filtered_fish_templates, weights=weights)[0]


def calculate_fish_value_and_weight(caught_fish: FishTemplate) -> tuple:
    """计算鱼的价值和重量"""
    # 计算鱼的重量
    final_weight = random.uniform(caught_fish.min_weight / 1000.0, caught_fish.max_weight / 1000.0)

    # 计算平均重量（公斤）
    average_weight = ((caught_fish.min_weight + caught_fish.max_weight) / 2) / 1000.0

    # 使用新的价值公式：价值 = 基础价值 × (1 + 重量 ÷ 平均重量)
    final_value = int(caught_fish.base_value * (1 + final_weight / average_weight))

    return final_weight, final_value


def calculate_catch_rate(base_rate: float, catch_rate_bonus: float, max_rate: float = 0.95) -> float:
    """计算最终钓鱼成功率"""
    return min(base_rate * catch_rate_bonus, max_rate)


def calculate_rod_durability_cost() -> int:
    """计算鱼竿耐久度消耗"""
    return random.randint(1, 5)