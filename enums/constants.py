from enum import IntEnum


class Constants:
    """项目常量定义"""

    # 等级相关常量
    MAX_LEVEL = 100  # 最大等级
    BASE_EXP_PER_LEVEL = 100  # 每级基础经验需求系数

    # 签到相关常量
    SIGN_IN_BASE_GOLD = 50  # 签到基础金币奖励
    SIGN_IN_BASE_EXP = 10  # 签到基础经验奖励
    SIGN_IN_STREAK_GOLD_INCREMENT = 20  # 连续签到金币奖励增量
    SIGN_IN_STREAK_EXP_INCREMENT = 2  # 连续签到经验奖励增量

    # 装备相关常量
    STARTER_ROD_TEMPLATE_ID = 1  # 新手鱼竿模板ID
    STARTING_GOLD = 200  # 初始金币数量

    FISHING_COOLDOWN = 20  # 钓鱼冷却时间（秒）

    POND_BASE_CAPACITY = 50 # 鱼塘初始容量
    POND_UPGRADE_CONFIG = [
        (500, 50),  # 等级0->1: 费用500, 扩容50
        (1000, 100),  # 等级1->2: 费用1000, 扩容100
        (2000, 150),
        (5000, 200),
        (10000, 250)
    ]