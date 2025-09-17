from dataclasses import dataclass, field
from typing import Optional, List
import time

@dataclass
class User:
    """用户实体类"""
    user_id: str
    nickname: str
    gold: int = 100  # 金币
    exp: int = 0     # 经验值
    level: int = 1   # 等级
    fishing_count: int = 0  # 钓鱼次数
    total_fish_weight: float = 0.0  # 总鱼类重量
    total_income: int = 0   # 总收入
    last_fishing_time: int = 0  # 上次钓鱼时间
    auto_fishing: bool = False  # 是否开启自动钓鱼
    created_at: int = field(default_factory=lambda: int(time.time()))
    updated_at: int = field(default_factory=lambda: int(time.time()))

@dataclass
class FishInventory:
    """用户鱼类库存"""
    id: int
    user_id: str
    fish_template_id: int
    weight: float
    value: int
    caught_at: int

@dataclass
class RodInstance:
    """用户鱼竿实例"""
    id: int
    user_id: str
    rod_template_id: int
    level: int = 1
    exp: int = 0
    is_equipped: bool = False
    acquired_at: int = field(default_factory=lambda: int(time.time()))

@dataclass
class AccessoryInstance:
    """用户饰品实例"""
    id: int
    user_id: str
    accessory_template_id: int
    is_equipped: bool = False
    acquired_at: int = field(default_factory=lambda: int(time.time()))

@dataclass
class BaitInventory:
    """用户鱼饵库存"""
    id: int
    user_id: str
    bait_template_id: int
    quantity: int