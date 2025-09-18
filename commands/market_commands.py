from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger
from ..services.user_service import UserService
from ..services.equipment_service import EquipmentService
from ..models.database import DatabaseManager
import time

class MarketCommands:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_service = UserService(db_manager)
        self.equipment_service = EquipmentService(db_manager)

    async def market_command(self, event: AstrMessageEvent):
        """市场命令"""
        # 获取市场商品列表
        market_items = self.db_manager.fetch_all(
            """SELECT ml.*, u.nickname as seller_name FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               WHERE ml.expires_at > ?""",
            (int(time.time()),)
        )

        if not market_items:
            yield event.plain_result("市场暂时没有商品，快去上架一些物品吧！")
            return

        # 构建市场信息
        market_info = "=== 庄园市场 ===\n"
        for item in market_items:
            item_type = item['item_type']
            item_id = item['item_id']
            price = item['price']
            seller_name = item['seller_name']

            # 获取物品名称
            item_name = "未知物品"
            if item_type == "fish":
                fish_info = self.db_manager.fetch_one(
                    """SELECT ft.name, ft.rarity FROM user_fish_inventory ufi
                       JOIN fish_templates ft ON ufi.fish_template_id = ft.id
                       WHERE ufi.id = ?""",
                    (item_id,)
                )
                if fish_info:
                    rarity_stars = "★" * fish_info['rarity']
                    item_name = f"{fish_info['name']} {rarity_stars}"
            elif item_type == "rod":
                rod_info = self.db_manager.fetch_one(
                    """SELECT rt.name, rt.rarity FROM user_rod_instances uri
                       JOIN rod_templates rt ON uri.rod_template_id = rt.id
                       WHERE uri.id = ?""",
                    (item_id,)
                )
                if rod_info:
                    rarity_stars = "★" * rod_info['rarity']
                    item_name = f"{rod_info['name']} {rarity_stars}"
            elif item_type == "bait":
                bait_info = self.db_manager.fetch_one(
                    """SELECT bt.name, bt.rarity FROM user_bait_inventory ubi
                       JOIN bait_templates bt ON ubi.bait_template_id = bt.id
                       WHERE ubi.id = ?""",
                    (item_id,)
                )
                if bait_info:
                    rarity_stars = "★" * bait_info['rarity']
                    item_name = f"{bait_info['name']} {rarity_stars}"

            market_info += f"ID: {item['id']} - {item_name}\n"
            market_info += f"  价格: {price}金币  卖家: {seller_name}\n\n"

        yield event.plain_result(market_info)

    async def list_bait_command(self, event: AstrMessageEvent, bait_id: int, price: int):
        """上架鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼饵是否存在且数量足够
        bait_instance = self.db_manager.fetch_one(
            """SELECT ubi.id, ubi.quantity, bt.name FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.bait_template_id = ? AND ubi.quantity > 0""",
            (user_id, bait_id)
        )

        if not bait_instance:
            yield event.plain_result("您没有该鱼饵或数量不足")
            return

        # 检查价格是否合理
        if price <= 0:
            yield event.plain_result("价格必须大于0")
            return

        # 上架鱼饵（减少库存）
        self.db_manager.execute_query(
            "UPDATE user_bait_inventory SET quantity = quantity - 1 WHERE id = ?",
            (bait_instance['id'],)
        )

        # 添加到市场
        self.db_manager.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, "bait", bait_instance['id'], price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        yield event.plain_result(f"成功上架鱼饵: {bait_instance['name']}，价格: {price}金币")

    async def list_rod_command(self, event: AstrMessageEvent, rod_id: int, price: int):
        """上架鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在
        rod_instance = self.db_manager.fetch_one(
            """SELECT uri.id, uri.is_equipped, rt.name FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.rod_template_id = ?""",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("您没有该鱼竿")
            return

        # 检查是否装备中
        if rod_instance['is_equipped']:
            yield event.plain_result("装备中的鱼竿无法上架，请先卸下")
            return

        # 检查价格是否合理
        if price <= 0:
            yield event.plain_result("价格必须大于0")
            return

        # 上架鱼竿（删除用户库存）
        self.db_manager.execute_query(
            "DELETE FROM user_rod_instances WHERE id = ?",
            (rod_instance['id'],)
        )

        # 添加到市场
        self.db_manager.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, "rod", rod_instance['id'], price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        yield event.plain_result(f"成功上架鱼竿: {rod_instance['name']}，价格: {price}金币")

    async def buy_item_command(self, event: AstrMessageEvent, item_id: int):
        """购买商品命令"""
        user_id = event.get_sender_id()
        user = self.user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查商品是否存在且未过期
        market_item = self.db_manager.fetch_one(
            "SELECT * FROM market_listings WHERE id = ? AND expires_at > ?",
            (item_id, int(time.time()))
        )

        if not market_item:
            yield event.plain_result("商品不存在或已过期")
            return

        # 检查金币是否足够
        if user.gold < market_item['price']:
            yield event.plain_result("金币不足，无法购买")
            return

        # 扣除买家金币
        self.db_manager.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (market_item['price'], user_id)
        )

        # 添加卖家金币
        self.db_manager.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (market_item['price'], market_item['seller_user_id'])
        )

        # 根据物品类型处理物品转移
        item_type = market_item['item_type']
        original_item_id = market_item['item_id']

        if item_type == "bait":
            # 购买鱼饵
            bait_info = self.db_manager.fetch_one(
                "SELECT bait_template_id FROM user_bait_inventory WHERE id = ?",
                (original_item_id,)
            )
            if bait_info:
                # 检查买家是否已有该鱼饵
                existing_bait = self.db_manager.fetch_one(
                    "SELECT id, quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                    (user_id, bait_info['bait_template_id'])
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
                        (user_id, bait_info['bait_template_id'])
                    )
        elif item_type == "rod":
            # 购买鱼竿
            rod_info = self.db_manager.fetch_one(
                "SELECT rod_template_id, level, exp, durability FROM user_rod_instances WHERE id = ?",
                (original_item_id,)
            )
            if rod_info:
                # 添加到买家库存
                self.db_manager.execute_query(
                    """INSERT INTO user_rod_instances
                       (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                       VALUES (?, ?, ?, ?, FALSE, ?, ?)""",
                    (user_id, rod_info['rod_template_id'], rod_info['level'], rod_info['exp'],
                     int(time.time()), rod_info['durability'])
                )

        # 删除市场商品
        self.db_manager.execute_query(
            "DELETE FROM market_listings WHERE id = ?",
            (item_id,)
        )

        yield event.plain_result("购买成功！")