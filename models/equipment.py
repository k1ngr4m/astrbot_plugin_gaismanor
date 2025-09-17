from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class Equipment:
    """装备基类"""
    id: int
    name: str
    rarity: int  # 稀有度 1-5星
    description: str
    price: int
    created_at: int = field(default_factory=lambda: int(time.time()))

@dataclass
class Rod(Equipment):
    """鱼竿类"""
    catch_bonus: float = 1.0  # 捕获加成
    weight_bonus: float = 1.0  # 重量加成
    level: int = 1
    exp: int = 0

@dataclass
class Accessory(Equipment):
    """饰品类"""
    effect_type: str = ""  # 效果类型
    effect_value: float = 0.0  # 效果值

@dataclass
class Bait(Equipment):
    """鱼饵类"""
    catch_rate_bonus: float = 1.0  # 捕获率加成
    duration: int = 300  # 持续时间(秒)