from typing import Optional, List

from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate
from ..models.database import DatabaseManager
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
/购买鱼饵 <ID> [数量]  - 购买指定ID的鱼饵
/购买鱼竿 <ID>  - 购买指定ID的鱼竿
/使用鱼饵 <ID>  - 使用指定ID的鱼饵
/使用鱼竿 <ID>  - 装备指定ID的鱼竿
"""
        yield event.plain_result(shop_info)

    async def shop_rods_command(self, event: AstrMessageEvent):
        """查看鱼竿商店商品"""
        rods = self.get_rod_shop_items()

        if not rods:
            yield event.plain_result("暂无鱼竿商品")
            return

        rod_info = "=== 鱼竿商店 ===\n"
        for rod in rods:
            rarity_stars = "★" * rod.rarity + "☆" * (5 - rod.rarity)
            rod_info += f"ID: {rod.id} - {rod.name} {rarity_stars}\n"
            rod_info += f"  价格: {rod.purchase_cost}金币  品质加成: +{rod.quality_mod}  数量加成: +{rod.quantity_mod}\n"
            rod_info += f"  描述: {rod.description}\n\n"

        yield event.plain_result(rod_info)

    async def shop_bait_command(self, event: AstrMessageEvent):
        """查看鱼饵商店商品"""
        bait_list = self.get_bait_shop_items()

        if not bait_list:
            yield event.plain_result("暂无鱼饵商品")
            return

        bait_info = "=== 鱼饵商店 ===\n"
        for bait in bait_list:
            rarity_stars = "★" * bait.rarity + "☆" * (5 - bait.rarity)
            bait_info += f"ID: {bait.id} - {bait.name} {rarity_stars}\n"
            bait_info += f"  价格: {bait.cost}金币  效果: {bait.effect_description}\n"
            bait_info += f"  描述: {bait.description}\n\n"

        yield event.plain_result(bait_info)

    async def buy_bait_command(self, event: AstrMessageEvent, bait_id: int, quantity: int = 1):
        """购买鱼饵"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买鱼饵
        success = self.buy_bait(user_id, bait_id, quantity)

        if success:
            bait_template = self.db.fetch_one(
                "SELECT name FROM bait_templates WHERE id = ?",
                (bait_id,)
            )
            bait_name = bait_template['name'] if bait_template else "未知鱼饵"
            yield event.plain_result(f"成功购买鱼饵: {bait_name} x{quantity}")
        else:
            yield event.plain_result("购买鱼饵失败，请检查金币是否足够或商品是否存在")

    async def buy_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """购买鱼竿"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 购买鱼竿
        success = self.buy_rod(user_id, rod_id)

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功购买鱼竿: {rod_name}")
        else:
            yield event.plain_result("购买鱼竿失败，请检查金币是否足够或商品是否存在")

    async def use_bait_command(self, event: AstrMessageEvent, bait_id: int):
        """使用鱼饵命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼饵是否存在
        bait_instance = self.db.fetch_one(
            "SELECT * FROM user_bait_inventory WHERE user_id = ? AND bait_template_id = ? AND quantity > 0",
            (user_id, bait_id)
        )

        if not bait_instance:
            yield event.plain_result("您没有该鱼饵或数量不足")
            return

        # 使用鱼饵（这里简化处理，实际应该应用鱼饵效果）
        yield event.plain_result("鱼饵使用功能正在开发中，敬请期待！")

    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """装备鱼竿命令"""
        user_id = event.get_sender_id()
        user = self.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 检查鱼竿是否存在
        rod_instance = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND rod_template_id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("您没有该鱼竿")
            return

        # 装备鱼竿
        success = self.equip_rod(user_id, rod_instance['id'])

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_id,)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功装备鱼竿: {rod_name}")
        else:
            yield event.plain_result("装备鱼竿失败")

    def get_rod_shop_items(self) -> List[RodTemplate]:
        """获取鱼竿商店商品"""
        results = self.db.fetch_all(
            "SELECT * FROM rod_templates WHERE source = 'shop' ORDER BY rarity, id"
        )
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

    def get_bait_shop_items(self) -> List[BaitTemplate]:
        """获取鱼饵商店商品"""
        results = self.db.fetch_all(
            "SELECT * FROM bait_templates ORDER BY rarity, id"
        )
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

    def buy_bait(self, user_id: str, bait_id: int, quantity: int = 1) -> bool:
        """购买鱼饵"""
        # 获取鱼饵模板信息
        bait_template = self.db.fetch_one(
            "SELECT * FROM bait_templates WHERE id = ?",
            (bait_id,)
        )
        if not bait_template:
            return False

        # 检查用户金币是否足够
        user = self.get_user(user_id)
        if not user or user.gold < bait_template['cost'] * quantity:
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (bait_template['cost'] * quantity, user_id)
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

    def buy_rod(self, user_id: str, rod_id: int) -> bool:
        """购买鱼竿"""
        # 获取鱼竿模板信息
        rod_template = self.db.fetch_one(
            "SELECT * FROM rod_templates WHERE id = ?",
            (rod_id,)
        )
        if not rod_template:
            return False

        # 检查用户金币是否足够
        user = self.get_user(user_id)
        if not user or user.gold < (rod_template['purchase_cost'] or 0):
            return False

        # 扣除金币
        self.db.execute_query(
            "UPDATE users SET gold = gold - ? WHERE user_id = ?",
            (rod_template['purchase_cost'], user_id)
        )

        # 添加到用户鱼竿库存
        self.db.execute_query(
            """INSERT INTO user_rod_instances
               (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
               VALUES (?, ?, 1, 0, FALSE, ?, ?)""",
            (user_id, rod_id, int(time.time()), rod_template['durability'] or 0)
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