from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager
import random
import time

class GachaCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

        # 抽卡费用
        self.single_gacha_cost = 1000
        self.ten_gacha_cost = 10000

    async def gacha_command(self, event: AstrMessageEvent, pool_id: int):
        """单次抽卡命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查金币是否足够
        if user.gold < self.single_gacha_cost:
            yield event.plain_result(f"金币不足，单次抽卡需要 {self.single_gacha_cost} 金币")
            return

        # 执行抽卡
        result = self._perform_gacha(pool_id, 1)

        if not result:
            yield event.plain_result("抽卡失败，请检查卡池ID是否正确")
            return

        # 扣除金币
        user.gold -= self.single_gacha_cost
        self.user_service.update_user(user)

        # 添加抽卡结果到用户背包
        item_type, item_template_id, rarity = result
        self._add_gacha_item_to_user(user_id, item_type, item_template_id)

        # 记录抽卡日志
        self.db_manager.execute_query(
            """INSERT INTO gacha_logs
               (user_id, item_type, item_template_id, rarity, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, item_type, item_template_id, rarity, int(time.time()))
        )

        # 获取物品名称
        item_name = self._get_item_name(item_type, item_template_id)
        rarity_stars = "★" * rarity

        yield event.plain_result(f"抽卡结果: {item_name} {rarity_stars}")

    async def ten_gacha_command(self, event: AstrMessageEvent, pool_id: int):
        """十连抽卡命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查金币是否足够
        if user.gold < self.ten_gacha_cost:
            yield event.plain_result(f"金币不足，十连抽卡需要 {self.ten_gacha_cost} 金币")
            return

        # 执行十连抽卡
        results = []
        for _ in range(10):
            result = self._perform_gacha(pool_id, 1)
            if result:
                results.append(result)

        if not results:
            yield event.plain_result("抽卡失败，请检查卡池ID是否正确")
            return

        # 扣除金币
        user.gold -= self.ten_gacha_cost
        self.user_service.update_user(user)

        # 添加抽卡结果到用户背包
        item_details = []
        for item_type, item_template_id, rarity in results:
            self._add_gacha_item_to_user(user_id, item_type, item_template_id)

            # 记录抽卡日志
            self.db_manager.execute_query(
                """INSERT INTO gacha_logs
                   (user_id, item_type, item_template_id, rarity, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, item_type, item_template_id, rarity, int(time.time()))
            )

            # 获取物品名称
            item_name = self._get_item_name(item_type, item_template_id)
            rarity_stars = "★" * rarity
            item_details.append(f"{item_name} {rarity_stars}")

        yield event.plain_result(f"十连抽卡结果:\n" + "\n".join(item_details))

    async def view_gacha_pool_command(self, event: AstrMessageEvent, pool_id: int):
        """查看卡池详细信息命令"""
        # 获取卡池信息
        pool = self.db_manager.fetch_one(
            "SELECT * FROM gacha_pools WHERE id = ?",
            (pool_id,)
        )

        if not pool:
            yield event.plain_result("卡池不存在，请检查ID是否正确")
            return

        # 获取卡池物品概率
        pool_items = self.db_manager.fetch_all(
            "SELECT * FROM gacha_pool_items WHERE pool_id = ?",
            (pool_id,)
        )

        if not pool_items:
            yield event.plain_result("该卡池暂无物品")
            return

        # 构建卡池信息
        pool_info = f"=== 卡池: {pool['name']} ===\n"
        pool_info += f"描述: {pool['description']}\n\n"
        pool_info += "物品概率:\n"

        for item in pool_items:
            item_type = item['item_type']
            item_template_id = item['item_template_id']
            probability = item['probability']

            # 获取物品名称
            item_name = self._get_item_name(item_type, item_template_id)
            rarity = item['rarity']
            rarity_stars = "★" * rarity

            pool_info += f"  {item_name} {rarity_stars} - 概率: {probability:.2f}%\n"

        yield event.plain_result(pool_info)

    def _perform_gacha(self, pool_id: int, user_rarity_bonus: int = 0):
        """执行抽卡逻辑"""
        # 获取卡池物品
        pool_items = self.db_manager.fetch_all(
            "SELECT * FROM gacha_pool_items WHERE pool_id = ?",
            (pool_id,)
        )

        if not pool_items:
            return None

        # 根据概率选择物品
        probabilities = [item['probability'] for item in pool_items]
        selected_item = random.choices(pool_items, probabilities)[0]

        return (
            selected_item['item_type'],
            selected_item['item_template_id'],
            selected_item['rarity']
        )

    def _add_gacha_item_to_user(self, user_id: str, item_type: str, item_template_id: int):
        """将抽卡获得的物品添加到用户背包"""
        if item_type == "rod":
            # 添加鱼竿
            self.db_manager.execute_query(
                """INSERT INTO user_rod_instances
                   (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                   VALUES (?, ?, 1, 0, FALSE, ?, 100)""",
                (user_id, item_template_id, int(time.time()))
            )
        elif item_type == "accessory":
            # 添加饰品
            self.db_manager.execute_query(
                """INSERT INTO user_accessory_instances
                   (user_id, accessory_template_id, is_equipped, acquired_at)
                   VALUES (?, ?, FALSE, ?)""",
                (user_id, item_template_id, int(time.time()))
            )
        elif item_type == "bait":
            # 添加鱼饵
            # 检查是否已有该鱼饵
            existing_bait = self.db_manager.fetch_one(
                "SELECT id, quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                (user_id, item_template_id)
            )
            if existing_bait:
                # 增加数量
                self.db_manager.execute_query(
                    "UPDATE user_bait_inventory SET quantity = quantity + 1 WHERE id = ?",
                    (existing_bait['id'],)
                )
            else:
                # 添加新鱼饵
                self.db_manager.execute_query(
                    """INSERT INTO user_bait_inventory
                       (user_id, bait_template_id, quantity)
                       VALUES (?, ?, 1)""",
                    (user_id, item_template_id)
                )

    def _get_item_name(self, item_type: str, item_template_id: int) -> str:
        """获取物品名称"""
        if item_type == "rod":
            item = self.db_manager.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (item_template_id,)
            )
            return item['name'] if item else "未知鱼竿"
        elif item_type == "accessory":
            item = self.db_manager.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (item_template_id,)
            )
            return item['name'] if item else "未知饰品"
        elif item_type == "bait":
            item = self.db_manager.fetch_one(
                "SELECT name FROM bait_templates WHERE id = ?",
                (item_template_id,)
            )
            return item['name'] if item else "未知鱼饵"
        return "未知物品"