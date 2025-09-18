from typing import List, Optional
from astrbot.core.platform import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
import random
import time

class GachaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # 定义抽卡概率 (星级: 概率)
        self.rarity_weights = {
            1: 50,  # 50% 概率获得1星物品
            2: 30,  # 30% 概率获得2星物品
            3: 15,  # 15% 概率获得3星物品
            4: 4,   # 4% 概率获得4星物品
            5: 1    # 1% 概率获得5星物品
        }

        # 定义卡池 (不同类型物品的抽卡池)
        self.gacha_pools = {
            1: {  # 普通卡池
                "name": "普通卡池",
                "description": "包含各种基础装备和物品",
                "items": {
                    "rod": [1, 2, 3],      # 1-3星鱼竿ID
                    "accessory": [1, 2],   # 1-2星饰品ID
                    "bait": [1, 2, 3]      # 1-3星鱼饵ID
                }
            },
            2: {  # 高级卡池
                "name": "高级卡池",
                "description": "包含稀有装备和物品",
                "items": {
                    "rod": [2, 3, 4],      # 2-4星鱼竿ID
                    "accessory": [2, 3],   # 2-3星饰品ID
                    "bait": [2, 3, 4]      # 2-4星鱼饵ID
                }
            },
            3: {  # 限定卡池
                "name": "限定卡池",
                "description": "包含限定稀有装备",
                "items": {
                    "rod": [3, 4, 5],      # 3-5星鱼竿ID
                    "accessory": [3, 4],   # 3-4星饰品ID
                    "bait": [3, 4, 5]      # 3-5星鱼饵ID
                }
            }
        }

    def get_rarity(self) -> int:
        """根据权重随机获取稀有度"""
        rarities = list(self.rarity_weights.keys())
        weights = list(self.rarity_weights.values())
        return random.choices(rarities, weights=weights)[0]

    def get_random_item(self, pool_id: int, item_type: str, rarity: int) -> Optional[int]:
        """从指定卡池中随机获取指定类型和稀有度的物品"""
        if pool_id not in self.gacha_pools:
            return None

        pool = self.gacha_pools[pool_id]
        if item_type not in pool["items"]:
            return None

        # 获取指定稀有度的物品ID列表
        item_ids = pool["items"][item_type]

        # 从数据库中获取对应稀有度的物品
        if item_type == "rod":
            items = self.db.fetch_all(
                "SELECT id FROM rod_templates WHERE id IN ({}) AND rarity = ?".format(
                    ','.join('?' * len(item_ids))
                ),
                item_ids + [rarity]
            )
        elif item_type == "accessory":
            items = self.db.fetch_all(
                "SELECT id FROM accessory_templates WHERE id IN ({}) AND rarity = ?".format(
                    ','.join('?' * len(item_ids))
                ),
                item_ids + [rarity]
            )
        elif item_type == "bait":
            items = self.db.fetch_all(
                "SELECT id FROM bait_templates WHERE id IN ({}) AND rarity = ?".format(
                    ','.join('?' * len(item_ids))
                ),
                item_ids + [rarity]
            )
        else:
            return None

        if not items:
            return None

        # 随机选择一个物品
        return random.choice(items)['id']

    def add_item_to_user(self, user_id: str, item_type: str, item_template_id: int) -> bool:
        """将抽到的物品添加到用户背包"""
        try:
            now = int(time.time())

            if item_type == "rod":
                # 添加鱼竿到用户背包
                self.db.execute_query(
                    """INSERT INTO user_rod_instances
                       (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                       VALUES (?, ?, 1, 0, FALSE, ?, 100)""",
                    (user_id, item_template_id, now)
                )
            elif item_type == "accessory":
                # 添加饰品到用户背包
                self.db.execute_query(
                    """INSERT INTO user_accessory_instances
                       (user_id, accessory_template_id, is_equipped, acquired_at)
                       VALUES (?, ?, FALSE, ?)""",
                    (user_id, item_template_id, now)
                )
            elif item_type == "bait":
                # 检查用户是否已有该鱼饵
                existing = self.db.fetch_one(
                    """SELECT id, quantity FROM user_bait_inventory
                       WHERE user_id = ? AND bait_template_id = ?""",
                    (user_id, item_template_id)
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
                        (user_id, item_template_id)
                    )

            return True
        except Exception as e:
            print(f"添加物品到用户背包时出错: {e}")
            return False

    async def gacha_command(self, event: AstrMessageEvent, pool_id: int):
        """单次抽卡命令"""
        user_id = event.get_sender_id()

        # 检查卡池是否存在
        if pool_id not in self.gacha_pools:
            yield event.plain_result("无效的卡池ID！请使用 1-3 之间的数字。")
            return

        # 检查用户金币 (假设单次抽卡消耗100金币)
        user = self.db.fetch_one("SELECT gold FROM users WHERE user_id = ?", (user_id,))
        if not user or user['gold'] < 100:
            yield event.plain_result("金币不足！单次抽卡需要100金币。")
            return

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - 100 WHERE user_id = ?",
            (user_id,)
        )

        # 执行抽卡
        pool = self.gacha_pools[pool_id]
        rarity = self.get_rarity()

        # 随机选择物品类型
        item_types = ["rod", "accessory", "bait"]
        item_type = random.choice(item_types)

        # 获取物品
        item_template_id = self.get_random_item(pool_id, item_type, rarity)
        if not item_template_id:
            yield event.plain_result("抽卡失败，请稍后再试。")
            return

        # 获取物品名称
        if item_type == "rod":
            item = self.db.fetch_one("SELECT name FROM rod_templates WHERE id = ?", (item_template_id,))
        elif item_type == "accessory":
            item = self.db.fetch_one("SELECT name FROM accessory_templates WHERE id = ?", (item_template_id,))
        elif item_type == "bait":
            item = self.db.fetch_one("SELECT name FROM bait_templates WHERE id = ?", (item_template_id,))
        else:
            item = None

        if not item:
            yield event.plain_result("抽卡失败，请稍后再试。")
            return

        item_name = item['name']

        # 添加物品到用户背包
        if not self.add_item_to_user(user_id, item_type, item_template_id):
            yield event.plain_result("抽卡成功，但添加物品到背包时出错。")
            return

        # 记录抽卡日志
        self.db.execute_query(
            """INSERT INTO gacha_logs
               (user_id, item_type, item_template_id, rarity, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, item_type, item_template_id, rarity, int(time.time()))
        )

        # 构造返回消息
        rarity_stars = "★" * rarity
        result_msg = f"🎉 抽卡成功！\n"
        result_msg += f"卡池: {pool['name']}\n"
        result_msg += f"获得物品: {item_name}\n"
        result_msg += f"稀有度: {rarity_stars} ({rarity}星)\n"
        result_msg += f"剩余金币: {user['gold'] - 100}枚"

        yield event.plain_result(result_msg)

    async def ten_gacha_command(self, event: AstrMessageEvent, pool_id: int):
        """十连抽卡命令"""
        user_id = event.get_sender_id()

        # 检查卡池是否存在
        if pool_id not in self.gacha_pools:
            yield event.plain_result("无效的卡池ID！请使用 1-3 之间的数字。")
            return

        # 检查用户金币 (十连抽卡消耗900金币，相当于9折)
        user = self.db.fetch_one("SELECT gold FROM users WHERE user_id = ?", (user_id,))
        if not user or user['gold'] < 900:
            yield event.plain_result("金币不足！十连抽卡需要900金币。")
            return

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - 900 WHERE user_id = ?",
            (user_id,)
        )

        # 执行十连抽卡
        pool = self.gacha_pools[pool_id]
        results = []

        for i in range(10):
            rarity = self.get_rarity()

            # 随机选择物品类型
            item_types = ["rod", "accessory", "bait"]
            item_type = random.choice(item_types)

            # 获取物品
            item_template_id = self.get_random_item(pool_id, item_type, rarity)
            if not item_template_id:
                continue

            # 获取物品名称
            if item_type == "rod":
                item = self.db.fetch_one("SELECT name FROM rod_templates WHERE id = ?", (item_template_id,))
            elif item_type == "accessory":
                item = self.db.fetch_one("SELECT name FROM accessory_templates WHERE id = ?", (item_template_id,))
            elif item_type == "bait":
                item = self.db.fetch_one("SELECT name FROM bait_templates WHERE id = ?", (item_template_id,))
            else:
                item = None

            if not item:
                continue

            item_name = item['name']

            # 添加物品到用户背包
            if not self.add_item_to_user(user_id, item_type, item_template_id):
                continue

            # 记录抽卡日志
            self.db.execute_query(
                """INSERT INTO gacha_logs
                   (user_id, item_type, item_template_id, rarity, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, item_type, item_template_id, rarity, int(time.time()))
            )

            results.append({
                "name": item_name,
                "rarity": rarity,
                "type": item_type
            })

        # 构造返回消息
        result_msg = f"🎊 十连抽卡结果 (卡池: {pool['name']})\n"
        result_msg += "=" * 30 + "\n"

        # 按稀有度分组显示
        for rarity in range(5, 0, -1):  # 从5星到1星
            rarity_results = [r for r in results if r["rarity"] == rarity]
            if rarity_results:
                rarity_stars = "★" * rarity
                result_msg += f"{rarity_stars} ({rarity}星): {len(rarity_results)}个\n"
                for item in rarity_results:
                    result_msg += f"  · {item['name']} ({item['type']})\n"

        result_msg += "=" * 30 + "\n"
        result_msg += f"剩余金币: {user['gold'] - 900}枚"

        yield event.plain_result(result_msg)

    async def view_gacha_pool_command(self, event: AstrMessageEvent, pool_id: int):
        """查看卡池命令"""
        if pool_id not in self.gacha_pools:
            yield event.plain_result("无效的卡池ID！请使用 1-3 之间的数字。")
            return

        pool = self.gacha_pools[pool_id]

        # 构造卡池信息
        pool_info = f"=== {pool['name']} ===\n"
        pool_info += f"{pool['description']}\n\n"
        pool_info += "稀有度概率:\n"

        total_weight = sum(self.rarity_weights.values())
        for rarity in range(5, 0, -1):  # 从5星到1星
            probability = (self.rarity_weights[rarity] / total_weight) * 100
            stars = "★" * rarity
            pool_info += f"{stars} ({rarity}星): {probability:.1f}%\n"

        pool_info += "\n包含物品:\n"

        # 显示鱼竿
        pool_info += "鱼竿:\n"
        for rod_id in pool["items"]["rod"]:
            rod = self.db.fetch_one("SELECT name, rarity FROM rod_templates WHERE id = ?", (rod_id,))
            if rod:
                stars = "★" * rod['rarity']
                pool_info += f"  · {rod['name']} ({stars})\n"

        # 显示饰品
        pool_info += "饰品:\n"
        for accessory_id in pool["items"]["accessory"]:
            accessory = self.db.fetch_one("SELECT name, rarity FROM accessory_templates WHERE id = ?", (accessory_id,))
            if accessory:
                stars = "★" * accessory['rarity']
                pool_info += f"  · {accessory['name']} ({stars})\n"

        # 显示鱼饵
        pool_info += "鱼饵:\n"
        for bait_id in pool["items"]["bait"]:
            bait = self.db.fetch_one("SELECT name, rarity FROM bait_templates WHERE id = ?", (bait_id,))
            if bait:
                stars = "★" * bait['rarity']
                pool_info += f"  · {bait['name']} ({stars})\n"

        yield event.plain_result(pool_info)