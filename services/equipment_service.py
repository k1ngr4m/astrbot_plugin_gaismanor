from typing import Optional, List
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
import time
import logging

logger = logging.getLogger(__name__)

class EquipmentService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_user_rods(self, user_id: str) -> List[Rod]:
        """获取用户所有鱼竿"""
        results = self.db.fetch_all(
            """SELECT rt.*, uri.id as instance_id, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ?""",
            (user_id,)
        )
        return [
        Rod(
                id=row['instance_id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['purchase_cost'] or 0,
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                durability=row['durability'] or 0,
                level=row['level'],
                exp=row['exp'],
                is_equipped=bool(row['is_equipped'])
            ) for row in results
        ]

    def get_user_accessories(self, user_id: str) -> List[Accessory]:
        """获取用户所有饰品"""
        results = self.db.fetch_all(
            """SELECT at.*, uai.is_equipped FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ?""",
            (user_id,)
        )
        return [
            Accessory(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=100,  # 默认价格
                quality_mod=row['quality_mod'],
                quantity_mod=row['quantity_mod'],
                coin_mod=row['coin_mod'],
                other_desc=row['other_desc'],
                is_equipped=bool(row['is_equipped'])
            ) for row in results
        ]

    def get_user_bait(self, user_id: str) -> List[Bait]:
        """获取用户所有鱼饵"""
        results = self.db.fetch_all(
            """SELECT bt.*, ubi.quantity FROM user_bait_inventory ubi
               JOIN bait_templates bt ON ubi.bait_template_id = bt.id
               WHERE ubi.user_id = ?""",
            (user_id,)
        )
        return [
            Bait(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['cost'],
                effect_description=row['effect_description'],
                duration_minutes=row['duration_minutes'],
                success_rate_modifier=row['success_rate_modifier'],
                rare_chance_modifier=row['rare_chance_modifier'],
                garbage_reduction_modifier=row['garbage_reduction_modifier'],
                value_modifier=row['value_modifier'],
                quantity_modifier=row['quantity_modifier'],
                is_consumable=bool(row['is_consumable']),
                quantity=row['quantity']
            ) for row in results
        ]

    def equip_rod(self, user_id: str, rod_id: int) -> bool:
        """装备鱼竿"""
        # 先取消当前装备的鱼竿
        self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )

        # 装备新的鱼竿
        result = self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )
        # execute_query方法不返回结果，我们通过检查影响的行数来判断是否成功
        # 这里假设如果能执行到这一步，就认为是成功的
        return True

    def equip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """装备饰品"""
        # 先取消当前装备的饰品
        self.db.execute_query(
            "UPDATE user_accessory_instances SET is_equipped = FALSE WHERE user_id = ? AND is_equipped = TRUE",
            (user_id,)
        )

        # 装备新的饰品
        result = self.db.execute_query(
            "UPDATE user_accessory_instances SET is_equipped = TRUE WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )
        # execute_query方法不返回结果，我们通过检查影响的行数来判断是否成功
        # 这里假设如果能执行到这一步，就认为是成功的
        return True

    def unequip_rod(self, user_id: str, rod_id: int) -> bool:
        """卸下鱼竿"""
        # 首先检查鱼竿是否存在且确实被装备
        rod_check = self.db.fetch_one(
            "SELECT id FROM user_rod_instances WHERE user_id = ? AND id = ? AND is_equipped = TRUE",
            (user_id, rod_id)
        )
        if not rod_check:
            return False

        # 执行卸下操作
        self.db.execute_query(
            "UPDATE user_rod_instances SET is_equipped = FALSE WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )

        return True

    def unequip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """卸下饰品"""
        self.db.execute_query(
            "UPDATE user_accessory_instances SET is_equipped = FALSE WHERE user_id = ? AND id = ?",
            (user_id, accessory_id)
        )
        # execute_query方法不返回结果，我们通过检查影响的行数来判断是否成功
        # 这里假设如果能执行到这一步，就认为是成功的
        return True

    def get_equipped_rod(self, user_id: str) -> Optional[Rod]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT uri.id as instance_id, rt.*, uri.level, uri.exp, uri.is_equipped, uri.durability FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return Rod(
                id=result['instance_id'],
                name=result['name'],
                rarity=result['rarity'],
                description=result['description'],
                price=result['purchase_cost'] or 0,
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                durability=result['durability'] or 0,
                level=result['level'],
                exp=result['exp'],
                is_equipped=bool(result['is_equipped'])
            )
        return None

    def get_equipped_accessory(self, user_id: str) -> Optional[Accessory]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.*, uai.is_equipped FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return Accessory(
                id=result['id'],
                name=result['name'],
                rarity=result['rarity'],
                description=result['description'],
                price=100,  # 默认价格
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                coin_mod=result['coin_mod'],
                other_desc=result['other_desc'],
                is_equipped=bool(result['is_equipped'])
            )
        return None

    async def rod_command(self, event: AstrMessageEvent):
        """鱼竿命令"""
        user_id = event.get_sender_id()
        # 获取用户鱼竿库存
        rods = self.get_user_rods(user_id)

        if not rods:
            yield event.plain_result("您的鱼竿背包是空的，快去商店购买一些鱼竿吧！")
            return

        # 构建鱼竿信息
        rod_info = "=== 您的鱼竿背包 ===\n"
        for i, rod in enumerate(rods, 1):
            rarity_stars = "★" * rod.rarity
            equip_status = " [装备中]" if rod.is_equipped else ""
            # 显示耐久度信息
            durability_info = f"  耐久度: {rod.durability}" if rod.durability > 0 else "  耐久度: ∞" if rod.durability == 0 else "  耐久度: 已损坏"
            rod_info += f"{i}. {rod.name} {rarity_stars} - 等级:{rod.level} - 经验:{rod.exp} (ID: {rod.id}){equip_status}\n"
            rod_info += f"   品质加成: +{rod.quality_mod}  数量加成: +{rod.quantity_mod}{durability_info}\n\n"

        yield event.plain_result(rod_info)

    async def use_rod_command(self, event: AstrMessageEvent, rod_id: int):
        """使用/装备鱼竿命令"""
        user_id = event.get_sender_id()

        # 检查鱼竿是否存在
        rod_instance = self.db.fetch_one(
            "SELECT * FROM user_rod_instances WHERE user_id = ? AND id = ?",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到指定的鱼竿")
            return

        # 装备鱼竿
        success = self.equip_rod(user_id, rod_id)

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_instance['rod_template_id'],)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"成功装备鱼竿: {rod_name}")
        else:
            yield event.plain_result("装备鱼竿失败")

    async def unequip_rod_command(self, event: AstrMessageEvent):
        """卸下鱼竿命令"""
        user_id = event.get_sender_id()

        # 获取当前装备的鱼竿
        equipped_rod = self.get_equipped_rod(user_id)

        if not equipped_rod:
            yield event.plain_result("您当前没有装备任何鱼竿")
            return

        # 卸下鱼竿
        success = self.unequip_rod(user_id, equipped_rod.id)

        if success:
            yield event.plain_result(f"成功卸下鱼竿: {equipped_rod.name}")
        else:
            yield event.plain_result("卸下鱼竿失败，可能鱼竿已被卸下或不存在")

    async def repair_rod_command(self, event: AstrMessageEvent, rod_id: int = None):
        """维修鱼竿命令"""
        user_id = event.get_sender_id()

        # 如果没有指定鱼竿ID，则显示需要指定鱼竿ID的提示
        if rod_id is None:
            yield event.plain_result("请指定要维修的鱼竿ID。使用 /鱼竿 命令查看您的鱼竿列表和对应的ID。")
            return

        # 获取用户信息
        from ..services.user_service import UserService
        user_service = UserService(self.db)
        user = user_service.get_user(user_id)

        if not user:
            yield event.plain_result("您还未注册，请先使用 /注册 命令注册账号")
            return

        # 获取指定的鱼竿
        rod_instance = self.db.fetch_one(
            """SELECT uri.*, rt.name as rod_name, rt.rarity as rod_rarity, rt.durability as max_durability
               FROM user_rod_instances uri
               JOIN rod_templates rt ON uri.rod_template_id = rt.id
               WHERE uri.user_id = ? AND uri.id = ?""",
            (user_id, rod_id)
        )

        if not rod_instance:
            yield event.plain_result("未找到指定的鱼竿，请检查鱼竿ID是否正确")
            return

        # 检查鱼竿是否已损坏（耐久度为0）
        if rod_instance['durability'] > 0:
            yield event.plain_result(f"鱼竿 [{rod_instance['rod_name']}] 未损坏，无需维修")
            return

        # 检查鱼竿是否有最大耐久度限制
        if rod_instance['max_durability'] is None:
            yield event.plain_result(f"鱼竿 [{rod_instance['rod_name']}] 无需维修")
            return

        # 计算维修费用（根据鱼竿稀有度计算）
        repair_cost = rod_instance['rod_rarity'] * 100  # 1星100金币，2星200金币，以此类推

        # 检查金币是否足够
        if user.gold < repair_cost:
            yield event.plain_result(f"金币不足！维修需要 {repair_cost} 金币，您当前只有 {user.gold} 金币。")
            return

        # 扣除金币并恢复耐久度
        user.gold -= repair_cost
        user_service.update_user(user)

        # 恢复鱼竿耐久度到最大值
        self.db.execute_query(
            "UPDATE user_rod_instances SET durability = ? WHERE id = ?",
            (rod_instance['max_durability'], rod_id)
        )

        yield event.plain_result(f"鱼竿 [{rod_instance['rod_name']}] 维修成功！\n消耗金币: {repair_cost}\n当前耐久度: {rod_instance['max_durability']}")

    def give_rod_to_user(self, user_id: str, rod_template_id: int) -> bool:
        """给用户发放指定模板的鱼竿"""
        try:
            # 获取鱼竿模板信息
            rod_template = self.db.fetch_one(
                "SELECT * FROM rod_templates WHERE id = ?",
                (rod_template_id,)
            )

            if not rod_template:
                return False

            # 获取当前时间
            current_time = int(time.time())

            # 插入用户鱼竿实例
            self.db.execute_query(
                """INSERT INTO user_rod_instances
                   (user_id, rod_template_id, level, exp, is_equipped, acquired_at, durability)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, rod_template_id, 1, 0, False, current_time, rod_template['durability'])
            )

            return True
        except Exception as e:
            logger.error(f"发放鱼竿给用户失败: {e}")
            return False
