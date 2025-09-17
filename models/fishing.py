from dataclasses import dataclass
from typing import Optional

@dataclass
class FishTemplate:
    """鱼类模板"""
    id: int
    name: str
    description: str
    rarity: int  # 稀有度 1-5星
    base_value: int  # 基础价值
    min_weight: int  # 最小重量(g)
    max_weight: int  # 最大重量(g)
    icon_url: Optional[str] = None

@dataclass
class RodTemplate:
    """鱼竿模板"""
    id: int
    name: str
    description: str
    rarity: int  # 稀有度 1-5星
    source: str  # 来源: shop, gacha
    purchase_cost: Optional[int]
    quality_mod: float = 1.0  # 品质加成
    quantity_mod: float = 1.0  # 数量加成
    rare_mod: float = 0.0  # 稀有度加成
    durability: Optional[int] = None  # 耐久度
    icon_url: Optional[str] = None

@dataclass
class AccessoryTemplate:
    """饰品模板"""
    id: int
    name: str
    description: str
    rarity: int  # 稀有度 1-5星
    slot_type: str  # 插槽类型
    quality_mod: float = 1.0  # 品质加成
    quantity_mod: float = 1.0  # 数量加成
    rare_mod: float = 0.0  # 稀有度加成
    coin_mod: float = 1.0  # 金币加成
    other_desc: Optional[str] = None  # 其他描述
    icon_url: Optional[str] = None

@dataclass
class BaitTemplate:
    """鱼饵模板"""
    id: int
    name: str
    description: str
    rarity: int  # 稀有度 1-5星
    effect_description: str  # 效果描述
    cost: int  # 购买成本
    duration_minutes: int = 0  # 持续时间(分钟)
    required_rod_rarity: int = 0  # 需要的鱼竿稀有度
    success_rate_modifier: float = 0.0  # 成功率加成
    rare_chance_modifier: float = 0.0  # 稀有鱼几率加成
    garbage_reduction_modifier: float = 0.0  # 垃圾减少加成
    value_modifier: float = 1.0  # 价值加成
    quantity_modifier: float = 1.0  # 数量加成
    is_consumable: bool = True  # 是否消耗

@dataclass
class FishingResult:
    """钓鱼结果"""
    success: bool
    fish: Optional[FishTemplate] = None
    weight: float = 0.0
    value: int = 0
    message: str = ""