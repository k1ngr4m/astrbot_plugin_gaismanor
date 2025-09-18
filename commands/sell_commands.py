from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.shop_service import ShopService
from ..models.database import DatabaseManager

class SellCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.shop_service = ShopService(db_manager)

    async def sell_all_command(self, event: AstrMessageEvent):
        """全部卖出命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取所有鱼类库存
        fish_inventory = self.user_service.get_user_fish_inventory(user_id)

        if not fish_inventory:
            yield event.plain_result("您的鱼塘是空的，没有鱼可以出售")
            return

        # 计算总价值
        total_value = 0
        sold_count = 0

        for fish in fish_inventory:
            # 获取鱼类模板信息
            fish_template = self.db_manager.fetch_one(
                "SELECT base_value FROM fish_templates WHERE id = ?",
                (fish.fish_template_id,)
            )
            if fish_template:
                # 计算出售价格 (按基础价值的80%)
                sell_price = int(fish_template['base_value'] * 0.8)
                total_value += sell_price
                sold_count += 1

        if sold_count == 0:
            yield event.plain_result("没有可以出售的鱼")
            return

        # 添加金币
        user.gold += total_value
        self.user_service.update_user(user)

        # 删除所有鱼类库存
        self.db_manager.execute_query(
            "DELETE FROM user_fish_inventory WHERE user_id = ?",
            (user_id,)
        )

        yield event.plain_result(f"成功出售 {sold_count} 条鱼，获得金币: {total_value}枚")

    async def sell_keep_one_command(self, event: AstrMessageEvent):
        """保留卖出命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取所有鱼类库存
        fish_inventory = self.user_service.get_user_fish_inventory(user_id)

        if not fish_inventory:
            yield event.plain_result("您的鱼塘是空的，没有鱼可以出售")
            return

        if len(fish_inventory) <= 1:
            yield event.plain_result("鱼塘中只有一条鱼或没有鱼，无法保留卖出")
            return

        # 计算总价值（保留一条）
        total_value = 0
        sold_count = 0

        # 跳过第一条鱼（保留）
        for fish in fish_inventory[1:]:
            # 获取鱼类模板信息
            fish_template = self.db_manager.fetch_one(
                "SELECT base_value FROM fish_templates WHERE id = ?",
                (fish.fish_template_id,)
            )
            if fish_template:
                # 计算出售价格 (按基础价值的80%)
                sell_price = int(fish_template['base_value'] * 0.8)
                total_value += sell_price
                sold_count += 1

        if sold_count == 0:
            yield event.plain_result("没有可以出售的鱼")
            return

        # 添加金币
        user.gold += total_value
        self.user_service.update_user(user)

        # 删除除第一条外的所有鱼类库存
        first_fish_id = fish_inventory[0].id
        self.db_manager.execute_query(
            "DELETE FROM user_fish_inventory WHERE user_id = ? AND id != ?",
            (user_id, first_fish_id)
        )

        yield event.plain_result(f"成功出售 {sold_count} 条鱼，获得金币: {total_value}枚，保留了1条鱼")

    async def sell_by_rarity_command(self, event: AstrMessageEvent, rarity: int):
        """按稀有度出售命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查稀有度范围
        if rarity < 1 or rarity > 5:
            yield event.plain_result("稀有度必须在1-5之间")
            return

        # 获取指定稀有度的鱼类库存
        fish_inventory = self.db_manager.fetch_all(
            """SELECT ufi.*, ft.base_value FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ? AND ft.rarity = ?""",
            (user_id, rarity)
        )

        if not fish_inventory:
            yield event.plain_result(f"您的鱼塘中没有{rarity}星稀有度的鱼")
            return

        # 计算总价值
        total_value = 0
        sold_count = 0

        fish_ids_to_delete = []
        for fish in fish_inventory:
            # 计算出售价格 (按基础价值的80%)
            sell_price = int(fish['base_value'] * 0.8)
            total_value += sell_price
            sold_count += 1
            fish_ids_to_delete.append(fish['id'])

        if sold_count == 0:
            yield event.plain_result("没有可以出售的鱼")
            return

        # 添加金币
        user.gold += total_value
        self.user_service.update_user(user)

        # 删除指定稀有度的鱼类库存
        placeholders = ','.join('?' * len(fish_ids_to_delete))
        self.db_manager.execute_query(
            f"DELETE FROM user_fish_inventory WHERE id IN ({placeholders})",
            fish_ids_to_delete
        )

        rarity_stars = "★" * rarity
        yield event.plain_result(f"成功出售 {sold_count} 条{rarity_stars}稀有度的鱼，获得金币: {total_value}枚")

    async def sell_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """出售鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在
        rod_instance = self.db_manager.fetch_one(
            """SELECT uri.*, rt.purchase_cost FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.rod_template_id = ?""",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("您没有该鱼竿")
            return

        # 检查是否装备中
        if rod_instance['is_equipped']:
            yield event.plain_result("装备中的鱼竿无法出售，请先卸下")
            return

        # 计算出售价格 (按原价的50%)
        sell_price = int((rod_instance['purchase_cost'] or 0) * 0.5)

        # 添加金币
        user.gold += sell_price
        self.user_service.update_user(user)

        # 删除鱼竿实例
        self.db_manager.execute_query(
            "DELETE FROM user_rod_instances WHERE id = ?",
            (rod_instance['id'],)
        )

        rod_template = self.db_manager.fetch_one(
            "SELECT name FROM rod_templates WHERE id = ?",
            (rod_id,)
        )
        rod_name = rod_template['name'] if rod_template else "未知鱼竿"

        yield event.plain_result(f"成功出售鱼竿: {rod_name}，获得金币: {sell_price}枚")

    async def sell_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """出售鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼饵是否存在
        bait_instance = self.db_manager.fetch_one(
            """SELECT ubi.*, bt.cost FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.bait_template_id = ? AND ubi.quantity > 0""",
            (user_id, bait_id)
        )

        if not bait_instance:
            yield event.plain_result("您没有该鱼饵或数量不足")
            return

        # 计算出售价格 (按原价的50%)
        sell_price = int(bait_instance['cost'] * 0.5)

        # 添加金币
        user.gold += sell_price
        self.user_service.update_user(user)

        # 删除鱼饵库存
        self.db_manager.execute_query(
            "DELETE FROM user_bait_inventory WHERE id = ?",
            (bait_instance['id'],)
        )

        bait_template = self.db_manager.fetch_one(
            "SELECT name FROM bait_templates WHERE id = ?",
            (bait_id,)
        )
        bait_name = bait_template['name'] if bait_template else "未知鱼饵"

        yield event.plain_result(f"成功出售鱼饵: {bait_name}，获得金币: {sell_price}枚")