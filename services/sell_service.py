from typing import List, Optional
from astrbot.core.platform import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.equipment import Rod, Bait
from ..models.database import DatabaseManager
import time

class SellService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def sell_all_command(self, event: AstrMessageEvent):
        """全部卖出鱼类命令"""
        user_id = event.get_sender_id()

        # 获取用户鱼类库存
        fish_inventory = self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )

        if not fish_inventory:
            yield event.plain_result("您的鱼塘是空的，没有鱼可以卖出！")
            return

        # 计算总价值
        total_value = sum(fish['value'] for fish in fish_inventory)

        # 删除所有鱼类并增加金币
        self.db.execute_query(
            "DELETE FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )

        # 增加用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (total_value, user_id)
        )

        yield event.plain_result(f"成功卖出所有鱼类！\n获得金币: {total_value}枚")

    async def sell_keep_one_command(self, event: AstrMessageEvent):
        """保留一条卖出其他鱼类命令"""
        user_id = event.get_sender_id()

        # 获取用户鱼类库存
        fish_inventory = self.db.fetch_all(
            "SELECT * FROM user_fish_inventory WHERE user_id = ? ORDER BY value DESC",
            (user_id,)
        )

        if not fish_inventory:
            yield event.plain_result("您的鱼塘是空的，没有鱼可以卖出！")
            return

        if len(fish_inventory) <= 1:
            yield event.plain_result("您的鱼塘中只有一条鱼或没有鱼，无法执行保留一条卖出的操作！")
            return

        # 保留价值最高的鱼，卖出其他鱼
        fish_to_sell = fish_inventory[1:]  # 除了第一条鱼之外的所有鱼
        total_value = sum(fish['value'] for fish in fish_to_sell)

        # 删除要卖出的鱼
        fish_ids = [fish['id'] for fish in fish_to_sell]
        placeholders = ','.join('?' * len(fish_ids))
        self.db.execute_query(
            f"DELETE FROM user_fish_inventory WHERE id IN ({placeholders})",
            fish_ids
        )

        # 增加用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (total_value, user_id)
        )

        yield event.plain_result(f"成功卖出 {len(fish_to_sell)} 条鱼！\n保留了价值最高的鱼\n获得金币: {total_value}枚")

    async def sell_by_rarity_command(self, event: AstrMessageEvent, rarity: int):
        """按稀有度卖出鱼类命令"""
        user_id = event.get_sender_id()

        # 验证稀有度参数
        if rarity < 1 or rarity > 5:
            yield event.plain_result("稀有度参数无效，请输入1-5之间的数字！")
            return

        # 获取指定稀有度的鱼类
        fish_inventory = self.db.fetch_all(
            """SELECT ufi.*, ft.name as fish_name
               FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ? AND ft.rarity = ?""",
            (user_id, rarity)
        )

        if not fish_inventory:
            yield event.plain_result(f"您的鱼塘中没有 {rarity} 星鱼类！")
            return

        # 计算总价值
        total_value = sum(fish['value'] for fish in fish_inventory)

        # 删除指定稀有度的鱼
        fish_ids = [fish['id'] for fish in fish_inventory]
        placeholders = ','.join('?' * len(fish_ids))
        self.db.execute_query(
            f"DELETE FROM user_fish_inventory WHERE id IN ({placeholders})",
            fish_ids
        )

        # 增加用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (total_value, user_id)
        )

        yield event.plain_result(f"成功卖出所有 {rarity} 星鱼类！\n共卖出 {len(fish_inventory)} 条鱼\n获得金币: {total_value}枚")

    async def sell_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """出售鱼竿命令"""
        user_id = event.get_sender_id()

        # 检查鱼竿是否存在且属于用户
        rod = self.db.fetch_one(
            """SELECT uri.*, rt.name as rod_name, rt.rarity as rod_rarity
               FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.id = ? AND uri.user_id = ?""",
            (rod_id, user_id)
        )

        if not rod:
            yield event.plain_result("找不到指定的鱼竿或该鱼竿不属于您！")
            return

        # 检查鱼竿是否正在使用
        if rod['is_equipped']:
            yield event.plain_result("不能出售正在使用的鱼竿，请先卸下该鱼竿！")
            return

        # 计算出售价格 (根据稀有度确定基础价格)
        base_price = 100 * rod['rod_rarity']  # 1星100金币，2星200金币，以此类推
        sell_price = max(10, base_price // 2)  # 最低10金币

        # 删除鱼竿
        self.db.execute_query(
            "DELETE FROM user_rod_instances WHERE id = ?",
            (rod_id,)
        )

        # 增加用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (sell_price, user_id)
        )

        yield event.plain_result(f"成功出售鱼竿 [{rod['rod_name']}]！\n获得金币: {sell_price}枚")

    async def sell_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """出售鱼饵命令"""
        user_id = event.get_sender_id()

        # 检查鱼饵是否存在且属于用户
        bait = self.db.fetch_one(
            """SELECT ubi.*, bt.name as bait_name, bt.rarity as bait_rarity
               FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.id = ? AND ubi.user_id = ?""",
            (bait_id, user_id)
        )

        if not bait:
            yield event.plain_result("找不到指定的鱼饵或该鱼饵不属于您！")
            return

        # 检查鱼饵数量
        if bait['quantity'] <= 0:
            yield event.plain_result("该鱼饵数量为0，无法出售！")
            return

        # 计算出售价格 (根据稀有度和数量确定价格)
        base_price = 50 * bait['bait_rarity']  # 1星50金币，2星100金币，以此类推
        sell_price = max(5, base_price // 2) * bait['quantity']  # 最低5金币每个

        # 删除鱼饵
        self.db.execute_query(
            "DELETE FROM user_bait_inventory WHERE id = ?",
            (bait_id,)
        )

        # 增加用户金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (sell_price, user_id)
        )

        yield event.plain_result(f"成功出售鱼饵 [{bait['bait_name']}] x{bait['quantity']}！\n获得金币: {sell_price}枚")