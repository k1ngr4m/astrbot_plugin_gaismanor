"""
金币相关的工具函数
"""


def add_gold_to_user(user, amount: int):
    """为用户增加金币"""
    if amount <= 0:
        return False

    user.gold += amount
    return True


def deduct_gold_from_user(user, amount: int) -> bool:
    """从用户扣除金币"""
    if amount <= 0:
        return False

    if user.gold >= amount:
        user.gold -= amount
        return True
    return False