from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Technology:
    """科技树节点"""
    id: int
    name: str
    description: str
    required_level: int  # 需要的用户等级
    required_gold: int   # 需要的金币
    required_tech_ids: List[int]  # 需要前置科技ID列表
    effect_type: str     # 效果类型 (如 "auto_fishing", "fish_pond_capacity", etc.)
    effect_value: int    # 效果值
    display_name: str    # 显示名称

@dataclass
class UserTechnology:
    """用户科技"""
    id: int
    user_id: str
    tech_id: int
    unlocked_at: int     # 解锁时间