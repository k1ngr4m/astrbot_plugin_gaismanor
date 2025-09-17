from typing import Optional, List
from ..models.user import User, FishInventory, RodInstance, AccessoryInstance, BaitInventory
from ..models.database import DatabaseManager
import time

class UserService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        result = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return User(
                user_id=result['user_id'],
                nickname=result['nickname'],
                gold=result['gold'],
                exp=result['exp'],
                level=result['level'],
                fishing_count=result['fishing_count'],
                total_fish_weight=result['total_fish_weight'],
                total_income=result['total_income'],
                last_fishing_time=result['last_fishing_time'],
                auto_fishing=result['auto_fishing'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None

    def create_user(self, user_id: str, nickname: str) -> User:
        """创建新用户"""
        now = int(time.time())
        user = User(user_id=user_id, nickname=nickname, created_at=now, updated_at=now)

        self.db.execute_query(
            """INSERT INTO users (
                user_id, nickname, gold, exp, level, fishing_count,
                total_fish_weight, total_income, last_fishing_time,
                auto_fishing, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user.user_id, user.nickname, user.gold, user.exp, user.level,
                user.fishing_count, user.total_fish_weight, user.total_income,
                user.last_fishing_time, user.auto_fishing, user.created_at, user.updated_at
            )
        )
        return user

    def update_user(self, user: User) -> None:
        """更新用户信息"""
        user.updated_at = int(time.time())
        self.db.execute_query(
            """UPDATE users SET
                nickname=?, gold=?, exp=?, level=?, fishing_count=?,
                total_fish_weight=?, total_income=?, last_fishing_time=?,
                auto_fishing=?, updated_at=?
            WHERE user_id=?""",
            (
                user.nickname, user.gold, user.exp, user.level, user.fishing_count,
                user.total_fish_weight, user.total_income, user.last_fishing_time,
                user.auto_fishing, user.updated_at, user.user_id
            )
        )

    def add_gold(self, user_id: str, amount: int) -> bool:
        """增加用户金币"""
        user = self.get_user(user_id)
        if user:
            user.gold += amount
            self.update_user(user)
            return True
        return False

    def deduct_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        user = self.get_user(user_id)
        if user and user.gold >= amount:
            user.gold -= amount
            self.update_user(user)
            return True
        return False

    def get_user_fish_inventory(self, user_id: str) -> List[FishInventory]:
        """获取用户鱼类库存"""
        results = self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )
        return [
            FishInventory(
                id=row['id'],
                user_id=row['user_id'],
                fish_template_id=row['fish_template_id'],
                weight=row['weight'],
                value=row['value'],
                caught_at=row['caught_at']
            ) for row in results
        ]

    def get_user_rods(self, user_id: str) -> List[RodInstance]:
        """获取用户所有鱼竿"""
        results = self.db.fetch_all(
            "SELECT * FROM user_rod_instances WHERE user_id = ?",
            (user_id,)
        )
        return [
            RodInstance(
                id=row['id'],
                user_id=row['user_id'],
                rod_template_id=row['rod_template_id'],
                level=row['level'],
                exp=row['exp'],
                is_equipped=row['is_equipped'],
                acquired_at=row['acquired_at']
            ) for row in results
        ]

    def get_user_accessories(self, user_id: str) -> List[AccessoryInstance]:
        """获取用户所有饰品"""
        results = self.db.fetch_all(
            "SELECT * FROM user_accessory_instances WHERE user_id = ?",
            (user_id,)
        )
        return [
            AccessoryInstance(
                id=row['id'],
                user_id=row['user_id'],
                accessory_template_id=row['accessory_template_id'],
                is_equipped=row['is_equipped'],
                acquired_at=row['acquired_at']
            ) for row in results
        ]

    def get_user_bait_inventory(self, user_id: str) -> List[BaitInventory]:
        """获取用户鱼饵库存"""
        results = self.db.fetch_all(
            "SELECT * FROM user_bait_inventory WHERE user_id = ?",
            (user_id,)
        )
        return [
            BaitInventory(
                id=row['id'],
                user_id=row['user_id'],
                bait_template_id=row['bait_template_id'],
                quantity=row['quantity']
            ) for row in results
        ]

    def get_equipped_rod(self, user_id: str) -> Optional[RodInstance]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )
        if result:
            return RodInstance(
                id=result['id'],
                user_id=result['user_id'],
                rod_template_id=result['rod_template_id'],
                level=result['level'],
                exp=result['exp'],
                is_equipped=result['is_equipped'],
                acquired_at=result['acquired_at']
            )
        return None

    def get_equipped_accessory(self, user_id: str) -> Optional[AccessoryInstance]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            "SELECT * FROM user_accessory_instances WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )
        if result:
            return AccessoryInstance(
                id=result['id'],
                user_id=result['user_id'],
                accessory_template_id=result['accessory_template_id'],
                is_equipped=result['is_equipped'],
                acquired_at=result['acquired_at']
            )
        return None