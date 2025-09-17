from dataclasses import dataclass
from typing import Optional

@dataclass
class FishTemplate:
    """鱼类模板"""
    id: int
    name: str
    rarity: int  # 稀有度 1-5星
    base_value: int  # 基础价值
    description: str
    catch_rate: float = 1.0  # 捕获率

@dataclass
class RodTemplate:
    """鱼竿模板"""
    id: int
    name: str
    rarity: int  # 稀有度 1-5星
    description: str
    price: int
    catch_bonus: float = 1.0  # 捕获加成
    weight_bonus: float = 1.0  # 重量加成

@dataclass
class AccessoryTemplate:
    """饰品模板"""
    id: int
    name: str
    rarity: int  # 稀有度 1-5星
    description: str
    price: int
    effect_type: str  # 效果类型
    effect_value: float  # 效果值

@dataclass
class BaitTemplate:
    """鱼饵模板"""
    id: int
    name: str
    rarity: int  # 稀有度 1-5星
    description: str
    price: int
    catch_rate_bonus: float = 1.0  # 捕获率加成
    duration: int = 300  # 持续时间(秒)

@dataclass
class FishingResult:
    """钓鱼结果"""
    success: bool
    fish: Optional[FishTemplate] = None
    weight: float = 0.0
    value: int = 0
    message: str = ""