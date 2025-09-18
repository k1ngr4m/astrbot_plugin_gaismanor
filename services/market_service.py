from typing import Optional, List

from astrbot.core.platform import AstrMessageEvent
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.fishing import FishTemplate
from ..models.database import DatabaseManager
import time

class MarketService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def market_command(self, event: AstrMessageEvent):
        """市场主命令"""
        market_info = """=== 庄园市场 ===
欢迎来到庄园市场！您可以在这里购买其他玩家上架的商品。

可用命令:
/市场 鱼类  - 查看市场上架的鱼类
/市场 鱼竿  - 查看市场上架的鱼竿
/市场 饰品  - 查看市场上架的饰品
/市场 鱼饵  - 查看市场上架的鱼饵
/上架鱼类 <ID> <价格>  - 将指定ID的鱼类上架到市场
/上架鱼竿 <ID> <价格>  - 将指定ID的鱼竿上架到市场
/上架饰品 <ID> <价格>  - 将指定ID的饰品上架到市场
/上架鱼饵 <ID> <价格>  - 将指定ID的鱼饵上架到市场
/购买 <商品ID>  - 购买指定ID的商品
"""
        yield event.plain_result(market_info)

    async def market_fish_command(self, event: AstrMessageEvent):
        """查看市场上架的鱼类"""
        fish_listings = self.get_market_fish_listings()

        if not fish_listings:
            yield event.plain_result("市场上暂无鱼类商品")
            return

        fish_info = "=== 市场鱼类商品 ===\n"
        for listing in fish_listings:
            fish_template = self.db.fetch_one(
                "SELECT name, rarity, base_value FROM fish_templates WHERE id = ?",
                (listing['fish_template_id'],)
            )
            if fish_template:
                rarity_stars = "★" * fish_template['rarity'] + "☆" * (5 - fish_template['rarity'])
                fish_info += f"商品ID: {listing['id']} - {fish_template['name']} {rarity_stars}\n"
                fish_info += f"  重量: {listing['fish_weight']:.2f}kg  价值: {listing['fish_value']}金币\n"
                fish_info += f"  售价: {listing['price']}金币  卖家: {listing['seller_nickname']}\n"
                fish_info += f"  上架时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['created_at']))}\n\n"

        yield event.plain_result(fish_info)

    async def market_rod_command(self, event: AstrMessageEvent):
        """查看市场上架的鱼竿"""
        rod_listings = self.get_market_rod_listings()

        if not rod_listings:
            yield event.plain_result("市场上暂无鱼竿商品")
            return

        rod_info = "=== 市场鱼竿商品 ===\n"
        for listing in rod_listings:
            rod_template = self.db.fetch_one(
                "SELECT name, rarity, purchase_cost FROM rod_templates WHERE id = ?",
                (listing['rod_template_id'],)
            )
            if rod_template:
                rarity_stars = "★" * rod_template['rarity'] + "☆" * (5 - rod_template['rarity'])
                rod_info += f"商品ID: {listing['id']} - {rod_template['name']} {rarity_stars}\n"
                rod_info += f"  等级: {listing['rod_level']}  经验: {listing['rod_exp']}\n"
                rod_info += f"  品质加成: +{listing['quality_mod']}  数量加成: +{listing['quantity_mod']}\n"
                rod_info += f"  售价: {listing['price']}金币  卖家: {listing['seller_nickname']}\n"
                rod_info += f"  上架时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['created_at']))}\n\n"

        yield event.plain_result(rod_info)

    async def market_accessory_command(self, event: AstrMessageEvent):
        """查看市场上架的饰品"""
        accessory_listings = self.get_market_accessory_listings()

        if not accessory_listings:
            yield event.plain_result("市场上暂无饰品商品")
            return

        accessory_info = "=== 市场饰品商品 ===\n"
        for listing in accessory_listings:
            accessory_template = self.db.fetch_one(
                "SELECT name, rarity FROM accessory_templates WHERE id = ?",
                (listing['accessory_template_id'],)
            )
            if accessory_template:
                rarity_stars = "★" * accessory_template['rarity'] + "☆" * (5 - accessory_template['rarity'])
                accessory_info += f"商品ID: {listing['id']} - {accessory_template['name']} {rarity_stars}\n"
                accessory_info += f"  品质加成: +{listing['quality_mod']}  数量加成: +{listing['quantity_mod']}\n"
                accessory_info += f"  稀有度加成: +{listing['rare_mod']}  金币加成: +{listing['coin_mod']}\n"
                accessory_info += f"  售价: {listing['price']}金币  卖家: {listing['seller_nickname']}\n"
                accessory_info += f"  上架时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['created_at']))}\n\n"

        yield event.plain_result(accessory_info)

    async def market_bait_command(self, event: AstrMessageEvent):
        """查看市场上架的鱼饵"""
        bait_listings = self.get_market_bait_listings()

        if not bait_listings:
            yield event.plain_result("市场上暂无鱼饵商品")
            return

        bait_info = "=== 市场鱼饵商品 ===\n"
        for listing in bait_listings:
            bait_template = self.db.fetch_one(
                "SELECT name, rarity, cost FROM bait_templates WHERE id = ?",
                (listing['bait_template_id'],)
            )
            if bait_template:
                rarity_stars = "★" * bait_template['rarity'] + "☆" * (5 - bait_template['rarity'])
                bait_info += f"商品ID: {listing['id']} - {bait_template['name']} {rarity_stars}\n"
                bait_info += f"  数量: {listing['quantity']}  效果: {listing['effect_description']}\n"
                bait_info += f"  售价: {listing['price']}金币  卖家: {listing['seller_nickname']}\n"
                bait_info += f"  上架时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(listing['created_at']))}\n\n"

        yield event.plain_result(bait_info)

    async def list_fish_command(self, event: AstrMessageEvent, fish_id: int, price: int):
        """上架鱼类命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼类是否存在且属于用户
        fish_inventory = self.db.fetch_one(
            """SELECT ufi.*, ft.name, ft.rarity, ft.base_value FROM user_fish_inventory ufi
               JOIN fish_templates ft ON ufi.fish_template_id = ft.id
               WHERE ufi.user_id = ? AND ufi.id = ?""",
            (user_id, fish_id)
        )

        if not fish_inventory:
            yield event.plain_result("未找到该鱼类或不属于您")
            return

        # 检查价格是否合理 (至少为基础价值的50%)
        min_price = int(fish_inventory['base_value'] * 0.5)
        if price < min_price:
            yield event.plain_result(f"价格过低，请至少设置为 {min_price} 金币")
            return

        # 上架鱼类到市场
        success = self.list_fish(user_id, fish_id, price)

        if success:
            yield event.plain_result(f"成功上架鱼类: {fish_inventory['name']}，售价: {price}金币")
        else:
            yield event.plain_result("上架鱼类失败")

    async def list_rod_command(self, event: AstrMessageEvent, rod_id: int, price: int):
        """上架鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在且属于用户
        rod_instance = self.db.fetch_one(
            """SELECT uri.*, rt.name, rt.rarity, rt.purchase_cost FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.id = ?""",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到该鱼竿或不属于您")
            return

        # 检查是否是装备中的鱼竿
        if rod_instance['is_equipped']:
            yield event.plain_result("装备中的鱼竿无法上架，请先卸下")
            return

        # 检查价格是否合理 (至少为原价的50%)
        min_price = int((rod_instance['purchase_cost'] or 0) * 0.5)
        if price < min_price:
            yield event.plain_result(f"价格过低，请至少设置为 {min_price} 金币")
            return

        # 上架鱼竿到市场
        success = self.list_rod(user_id, rod_id, price)

        if success:
            yield event.plain_result(f"成功上架鱼竿: {rod_instance['name']}，售价: {price}金币")
        else:
            yield event.plain_result("上架鱼竿失败")

    async def list_accessory_command(self, event: AstrMessageEvent, accessory_id: int, price: int):
        """上架饰品命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查饰品是否存在且属于用户
        accessory_instance = self.db.fetch_one(
            """SELECT uai.*, at.name, at.rarity FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.id = ?""",
            (user_id, accessory_id)
        )

        if not accessory_instance:
            yield event.plain_result("未找到该饰品或不属于您")
            return

        # 检查是否是装备中的饰品
        if accessory_instance['is_equipped']:
            yield event.plain_result("装备中的饰品无法上架，请先卸下")
            return

        # 检查价格是否合理 (至少为100金币)
        if price < 100:
            yield event.plain_result("价格过低，请至少设置为 100 金币")
            return

        # 上架饰品到市场
        success = self.list_accessory(user_id, accessory_id, price)

        if success:
            yield event.plain_result(f"成功上架饰品: {accessory_instance['name']}，售价: {price}金币")
        else:
            yield event.plain_result("上架饰品失败")

    async def list_bait_command(self, event: AstrMessageEvent, bait_id: int, price: int):
        """上架鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼饵是否存在且属于用户
        bait_inventory = self.db.fetch_one(
            """SELECT ubi.*, bt.name, bt.rarity, bt.cost FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ? AND ubi.id = ? AND ubi.quantity > 0""",
            (user_id, bait_id)
        )

        if not bait_inventory:
            yield event.plain_result("未找到该鱼饵或数量不足")
            return

        # 检查价格是否合理 (至少为基础价格的50%)
        min_price = int(bait_inventory['cost'] * 0.5)
        if price < min_price:
            yield event.plain_result(f"价格过低，请至少设置为 {min_price} 金币")
            return

        # 上架鱼饵到市场
        success = self.list_bait(user_id, bait_id, price)

        if success:
            yield event.plain_result(f"成功上架鱼饵: {bait_inventory['name']}，售价: {price}金币")
        else:
            yield event.plain_result("上架鱼饵失败")

    async def buy_item_command(self, event: AstrMessageEvent, item_id: int):
        """购买商品命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买商品
        success = self.buy_item(user_id, item_id)

        if success:
            yield event.plain_result("购买成功！")
        else:
            yield event.plain_result("购买失败，请检查金币是否足够或商品是否存在")

    def get_market_fish_listings(self) -> List[dict]:
        """获取市场上架的鱼类"""
        results = self.db.fetch_all(
            """SELECT ml.*, u.nickname as seller_nickname, ufi.fish_template_id, ufi.weight as fish_weight, ufi.value as fish_value
               FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               JOIN user_fish_inventory ufi ON ml.item_id = ufi.id
               WHERE ml.item_type = 'fish' AND ml.expires_at > ?
               ORDER BY ml.price ASC""",
            (int(time.time()),)
        )
        return [dict(row) for row in results]

    def get_market_rod_listings(self) -> List[dict]:
        """获取市场上架的鱼竿"""
        results = self.db.fetch_all(
            """SELECT ml.*, u.nickname as seller_nickname, uri.rod_template_id, uri.level as rod_level, uri.exp as rod_exp,
                      rt.quality_mod, rt.quantity_mod, rt.rare_mod, rt.durability
               FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               JOIN user_rod_instances uri ON ml.item_id = uri.id
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE ml.item_type = 'rod' AND ml.expires_at > ?
               ORDER BY ml.price ASC""",
            (int(time.time()),)
        )
        return [dict(row) for row in results]

    def get_market_accessory_listings(self) -> List[dict]:
        """获取市场上架的饰品"""
        results = self.db.fetch_all(
            """SELECT ml.*, u.nickname as seller_nickname, uai.accessory_template_id,
                      at.quality_mod, at.quantity_mod, at.rare_mod, at.coin_mod
               FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               JOIN user_accessory_instances uai ON ml.item_id = uai.id
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE ml.item_type = 'accessory' AND ml.expires_at > ?
               ORDER BY ml.price ASC""",
            (int(time.time()),)
        )
        return [dict(row) for row in results]

    def get_market_bait_listings(self) -> List[dict]:
        """获取市场上架的鱼饵"""
        results = self.db.fetch_all(
            """SELECT ml.*, u.nickname as seller_nickname, ubi.bait_template_id, ubi.quantity,
                      bt.effect_description
               FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               JOIN user_bait_inventory ubi ON ml.item_id = ubi.id
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ml.item_type = 'bait' AND ml.expires_at > ?
               ORDER BY ml.price ASC""",
            (int(time.time()),)
        )
        return [dict(row) for row in results]

    def list_fish(self, user_id: str, fish_id: int, price: int) -> bool:
        """上架鱼类到市场"""
        # 检查鱼类是否存在且属于用户
        fish_inventory = self.db.fetch_one(
            "SELECT * FROM user_fish_inventory WHERE user_id = ? AND id = ?",
            (user_id, fish_id)
        )
        if not fish_inventory:
            return False

        # 添加到市场
        self.db.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, 'fish', ?, ?, ?, ?)""",
            (user_id, fish_id, price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        # 从用户鱼类库存中移除
        self.db.execute_query(
            "DELETE FROM user_fish_inventory WHERE user_id = ? AND id = ?",
            (user_id, fish_id)
        )

        return True

    def list_rod(self, user_id: str, rod_id: int, price: int) -> bool:
        """上架鱼竿到市场"""
        # 检查鱼竿是否存在且属于用户
        rod_instance = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )
        if not rod_instance:
            return False

        # 检查是否是装备中的鱼竿
        if rod_instance['is_equipped']:
            return False

        # 添加到市场
        self.db.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, 'rod', ?, ?, ?, ?)""",
            (user_id, rod_id, price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        # 从用户鱼竿库存中移除
        self.db.execute_query(
            "DELETE FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )

        return True

    def list_accessory(self, user_id: str, accessory_id: int, price: int) -> bool:
        """上架饰品到市场"""
        # 检查饰品是否存在且属于用户
        accessory_instance = self.db.fetch_one(
            "SELECT * FROM user_accessory_instances WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )
        if not accessory_instance:
            return False

        # 检查是否是装备中的饰品
        if accessory_instance['is_equipped']:
            return False

        # 添加到市场
        self.db.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, 'accessory', ?, ?, ?, ?)""",
            (user_id, accessory_id, price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        # 从用户饰品库存中移除
        self.db.execute_query(
            "DELETE FROM user_accessory_instances WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )

        return True

    def list_bait(self, user_id: str, bait_id: int, price: int) -> bool:
        """上架鱼饵到市场"""
        # 检查鱼饵是否存在且属于用户
        bait_inventory = self.db.fetch_one(
            "SELECT * FROM user_bait_inventory WHERE user_id = ? AND id = ? AND quantity > 0",
            (user_id, bait_id)
        )
        if not bait_inventory:
            return False

        # 添加到市场
        self.db.execute_query(
            """INSERT INTO market_listings
               (seller_user_id, item_type, item_id, price, created_at, expires_at)
               VALUES (?, 'bait', ?, ?, ?, ?)""",
            (user_id, bait_id, price, int(time.time()), int(time.time()) + 86400 * 7)  # 7天有效期
        )

        # 从用户鱼饵库存中移除
        self.db.execute_query(
            "DELETE FROM user_bait_inventory WHERE user_id = ? AND id = ?",
            (user_id, bait_id)
        )

        return True

    def buy_item(self, user_id: str, item_id: int) -> bool:
        """购买商品"""
        # 获取商品信息
        market_item = self.db.fetch_one(
            """SELECT ml.*, u.gold as seller_gold FROM market_listings ml
               JOIN users u ON ml.seller_user_id = u.user_id
               WHERE ml.id = ? AND ml.expires_at > ?""",
            (item_id, int(time.time()))
        )
        if not market_item:
            return False

        # 检查买家金币是否足够
        buyer = self.get_user(user_id)
        if not buyer or buyer.gold < market_item['price']:
            return False

        # 扣除买家金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (market_item['price'], user_id)
        )

        # 添加卖家金币
        self.db.execute_query(
            "UPDATE users SET gold = gold + ? WHERE user_id = ?",
            (market_item['price'], market_item['seller_user_id'])
        )

        # 根据商品类型处理转移
        item_type = market_item['item_type']
        original_item_id = market_item['item_id']

        if item_type == "fish":
            # 购买鱼类
            fish_inventory = self.db.fetch_one(
                "SELECT * FROM user_fish_inventory WHERE id = ?",
                (original_item_id,)
            )
            if fish_inventory:
                # 转移到买家库存
                self.db.execute_query(
                    """INSERT INTO user_fish_inventory
                       (user_id, fish_template_id, weight, value, caught_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, fish_inventory['fish_template_id'], fish_inventory['weight'], fish_inventory['value'], fish_inventory['caught_at'])
                )

                # 从原库存删除
                self.db.execute_query(
                    "DELETE FROM user_fish_inventory WHERE id = ?",
                    (original_item_id,)
                )
        elif item_type == "rod":
            # 购买鱼竿
            rod_instance = self.db.fetch_one(
                "SELECT * FROM user_rod_instances WHERE id = ?",
                (original_item_id,)
            )
            if rod_instance:
                # 转移到买家库存
                self.db.execute_query(
                    """INSERT INTO user_rod_instances
                       (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                       VALUES (?, ?, ?, ?, FALSE, ?, ?)""",
                    (user_id, rod_instance['rod_template_id'], rod_instance['level'], rod_instance['exp'], rod_instance['acquired_at'], rod_instance['durability'])
                )

                # 从原库存删除
                self.db.execute_query(
                    "DELETE FROM user_rod_instances WHERE id = ?",
                    (original_item_id,)
                )
        elif item_type == "accessory":
            # 购买饰品
            accessory_instance = self.db.fetch_one(
                "SELECT * FROM user_accessory_instances WHERE id = ?",
                (original_item_id,)
            )
            if accessory_instance:
                # 转移到买家库存
                self.db.execute_query(
                    """INSERT INTO user_accessory_instances
                       (user_id, accessory_template_id, is_equipped, acquired_at)
                       VALUES (?, ?, FALSE, ?)""",
                    (user_id, accessory_instance['accessory_template_id'], accessory_instance['acquired_at'])
                )

                # 从原库存删除
                self.db.execute_query(
                    "DELETE FROM user_accessory_instances WHERE id = ?",
                    (original_item_id,)
                )
        elif item_type == "bait":
            # 购买鱼饵
            bait_inventory = self.db.fetch_one(
                "SELECT * FROM user_bait_inventory WHERE id = ?",
                (original_item_id,)
            )
            if bait_inventory:
                # 检查买家是否已有该鱼饵
                existing_bait = self.db.fetch_one(
                    "SELECT id, quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
                    (user_id, bait_inventory['bait_template_id'])
                )
                if existing_bait:
                    # 增加数量
                    self.db.execute_query(
                        "UPDATE user_bait_inventory SET quantity = quantity + ? WHERE id = ?",
                        (bait_inventory['quantity'], existing_bait['id'])
                    )
                else:
                    # 添加新的鱼饵库存
                    self.db.execute_query(
                        """INSERT INTO user_bait_inventory
                           (user_id, bait_template_id, quantity)
                           VALUES (?, ?, ?)""",
                        (user_id, bait_inventory['bait_template_id'], bait_inventory['quantity'])
                    )

                # 从原库存删除
                self.db.execute_query(
                    "DELETE FROM user_bait_inventory WHERE id = ?",
                    (original_item_id,)
                )

        # 删除市场商品
        self.db.execute_query(
            "DELETE FROM market_listings WHERE id = ?",
            (item_id,)
        )

        return True

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