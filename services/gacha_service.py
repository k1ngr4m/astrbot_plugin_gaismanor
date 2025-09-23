from typing import List, Optional
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
from ..dao.gacha_dao import GachaDAO
import random
import time

class GachaService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.gacha_dao = GachaDAO(db_manager)
        # 从数据库加载卡池数据
        self.gacha_pools = self._load_gacha_pools()

    def _load_gacha_pools(self):
        """从数据库加载卡池数据"""
        pools = {}

        # 获取所有卡池
        pool_records = self.gacha_dao.get_enabled_gacha_pools()

        for pool_record in pool_records:
            pool_id = pool_record['id']

            # 获取卡池稀有度权重
            rarity_weights = {}
            weights = self.gacha_dao.get_gacha_pool_rarity_weights(pool_id)
            for weight in weights:
                rarity_weights[weight['rarity']] = weight['weight']

            # 获取卡池中的物品
            items = self.gacha_dao.get_gacha_pool_items(pool_id)

            # 按类型分组物品ID
            items_dict = {"rod": [], "accessory": [], "bait": []}
            for item in items:
                item_type = item['item_type']
                if item_type in items_dict:
                    items_dict[item_type].append(item['item_template_id'])

            pools[pool_id] = {
                "name": pool_record['name'],
                "description": pool_record['description'],
                "items": items_dict,
                "rarity_weights": rarity_weights
            }

        return pools

    def get_rarity(self, pool_id: int) -> int:
        """根据权重随机获取稀有度"""
        if pool_id not in self.gacha_pools:
            # 如果卡池不存在，使用默认权重
            rarity_weights = {
                1: 50,  # 50% 概率获得1星物品
                2: 30,  # 30% 概率获得2星物品
                3: 15,  # 15% 概率获得3星物品
                4: 4,   # 4% 概率获得4星物品
                5: 1    # 1% 概率获得5星物品
            }
        else:
            rarity_weights = self.gacha_pools[pool_id]["rarity_weights"]

        rarities = list(rarity_weights.keys())
        weights = list(rarity_weights.values())
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
        items = self.gacha_dao.get_items_by_rarity(item_type, item_ids, rarity)

        if not items:
            return None

        # 随机选择一个物品
        return random.choice(items)['id']

    def add_item_to_user(self, user_id: str, item_type: str, item_template_id: int) -> bool:
        """将抽到的物品添加到用户背包"""
        if item_type == "rod":
            return self.gacha_dao.add_rod_to_user(user_id, item_template_id)
        elif item_type == "accessory":
            return self.gacha_dao.add_accessory_to_user(user_id, item_template_id)
        elif item_type == "bait":
            return self.gacha_dao.add_bait_to_user(user_id, item_template_id)
        else:
            return False

    async def gacha_command(self, event: AstrMessageEvent, pool_id: int):
        """单次抽卡命令"""
        user_id = event.get_sender_id()

        # 检查卡池是否存在
        if pool_id not in self.gacha_pools:
            yield event.plain_result("无效的卡池ID！请使用 1-3 之间的数字。")
            return

        # 检查用户金币 (假设单次抽卡消耗100金币)
        user = self.gacha_dao.get_user_gold(user_id)
        if not user or user['gold'] < 100:
            yield event.plain_result("金币不足！单次抽卡需要100金币。")
            return

        # 扣除金币
        if not self.gacha_dao.deduct_user_gold(user_id, 100):
            yield event.plain_result("扣除金币失败，请稍后再试。")
            return

        # 执行抽卡
        pool = self.gacha_pools[pool_id]
        rarity = self.get_rarity(pool_id)

        # 随机选择物品类型
        item_types = ["rod", "accessory", "bait"]
        item_type = random.choice(item_types)

        # 获取物品
        item_template_id = self.get_random_item(pool_id, item_type, rarity)
        if not item_template_id:
            yield event.plain_result("抽卡失败，请稍后再试。")
            return

        # 获取物品名称
        item_name = self.gacha_dao.get_item_name(item_type, item_template_id)
        if not item_name:
            yield event.plain_result("抽卡失败，请稍后再试。")
            return

        # 添加物品到用户背包
        if not self.add_item_to_user(user_id, item_type, item_template_id):
            yield event.plain_result("抽卡成功，但添加物品到背包时出错。")
            return

        # 记录抽卡日志
        if not self.gacha_dao.add_gacha_log(user_id, item_type, item_template_id, rarity):
            yield event.plain_result("抽卡成功，但记录日志时出错。")
            return

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
        user = self.gacha_dao.get_user_gold(user_id)
        if not user or user['gold'] < 900:
            yield event.plain_result("金币不足！十连抽卡需要900金币。")
            return

        # 扣除金币
        if not self.gacha_dao.deduct_user_gold(user_id, 900):
            yield event.plain_result("扣除金币失败，请稍后再试。")
            return

        # 执行十连抽卡
        pool = self.gacha_pools[pool_id]
        results = []

        for i in range(10):
            rarity = self.get_rarity(pool_id)

            # 随机选择物品类型
            item_types = ["rod", "accessory", "bait"]
            item_type = random.choice(item_types)

            # 获取物品
            item_template_id = self.get_random_item(pool_id, item_type, rarity)
            if not item_template_id:
                continue

            # 获取物品名称
            item_name = self.gacha_dao.get_item_name(item_type, item_template_id)
            if not item_name:
                continue

            # 添加物品到用户背包
            if not self.add_item_to_user(user_id, item_type, item_template_id):
                continue

            # 记录抽卡日志
            if not self.gacha_dao.add_gacha_log(user_id, item_type, item_template_id, rarity):
                continue

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
        pool_info = f"=== {pool['name']} ===\n\n"
        pool_info += f"{pool['description']}\n\n\n"

        pool_info += "\n\n包含物品:\n\n"

        # 显示鱼竿
        pool_info += "鱼竿:\n\n"
        for rod_id in pool["items"]["rod"]:
            rod_name = self.gacha_dao.get_item_name("rod", rod_id)
            # 由于GachaDAO中没有直接获取物品稀有度的方法，我们仍然需要查询数据库
            rod = self.db.fetch_one("SELECT name, rarity FROM rod_templates WHERE id = ?", (rod_id,))
            if rod and rod_name:
                stars = "★" * rod['rarity']
                pool_info += f"  · {rod_name} ({stars})\n\n"

        # 显示饰品
        pool_info += "饰品:\n\n"
        for accessory_id in pool["items"]["accessory"]:
            accessory_name = self.gacha_dao.get_item_name("accessory", accessory_id)
            # 由于GachaDAO中没有直接获取物品稀有度的方法，我们仍然需要查询数据库
            accessory = self.db.fetch_one("SELECT name, rarity FROM accessory_templates WHERE id = ?", (accessory_id,))
            if accessory and accessory_name:
                stars = "★" * accessory['rarity']
                pool_info += f"  · {accessory_name} ({stars})\n\n"

        # 显示鱼饵
        pool_info += "鱼饵:\n\n"
        for bait_id in pool["items"]["bait"]:
            bait_name = self.gacha_dao.get_item_name("bait", bait_id)
            # 由于GachaDAO中没有直接获取物品稀有度的方法，我们仍然需要查询数据库
            bait = self.db.fetch_one("SELECT name, rarity FROM bait_templates WHERE id = ?", (bait_id,))
            if bait and bait_name:
                stars = "★" * bait['rarity']
                pool_info += f"  · {bait_name} ({stars})\n\n"

        yield event.plain_result(pool_info)

    async def gacha_log_command(self, event: AstrMessageEvent):
        """查看抽卡记录命令"""
        user_id = event.get_sender_id()

        # 获取用户的抽卡记录
        logs = self.gacha_dao.get_gacha_logs(user_id, 20)

        # 如果没有抽卡记录
        if not logs:
            yield event.plain_result("您还没有抽卡记录。")
            return

        # 获取其他类型的物品名称
        accessory_logs = self.gacha_dao.get_accessory_logs(user_id, 20)

        bait_logs = self.gacha_dao.get_bait_logs(user_id, 20)

        # 合并所有记录并按时间排序
        all_logs = list(logs) + list(accessory_logs) + list(bait_logs)
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        all_logs = all_logs[:20]  # 只取最新的20条记录

        if not all_logs:
            yield event.plain_result("您还没有抽卡记录。")
            return

        # 构造返回消息
        result_msg = "=== 抽卡记录 (最近20条) ===\n\n"

        for log in all_logs:
            # 获取物品名称和稀有度
            item_name = log['item_name']
            item_rarity = log['item_rarity']

            if not item_name or item_rarity is None:
                # 如果物品信息缺失，尝试从对应的表中获取
                if log['item_type'] == 'rod':
                    item = self.db.fetch_one("SELECT name, rarity FROM rod_templates WHERE id = ?", (log['item_template_id'],))
                elif log['item_type'] == 'accessory':
                    item = self.db.fetch_one("SELECT name, rarity FROM accessory_templates WHERE id = ?", (log['item_template_id'],))
                elif log['item_type'] == 'bait':
                    item = self.db.fetch_one("SELECT name, rarity FROM bait_templates WHERE id = ?", (log['item_template_id'],))
                else:
                    item = None

                if item:
                    item_name = item['name']
                    item_rarity = item['rarity']
                else:
                    item_name = "未知物品"
                    item_rarity = 1

            # 格式化时间
            import datetime
            timestamp = datetime.datetime.fromtimestamp(log['timestamp'])
            time_str = timestamp.strftime("%m-%d %H:%M")

            # 物品类型中文
            type_map = {
                'rod': '鱼竿',
                'accessory': '饰品',
                'bait': '鱼饵'
            }
            item_type = type_map.get(log['item_type'], log['item_type'])

            # 稀有度星星
            rarity_stars = "★" * item_rarity

            result_msg += f"{time_str} 抽到 {item_type} {rarity_stars}\n"
            result_msg += f"  · {item_name}\n\n"

        yield event.plain_result(result_msg)