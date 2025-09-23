"""
抽奖数据访问对象
"""
import time
from typing import List, Optional, Dict, Any
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class GachaDAO(BaseDAO):
    """抽奖数据访问对象，封装所有抽奖相关的数据库操作"""

    def get_enabled_gacha_pools(self) -> List[Dict[str, Any]]:
        """获取所有启用的卡池"""
        return self.db.fetch_all("SELECT * FROM gacha_pools WHERE enabled = TRUE ORDER BY sort_order, id")

    def get_gacha_pool_rarity_weights(self, pool_id: int) -> List[Dict[str, Any]]:
        """获取卡池稀有度权重"""
        return self.db.fetch_all(
            "SELECT rarity, weight FROM gacha_pool_rarity_weights WHERE pool_id = ?",
            (pool_id,)
        )

    def get_gacha_pool_items(self, pool_id: int) -> List[Dict[str, Any]]:
        """获取卡池中的物品"""
        return self.db.fetch_all(
            "SELECT item_type, item_template_id FROM gacha_pool_items WHERE pool_id = ?",
            (pool_id,)
        )

    def get_items_by_rarity(self, item_type: str, item_ids: List[int], rarity: int) -> List[Dict[str, Any]]:
        """根据物品类型和稀有度获取物品"""
        if not item_ids:
            return []

        if item_type == "rod":
            query = "SELECT id FROM rod_templates WHERE id IN ({}) AND rarity = ?".format(
                ','.join('?' * len(item_ids))
            )
            params = item_ids + [rarity]
        elif item_type == "accessory":
            query = "SELECT id FROM accessory_templates WHERE id IN ({}) AND rarity = ?".format(
                ','.join('?' * len(item_ids))
            )
            params = item_ids + [rarity]
        elif item_type == "bait":
            query = "SELECT id FROM bait_templates WHERE id IN ({}) AND rarity = ?".format(
                ','.join('?' * len(item_ids))
            )
            params = item_ids + [rarity]
        else:
            return []

        return self.db.fetch_all(query, params)

    def add_rod_to_user(self, user_id: str, rod_template_id: int) -> bool:
        """添加鱼竿到用户背包"""
        try:
            now = int(time.time())
            self.db.execute_query(
                """INSERT INTO user_rod_instances
                   (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                   VALUES (?, ?, 1, 0, FALSE, ?, 100)""",
                (user_id, rod_template_id, now)
            )
            return True
        except Exception as e:
            print(f"添加鱼竿到用户背包时出错: {e}")
            return False

    def add_accessory_to_user(self, user_id: str, accessory_template_id: int) -> bool:
        """添加饰品到用户背包"""
        try:
            now = int(time.time())
            self.db.execute_query(
                """INSERT INTO user_accessory_instances
                   (user_id, accessory_template_id, is_equipped, acquired_at)
                   VALUES (?, ?, FALSE, ?)""",
                (user_id, accessory_template_id, now)
            )
            return True
        except Exception as e:
            print(f"添加饰品到用户背包时出错: {e}")
            return False

    def add_bait_to_user(self, user_id: str, bait_template_id: int) -> bool:
        """添加鱼饵到用户背包"""
        try:
            # 检查用户是否已有该鱼饵
            existing = self.db.fetch_one(
                """SELECT id, quantity FROM user_bait_inventory
                   WHERE user_id = ? AND bait_template_id = ?""",
                (user_id, bait_template_id)
            )

            if existing:
                # 增加现有鱼饵数量
                self.db.execute_query(
                    "UPDATE user_bait_inventory SET quantity = quantity + 1 WHERE id = ?",
                    (existing['id'],)
                )
            else:
                # 添加新鱼饵
                self.db.execute_query(
                    """INSERT INTO user_bait_inventory
                       (user_id, bait_template_id, quantity)
                       VALUES (?, ?, 1)""",
                    (user_id, bait_template_id)
                )
            return True
        except Exception as e:
            print(f"添加鱼饵到用户背包时出错: {e}")
            return False

    def get_user_gold(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户金币"""
        return self.db.fetch_one("SELECT gold FROM users WHERE user_id = ?", (user_id,))

    def deduct_user_gold(self, user_id: str, amount: int) -> bool:
        """扣除用户金币"""
        try:
            self.db.execute_query(
                "UPDATE users SET gold = gold - ? WHERE user_id = ?",
                (amount, user_id)
            )
            return True
        except Exception as e:
            print(f"扣除用户金币时出错: {e}")
            return False

    def add_gacha_log(self, user_id: str, item_type: str, item_template_id: int, rarity: int) -> bool:
        """添加抽卡日志"""
        try:
            self.db.execute_query(
                """INSERT INTO gacha_logs
                   (user_id, item_type, item_template_id, rarity, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, item_type, item_template_id, rarity, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"添加抽卡日志时出错: {e}")
            return False

    def get_item_name(self, item_type: str, item_template_id: int) -> Optional[str]:
        """获取物品名称"""
        if item_type == "rod":
            result = self.db.fetch_one("SELECT name FROM rod_templates WHERE id = ?", (item_template_id,))
        elif item_type == "accessory":
            result = self.db.fetch_one("SELECT name FROM accessory_templates WHERE id = ?", (item_template_id,))
        elif item_type == "bait":
            result = self.db.fetch_one("SELECT name FROM bait_templates WHERE id = ?", (item_template_id,))
        else:
            return None

        return result['name'] if result else None

    def get_gacha_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的抽卡记录"""
        return self.db.fetch_all(
            """SELECT gl.*, rt.name as item_name, rt.rarity as item_rarity
               FROM gacha_logs gl
               LEFT JOIN rod_templates rt ON gl.item_template_id = rt.id AND gl.item_type = 'rod'
               WHERE gl.user_id = ?
               ORDER BY gl.timestamp DESC
               LIMIT ?""",
            (user_id, limit)
        )

    def get_accessory_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的饰品抽卡记录"""
        return self.db.fetch_all(
            """SELECT gl.*, at.name as item_name, at.rarity as item_rarity
               FROM gacha_logs gl
               LEFT JOIN accessory_templates at ON gl.item_template_id = at.id AND gl.item_type = 'accessory'
               WHERE gl.user_id = ? AND gl.item_type = 'accessory'
               ORDER BY gl.timestamp DESC
               LIMIT ?""",
            (user_id, limit)
        )

    def get_bait_logs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户的鱼饵抽卡记录"""
        return self.db.fetch_all(
            """SELECT gl.*, bt.name as item_name, bt.rarity as item_rarity
               FROM gacha_logs gl
               LEFT JOIN bait_templates bt ON gl.item_template_id = bt.id AND gl.item_type = 'bait'
               WHERE gl.user_id = ? AND gl.item_type = 'bait'
               ORDER BY gl.timestamp DESC
               LIMIT ?""",
            (user_id, limit)
        )