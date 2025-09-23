from typing import Optional, List

from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
from ..dao.shop_dao import ShopDAO
from ..dao.user_dao import UserDAO
from ..enums.messages import Messages
import time

class ShopService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def shop_command(self, event: AstrMessageEvent):
        """商店主命令"""
        shop_info = """=== 庄园商店 ===

欢迎来到庄园商店！您可以在这里购买各种钓鱼装备。

可用命令:

/商店鱼竿  - 查看可购买的鱼竿

/商店鱼饵  - 查看可购买的鱼饵

/商店饰品  - 查看可购买的饰品

/购买鱼饵 <ID> [数量]  - 购买指定ID的鱼饵

/购买鱼竿 <ID>  - 购买指定ID的鱼竿

/购买饰品 <ID>  - 购买指定ID的饰品

/使用鱼饵 <ID>  - 使用指定ID的鱼饵

/使用鱼竿 <ID>  - 装备指定ID的鱼竿

/使用饰品 <ID>  - 装备指定ID的饰品
"""
        yield event.plain_result(shop_info)

    async def shop_rods_command(self, event: AstrMessageEvent):
        """查看鱼竿商店商品"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        rods = self.get_rod_shop_items(user.level)

        if not rods:
            yield event.plain_result(Messages.SHOP_NO_ROD_ITEMS.value)
            return

        rod_info = "=== 鱼竿商店 ===\n\n"
        for rod in rods:
            rarity_stars = "★" * rod.rarity + "☆" * (5 - rod.rarity)
            rod_info += f"ID: {rod.id} - {rod.name} {rarity_stars}\n\n"
            rod_info += f"  价格: {rod.purchase_cost}金币  品质加成: +{rod.quality_mod}  数量加成: +{rod.quantity_mod}\n\n"
            rod_info += f"  描述: {rod.description}\n\n"

        yield event.plain_result(rod_info)

    async def shop_bait_command(self, event: AstrMessageEvent):
        """查看鱼饵商店商品"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查用户是否已解锁鱼饵系统
        if not self.is_bait_system_unlocked(user_id):
            yield event.plain_result(Messages.SHOP_BAIT_SYSTEM_NOT_UNLOCKED.value)
            return

        bait_list = self.get_bait_shop_items(user.level)

        if not bait_list:
            yield event.plain_result(Messages.SHOP_NO_BAIT_ITEMS.value)
            return

        bait_info = "=== 鱼饵商店 ===\n\n"
        for bait in bait_list:
            rarity_stars = "★" * bait.rarity + "☆" * (5 - bait.rarity)
            bait_info += f"ID: {bait.id} - {bait.name} {rarity_stars}\n\n"
            bait_info += f"  价格: {bait.cost}金币  效果: {bait.effect_description}\n\n"
            bait_info += f"  描述: {bait.description}\n\n"

        yield event.plain_result(bait_info)

    async def shop_accessory_command(self, event: AstrMessageEvent):
        """查看饰品商店商品"""
        accessory_list = self.get_accessory_shop_items()

        if not accessory_list:
            yield event.plain_result(Messages.SHOP_NO_ACCESSORY_ITEMS.value)
            return

        accessory_info = "=== 饰品商店 ===\n\n"
        for accessory in accessory_list:
            rarity_stars = "★" * accessory.rarity + "☆" * (5 - accessory.rarity)
            accessory_info += f"ID: {accessory.id} - {accessory.name} {rarity_stars}\n\n"
            accessory_info += f"  价格: {accessory.cost}金币  品质加成: +{accessory.quality_mod}  数量加成: +{accessory.quantity_mod}\n\n"
            accessory_info += f"  稀有度加成: +{accessory.rare_mod}  金币加成: +{accessory.coin_mod}\n\n"
            accessory_info += f"  描述: {accessory.description}\n\n"

        yield event.plain_result(accessory_info)

    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        """购买鱼饵"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查用户是否已解锁鱼饵系统
        if not self.is_bait_system_unlocked(user_id):
            yield event.plain_result(Messages.SHOP_BAIT_SYSTEM_NOT_UNLOCKED.value)
            return

        # 购买鱼饵
        success = self.buy_bait(user_id, bait_id, quantity)

        if success:
            bait_template = self.db.fetch_one(
                "SELECT name FROM bait_templates WHERE id = ?",
                (bait_id,)
            )
            bait_name = bait_template['name'] if bait_template else "未知鱼饵"
            yield event.plain_result(f"{Messages.SHOP_BUY_BAIT_SUCCESS.value}: {bait_name} x{quantity}")
        else:
            yield event.plain_result(Messages.SHOP_BUY_BAIT_FAILED.value)

    async def buy_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        """购买饰品"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 购买饰品
        success = self.buy_accessory(user_id, accessory_id)

        if success:
            accessory_template = self.db.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (accessory_id,)
            )
            accessory_name = accessory_template['name'] if accessory_template else "未知饰品"
            yield event.plain_result(f"{Messages.SHOP_BUY_ACCESSORY_SUCCESS.value}: {accessory_name}")
        else:
            yield event.plain_result(Messages.SHOP_BUY_ACCESSORY_FAILED.value)

    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """购买鱼竿"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 购买鱼竿
        success = self.buy_rod(user_id, rod_id)

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"{Messages.SHOP_BUY_ROD_SUCCESS.value}: {rod_name}")
        else:
            yield event.plain_result(Messages.SHOP_BUY_ROD_FAILED.value)

    async def use_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """使用鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查鱼饵是否存在
        bait_instance = self.db.fetch_one(
            "SELECT * FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ? AND quantity > 0",
            (user_id, bait_id)
        )

        if not bait_instance:
            yield event.plain_result(Messages.SHOP_USE_BAIT_NOT_OWNED.value)
            return

        # 使用鱼饵（这里简化处理，实际应该应用鱼饵效果）
        yield event.plain_result(Messages.SHOP_USE_BAIT_FEATURE_COMING_SOON.value)

    async def use_accessory_command(self, event: AstrMessageEvent, accessory_id: int):
        """装备饰品命令"""
        from ..services.equipment_service import EquipmentService
        equipment_service = EquipmentService(self.db)

        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查饰品是否存在
        accessory_instance = self.db.fetch_one(
            "SELECT * FROM user_accessory_instances WHERE user_id = ? AND accessory_template_id = ?",
            (user_id, accessory_id)
        )

        if not accessory_instance:
            yield event.plain_result(Messages.SHOP_EQUIP_ACCESSORY_NOT_OWNED.value)
            return

        # 装备饰品
        success = equipment_service.equip_accessory(user_id, accessory_instance['id'])

        if success:
            accessory_template = self.db.fetch_one(
                "SELECT name FROM accessory_templates WHERE id = ?",
                (accessory_id,)
            )
            accessory_name = accessory_template['name'] if accessory_template else "未知饰品"
            yield event.plain_result(f"{Messages.SHOP_EQUIP_ACCESSORY_SUCCESS.value}: {accessory_name}")
        else:
            yield event.plain_result(Messages.SHOP_EQUIP_ACCESSORY_FAILED.value)

    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """装备鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
            return

        # 检查鱼竿是否存在
        rod_instance = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND rod_template_id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result(Messages.SHOP_EQUIP_ROD_NOT_OWNED.value)
            return

        # 装备鱼竿
        success = self.equip_rod(user_id, rod_instance['id'])

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"{Messages.SHOP_EQUIP_ROD_SUCCESS.value}: {rod_name}")
        else:
            yield event.plain_result(Messages.SHOP_EQUIP_ROD_FAILED.value)

    def get_rod_shop_items(self, user_level: int = 1) -> List[RodTemplate]:
        """获取鱼竿商店商品"""
        # 根据用户等级过滤可购买的鱼竿
        # 竹制鱼竿(2级)需要用户达到3级才能购买
        # 长者之竿(2级)需要用户达到8级才能购买
        # 冷静之竿(3级)需要用户达到12级才能购买
        # 碳素纤维竿(3级)需要用户达到20级才能购买
        if user_level >= 3:
            rarity_filter = "rt.rarity >= 1"
        else:
            rarity_filter = "rt.rarity = 1"  # 只显示1级鱼竿

        results = self.db.fetch_all(f"""
            SELECT rt.*,
                   COALESCE(srt.purchase_cost, rt.purchase_cost) as purchase_cost
            FROM rod_templates rt
            LEFT JOIN shop_rod_templates srt ON rt.id = srt.rod_template_id
            WHERE rt.source = 'shop' AND (srt.enabled = 1 OR srt.enabled IS NULL)
                  AND ({rarity_filter} OR rt.name = '新手木竿')
                  AND NOT (rt.name = '竹制鱼竿' AND ? < 3)
                  AND NOT (rt.name = '长者之竿' AND ? < 8)
                  AND NOT (rt.name = '冷静之竿' AND ? < 12)
                  AND NOT (rt.name = '碳素纤维竿' AND ? < 20)
            ORDER BY rt.rarity, rt.id
        """, (user_level, user_level, user_level, user_level))
        return [
            RodTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                source=row['source'],
                purchase_cost=row['purchase_cost'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                durability=row['durability'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_bait_shop_items(self, user_level: int = 1) -> List[BaitTemplate]:
        """获取鱼饵商店商品"""
        # 5级以下的用户无法看到鱼饵商品
        if user_level < 5:
            return []

        results = self.db.fetch_all("""
            SELECT bt.*,
                   COALESCE(sbt.cost, bt.cost) as cost
            FROM bait_templates bt
            LEFT JOIN shop_bait_templates sbt ON bt.id = sbt.bait_template_id
            WHERE sbt.enabled = 1 OR sbt.enabled IS NULL
            ORDER BY bt.rarity, bt.id
        """)
        return [
            BaitTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                cost=row['cost'],
                required_rod_rarity=row['required_rod_rarity'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=row['is_consumable']
            ) for row in results
        ]

    def get_accessory_shop_items(self) -> List[AccessoryTemplate]:
        """获取饰品商店商品"""
        results = self.db.fetch_all("""
            SELECT at.*,
                   COALESCE(sat.cost, at.cost) as cost
            FROM accessory_templates at
            LEFT JOIN shop_accessory_templates sat ON at.id = sat.accessory_template_id
            WHERE sat.enabled = 1 OR sat.enabled IS NULL
            ORDER BY at.rarity, at.id
        """)
        return [
            AccessoryTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                slot_type=row['slot_type'],
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                rare_mod=row['rare_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息"""
        result = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        if result:
            return User(
                user_id=result['user_id'],
                platform=result['platform'],
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

    def is_bait_system_unlocked(self, user_id: str) -> bool:
        """检查用户是否已解锁鱼饵系统"""
        # 先检查用户是否达到5级
        user = self.get_user(user_id)
        if user and user.level >= 5:
            return True

        # 再检查是否通过科技解锁
        result = self.db.fetch_one(
            """SELECT ut.id FROM user_technologies ut
               JOIN technologies t ON ut.tech_id = t.id
               WHERE ut.user_id = ? AND t.name = '鱼饵系统'""",
            (user_id,)
        )
        return result is not None

    def buy_bait(self, user_id: str, bait_id: int, quantity: int = 1) -> bool:
        """购买鱼饵"""
        # 检查用户是否已解锁鱼饵系统
        if not self.is_bait_system_unlocked(user_id):
            return False

        # 获取商店中的鱼饵信息
        bait_info = self.db.fetch_one("""
            SELECT bt.*, COALESCE(sbt.cost, bt.cost) as cost, sbt.stock
            FROM bait_templates bt
            LEFT JOIN shop_bait_templates sbt ON bt.id = sbt.bait_template_id
            WHERE bt.id = ? AND (sbt.enabled = 1 OR sbt.enabled IS NULL)
        """, (bait_id,))

        if not bait_info:
            return False

        # 检查库存是否足够（0表示无限库存）
        if bait_info['stock'] is not None and bait_info['stock'] > 0 and bait_info['stock'] < quantity:
            return False

        # 检查用户金币是否足够
        user = self.get_user(user_id)
        if not user or user.gold < bait_info['cost'] * quantity:
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (bait_info['cost'] * quantity, user_id)
        )

        # 减少库存（如果库存不为0）
        if bait_info['stock'] is not None and bait_info['stock'] > 0:
            self.db.execute_query(
                "UPDATE shop_bait_templates SET stock = stock - ? WHERE bait_template_id = ?",
                (quantity, bait_id)
            )

        # 检查是否已有该鱼饵库存
        existing_bait = self.db.fetch_one(
            "SELECT id, quantity FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ?",
            (user_id, bait_id)
        )

        if existing_bait:
            # 更新数量
            self.db.execute_query(
                "UPDATE user_bait_inventory SET quantity = quantity + ? WHERE id = ?",
                (quantity, existing_bait['id'])
            )
        else:
            # 添加新的鱼饵库存
            self.db.execute_query(
                """INSERT INTO user_bait_inventory
                   (user_id, bait_template_id, quantity)
                   VALUES (?, ?, ?)""",
                (user_id, bait_id, quantity)
            )

        return True

    def buy_accessory(self, user_id: str, accessory_id: int) -> bool:
        """购买饰品"""
        # 获取商店中的饰品信息
        accessory_info = self.db.fetch_one("""
            SELECT at.*, COALESCE(sat.cost, at.cost) as cost, sat.stock
            FROM accessory_templates at
            LEFT JOIN shop_accessory_templates sat ON at.id = sat.accessory_template_id
            WHERE at.id = ? AND (sat.enabled = 1 OR sat.enabled IS NULL)
        """, (accessory_id,))

        if not accessory_info:
            return False

        # 检查库存是否足够（0表示无限库存）
        if accessory_info['stock'] is not None and accessory_info['stock'] > 0 and accessory_info['stock'] < 1:
            return False

        # 检查用户金币是否足够
        user = self.get_user(user_id)
        if not user or user.gold < (accessory_info['cost'] or 0):
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (accessory_info['cost'], user_id)
        )

        # 减少库存（如果库存不为0）
        if accessory_info['stock'] is not None and accessory_info['stock'] > 0:
            self.db.execute_query(
                "UPDATE shop_accessory_templates SET stock = stock - 1 WHERE accessory_template_id = ?",
                (accessory_id,)
            )

        # 添加到用户饰品库存
        self.db.execute_query(
            """INSERT INTO user_accessory_instances
               (user_id, accessory_template_id, is_equipped, acquired_at)
               VALUES (?, ?, FALSE, ?)""",
            (user_id, accessory_id, int(time.time()))
        )

        return True

    def buy_rod(self, user_id: str, rod_id: int) -> bool:
        """购买鱼竿"""
        # 获取用户信息
        user = self.get_user(user_id)
        if not user:
            return False

        # 获取商店中的鱼竿信息
        rod_info = self.db.fetch_one("""
            SELECT rt.*, COALESCE(srt.purchase_cost, rt.purchase_cost) as purchase_cost, srt.stock
            FROM rod_templates rt
            LEFT JOIN shop_rod_templates srt ON rt.id = srt.rod_template_id
            WHERE rt.id = ? AND rt.source = 'shop' AND (srt.enabled = 1 OR srt.enabled IS NULL)
        """, (rod_id,))

        if not rod_info:
            return False

        # 检查等级限制
        # 竹制鱼竿需要用户达到3级才能购买
        if rod_info['name'] == '竹制鱼竿' and user.level < 3:
            return False
        # 长者之竿需要用户达到8级才能购买
        if rod_info['name'] == '长者之竿' and user.level < 8:
            return False
        # 冷静之竿需要用户达到12级才能购买
        if rod_info['name'] == '冷静之竿' and user.level < 12:
            return False
        # 碳素纤维竿需要用户达到20级才能购买
        if rod_info['name'] == '碳素纤维竿' and user.level < 20:
            return False

        # 检查库存是否足够（0表示无限库存）
        if rod_info['stock'] is not None and rod_info['stock'] > 0 and rod_info['stock'] < 1:
            return False

        # 检查用户金币是否足够
        if user.gold < (rod_info['purchase_cost'] or 0):
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (rod_info['purchase_cost'], user_id)
        )

        # 减少库存（如果库存不为0）
        if rod_info['stock'] is not None and rod_info['stock'] > 0:
            self.db.execute_query(
                "UPDATE shop_rod_templates SET stock = stock - 1 WHERE rod_template_id = ?",
                (rod_id,)
            )

        # 添加到用户鱼竿库存
        self.db.execute_query(
            """INSERT INTO user_rod_instances
               (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
               VALUES (?, ?, 1, 0, FALSE, ?, ?)""",
            (user_id, rod_id, int(time.time()), rod_info['durability'] or 0)
        )

        return True

    def equip_rod(self, user_id: str, rod_instance_id: int) -> bool:
        """装备鱼竿"""
        # 先取消当前装备的鱼竿
        self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )

        # 装备新的鱼竿
        result = self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
            (user_id, rod_instance_id)
        )
        return result is not None

    def get_equipped_rod(self, user_id: str) -> Optional[RodTemplate]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.*, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return RodTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                source=result['source'],
                purchase_cost=result['purchase_cost'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                durability=result['durability'],
                icon_url=result['icon_url'],
                level=result['level'],
                exp=result['exp'],
                is_equipped=result['is_equipped']
            )
        return None