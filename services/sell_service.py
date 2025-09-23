from typing import List, Optional
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.fishing import FishTemplate
from ..models.equipment import Rod, Bait
from ..models.database import DatabaseManager
from ..dao.sell_dao import SellDAO
from ..dao.user_dao import UserDAO
import time

class SellService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.sell_dao = SellDAO(db_manager)
        self.user_dao = UserDAO(db_manager)

    async def sell_all_command(self, event: AstrMessageEvent):
        """全部卖出鱼类命令"""
        user_id = event.get_sender_id()

        # 获取用户鱼类库存
        fish_inventory = self.sell_dao.get_user_fish_inventory(user_id)

        if not fish_inventory:
            yield event.plain_result("您的鱼塘是空的，没有鱼可以卖出！")
            return

        # 计算总价值
        total_value = sum(fish['value'] for fish in fish_inventory)

        # 删除所有鱼类并增加金币
        self.sell_dao.delete_all_user_fish(user_id)

        # 增加用户金币
        self.user_dao.add_gold(user_id, total_value)

        yield event.plain_result(f"成功卖出所有鱼类！\n获得金币: {total_value}枚")

    async def sell_by_rarity_command(self, event: AstrMessageEvent, rarity: int):
        """按稀有度卖出鱼类命令"""
        user_id = event.get_sender_id()

        # 验证稀有度参数
        if rarity < 1 or rarity > 5:
            yield event.plain_result("稀有度参数无效，请输入1-5之间的数字！")
            return

        # 获取指定稀有度的鱼类
        fish_inventory = self.sell_dao.get_user_fish_by_rarity(user_id, rarity)

        if not fish_inventory:
            yield event.plain_result(f"您的鱼塘中没有 {rarity} 星鱼类！")
            return

        # 计算总价值
        total_value = sum(fish['value'] for fish in fish_inventory)

        # 删除指定稀有度的鱼
        self.sell_dao.delete_user_fish_by_rarity(user_id, rarity)

        # 增加用户金币
        self.user_dao.add_gold(user_id, total_value)

        yield event.plain_result(f"成功卖出所有 {rarity} 星鱼类！\n共卖出 {len(fish_inventory)} 条鱼\n获得金币: {total_value}枚")

    async def sell_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """出售鱼竿命令"""
        user_id = event.get_sender_id()

        # 检查鱼竿是否存在且属于用户
        rod = self.sell_dao.get_user_rod_by_id(user_id, rod_id)

        if not rod:
            yield event.plain_result("找不到指定的鱼竿或该鱼竿不属于您！")
            return

        # 检查鱼竿是否正在使用
        if rod['is_equipped']:
            yield event.plain_result("不能出售正在使用的鱼竿，请先卸下该鱼竿！")
            return

        # 计算出售价格 (根据稀有度确定基础价格)
        base_price = 100 * rod['rarity']  # 1星100金币，2星200金币，以此类推
        sell_price = max(10, base_price // 2)  # 最低10金币

        # 删除鱼竿
        self.sell_dao.delete_user_rod(user_id, rod_id)

        # 增加用户金币
        self.user_dao.add_gold(user_id, sell_price)

        yield event.plain_result(f"成功出售鱼竿 [{rod['name']}]！\n获得金币: {sell_price}枚")

    async def sell_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """出售鱼饵命令"""
        user_id = event.get_sender_id()

        # 检查鱼饵是否存在且属于用户
        # 注意：这里需要直接查询数据库，因为SellDAO没有提供这个方法
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
        self.sell_dao.delete_user_bait(user_id, bait['bait_template_id'], bait['quantity'])

        # 增加用户金币
        self.user_dao.add_gold(user_id, sell_price)

        yield event.plain_result(f"成功出售鱼饵 [{bait['bait_name']}] x{bait['quantity']}！\n获得金币: {sell_price}枚")

    async def sell_all_rods_command(self, event: AstrMessageEvent):
        """出售所有鱼竿命令"""
        user_id = event.get_sender_id()

        # 获取用户所有非五星鱼竿（保留五星鱼竿）
        # 注意：这里需要直接查询数据库，因为SellDAO没有提供这个方法
        rods = self.db.fetch_all(
            """SELECT uri.*, rt.name as rod_name, rt.rarity as rod_rarity
               FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = FALSE AND rt.rarity < 5""",
            (user_id,)
        )

        if not rods:
            yield event.plain_result("您没有可以出售的鱼竿（非五星且未装备的鱼竿）！")
            return

        # 计算总价值
        total_value = 0
        rod_names = []

        for rod in rods:
            # 计算出售价格 (根据稀有度确定基础价格)
            base_price = 100 * rod['rod_rarity']  # 1星100金币，2星200金币，以此类推
            sell_price = max(10, base_price // 2)  # 最低10金币

            total_value += sell_price
            rod_names.append(rod['rod_name'])

            # 删除鱼竿
            self.sell_dao.delete_user_rod(user_id, rod['id'])

        # 增加用户金币
        self.user_dao.add_gold(user_id, total_value)

        # 构造返回消息
        rod_list = "\n".join([f"  · {name}" for name in rod_names])
        yield event.plain_result(f"成功出售以下鱼竿：\n{rod_list}\n\n获得金币: {total_value}枚")