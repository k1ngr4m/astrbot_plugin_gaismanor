from typing import List, Optional
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
import time

class ShopService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_rod_shop_items(self) -> List[Rod]:
        """获取鱼竿商店商品"""
        results = self.db.fetch_all("SELECT * FROM rod_templates WHERE source = 'shop'")
        return [
            Rod(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['purchase_cost'] or 0,
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                durability=row['durability'] or 0
            ) for row in results
        ]

    def get_accessory_shop_items(self) -> List[Accessory]:
        """获取饰品商店商品"""
        results = self.db.fetch_all("SELECT * FROM accessory_templates")
        return [
            Accessory(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=100,  # 默认价格，实际应从配置中获取
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc']
            ) for row in results
        ]

    def get_bait_shop_items(self) -> List[Bait]:
        """获取鱼饵商店商品"""
        results = self.db.fetch_all("SELECT * FROM bait_templates")
        return [
            Bait(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['cost'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=row['is_consumable']
            ) for row in results
        ]

    def buy_rod(self, user_id: str, rod_template_id: int) -> bool:
        """购买鱼竿"""
        # 获取鱼竿模板信息
        rod_template = self.db.fetch_one(
            "SELECT * FROM rod_templates WHERE id = ?",
            (rod_template_id,)
        )
        if not rod_template:
            return False

        # 检查用户金币是否足够
        user = self.db.fetch_one(
            "SELECT gold FROM users WHERE user_id = ?",
            (user_id,)
        )
        if not user or user['gold'] < (rod_template['purchase_cost'] or 0):
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (rod_template['purchase_cost'], user_id)
        )

        # 添加到用户鱼竿库存
        self.db.execute_query(
            """INSERT INTO user_rod_instances
               (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
               VALUES (?, ?, 1, 0, FALSE, ?, ?)""",
            (user_id, rod_template_id, int(time.time()), rod_template['durability'] or 0)
        )

        return True

    def buy_accessory(self, user_id: str, accessory_template_id: int) -> bool:
        """购买饰品"""
        # 获取饰品模板信息
        accessory_template = self.db.fetch_one(
            "SELECT * FROM accessory_templates WHERE id = ?",
            (accessory_template_id,)
        )
        if not accessory_template:
            return False

        # 检查用户金币是否足够 (默认价格100金币)
        user = self.db.fetch_one(
            "SELECT gold FROM users WHERE user_id = ?",
            (user_id,)
        )
        if not user or user['gold'] < 100:
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (100, user_id)
        )

        # 添加到用户饰品库存
        self.db.execute_query(
            """INSERT INTO user_accessory_instances
               (user_id, accessory_template_id, is_equipped, acquired_at)
               VALUES (?, ?, FALSE, ?)""",
            (user_id, accessory_template_id, int(time.time()))
        )

        return True

    def buy_bait(self, user_id: str, bait_template_id: int, quantity: int = 1) -> bool:
        """购买鱼饵"""
        # 获取鱼饵模板信息
        bait_template = self.db.fetch_one(
            "SELECT * FROM bait_templates WHERE id = ?",
            (bait_template_id,)
        )
        if not bait_template:
            return False

        # 计算总价
        total_price = bait_template['cost'] * quantity

        # 检查用户金币是否足够
        user = self.db.fetch_one(
            "SELECT gold FROM users WHERE user_id = ?",
            (user_id,)
        )
        if not user or user['gold'] < total_price:
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (total_price, user_id)
        )

        # 检查是否已有该鱼饵库存
        existing_bait = self.db.fetch_one(
            "SELECT quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
            (user_id, bait_template_id)
        )

        if existing_bait:
            # 更新数量
            self.db.execute_query(
                "UPDATE user_bait_inventory SET quantity = quantity + ? WHERE user_id = ? AND bait_template_id = ?",
                (quantity, user_id, bait_template_id)
            )
        else:
            # 添加新的鱼饵库存
            self.db.execute_query(
                """INSERT INTO user_bait_inventory
                   (user_id, bait_template_id, quantity)
                   VALUES (?, ?, ?)""",
                (user_id, bait_template_id, quantity)
            )

        return True

    def sell_fish(self, user_id: str, fish_inventory_id: int) -> bool:
        """出售鱼类"""
        # 获取鱼类信息
        fish_inventory = self.db.fetch_one(
            """SELECT ufi.*, ft.base_value FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ? AND ufi.id = ?""",
            (user_id, fish_inventory_id)
        )
        if not fish_inventory:
            return False

        # 计算出售价格 (按基础价值的80%)
        sell_price = int(fish_inventory['base_value'] * 0.8)

        # 添加金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (sell_price, user_id)
        )

        # 删除鱼类库存
        self.db.execute_query(
            "DELETE FROM user_fish_inventory WHERE user_id = ? AND id = ?",
            (user_id, fish_inventory_id)
        )

        return True

    def sell_rod(self, user_id: str, rod_instance_id: int) -> bool:
        """出售鱼竿"""
        # 获取鱼竿信息
        rod_instance = self.db.fetch_one(
            """SELECT uri.*, rt.purchase_cost FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.id = ?""",
            (user_id, rod_instance_id)
        )
        if not rod_instance:
            return False

        # 检查是否是装备中的鱼竿
        if rod_instance['is_equipped']:
            return False

        # 计算出售价格 (按原价的50%)
        sell_price = int((rod_instance['purchase_cost'] or 0) * 0.5)

        # 添加金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (sell_price, user_id)
        )

        # 删除鱼竿实例
        self.db.execute_query(
            "DELETE FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_instance_id)
        )

        return True

    def sell_accessory(self, user_id: str, accessory_instance_id: int) -> bool:
        """出售饰品"""
        # 获取饰品信息
        accessory_instance = self.db.fetch_one(
            """SELECT uai.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.id = ?""",
            (user_id, accessory_instance_id)
        )
        if not accessory_instance:
            return False

        # 检查是否是装备中的饰品
        if accessory_instance['is_equipped']:
            return False

        # 计算出售价格 (按原价的50%)
        sell_price = 50  # 默认售价

        # 添加金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (sell_price, user_id)
        )

        # 删除饰品实例
        self.db.execute_query(
            "DELETE FROM user_accessory_instances WHERE user_id = ? AND id = ?",
            (user_id, accessory_instance_id)
        )

        return True