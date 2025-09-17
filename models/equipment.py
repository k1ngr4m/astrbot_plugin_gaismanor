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
    quality_mod: float = 1.0  # 品质加成
    quantity_mod: float = 1.0  # 数量加成
    durability: int = 0  # 耐久度
    level: int = 1
    exp: int = 0
    is_equipped: bool = False

@dataclass
class Accessory(Equipment):
    """饰品类"""
    quality_mod: float = 1.0  # 品质加成
    quantity_mod: float = 1.0  # 数量加成
    coin_mod: float = 1.0  # 金币加成
    other_desc: Optional[str] = None  # 其他描述
    is_equipped: bool = False

@dataclass
class Bait(Equipment):
    """鱼饵类"""
    effect_description: str = ""  # 效果描述
    duration_minutes: int = 0  # 持续时间(分钟)
    success_rate_modifier: float = 0.0  # 成功率加成
    rare_chance_modifier: float = 0.0  # 稀有鱼几率加成
    garbage_reduction_modifier: float = 0.0  # 垃圾减少加成
    value_modifier: float = 1.0  # 价值加成
    quantity_modifier: float = 1.0  # 数量加成
    is_consumable: bool = True  # 是否消耗
    quantity: int = 0  # 库存数量