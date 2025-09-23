from typing import Optional, List
from astrbot.api.event import AstrMessageEvent
from ..models.user import User
from ..models.equipment import Rod, Accessory, Bait
from ..models.database import DatabaseManager
from ..dao.equipment_dao import EquipmentDAO
from ..enums.messages import Messages
import time
import logging

logger = logging.getLogger(__name__)

class EquipmentService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.equipment_dao = EquipmentDAO(db_manager)

    def get_user_rods(self, user_id: str) -> List[Rod]:
        """获取用户所有鱼竿"""
        results = self.equipment_dao.get_user_rods(user_id)
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
        results = self.equipment_dao.get_user_accessories(user_id)
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
        results = self.equipment_dao.get_user_bait(user_id)
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
        return self.equipment_dao.equip_rod(user_id, rod_id)

    def equip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """装备饰品"""
        return self.equipment_dao.equip_accessory(user_id, accessory_id)

    def unequip_rod(self, user_id: str) -> bool:
        """卸下鱼竿"""
        return self.equipment_dao.unequip_rod(user_id)

    def unequip_accessory(self, user_id: str, accessory_id: int) -> bool:
        """卸下饰品"""
        return self.equipment_dao.unequip_accessory(user_id, accessory_id)

    def get_equipped_rod(self, user_id: str) -> Optional[Rod]:
        """获取用户装备的鱼竿"""
        result = self.equipment_dao.get_equipped_rod(user_id)
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
        # 先获取数据
        results = self.equipment_dao.get_user_accessories(user_id)
        # 筛选已装备的饰品
        equipped_accessories = [row for row in results if row.get('is_equipped')]

        if equipped_accessories:
            result = equipped_accessories[0]
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
            yield event.plain_result(Messages.INVENTORY_NO_RODS.value)
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
            yield event.plain_result(Messages.EQUIPMENT_ROD_NOT_FOUND.value)
            return

        # 装备鱼竿
        success = self.equip_rod(user_id, rod_id)

        if success:
            rod_template = self.db.fetch_one(
                "SELECT name FROM rod_templates WHERE id = ?",
                (rod_instance['rod_template_id'],)
            )
            rod_name = rod_template['name'] if rod_template else "未知鱼竿"
            yield event.plain_result(f"{Messages.EQUIPMENT_ROD_EQUIP_SUCCESS.value}: {rod_name}")
        else:
            yield event.plain_result(Messages.EQUIPMENT_ROD_EQUIP_FAILED.value)

    async def unequip_rod_command(self, event: AstrMessageEvent):
        """卸下鱼竿命令"""
        user_id = event.get_sender_id()

        # 获取当前装备的鱼竿
        equipped_rod = self.get_equipped_rod(user_id)

        if not equipped_rod:
            yield event.plain_result(Messages.EQUIPMENT_ROD_NOT_EQUIPPED.value)
            return

        # 卸下鱼竿
        success = self.unequip_rod(user_id)

        if success:
            yield event.plain_result(f"{Messages.EQUIPMENT_ROD_UNEQUIP_SUCCESS.value}: {equipped_rod.name}")
        else:
            yield event.plain_result(Messages.EQUIPMENT_ROD_UNEQUIP_FAILED.value)

    async def repair_rod_command(self, event: AstrMessageEvent, rod_id: int = None):
        """维修鱼竿命令"""
        user_id = event.get_sender_id()

        # 如果没有指定鱼竿ID，则显示需要指定鱼竿ID的提示
        if rod_id is None:
            yield event.plain_result(Messages.EQUIPMENT_ROD_REPAIR_NO_ID.value)
            return

        # 获取用户信息
        from ..services.user_service import UserService
        user_service = UserService(self.db)
        user = user_service.get_user(user_id)

        if not user:
            yield event.plain_result(Messages.NOT_REGISTERED.value)
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
            yield event.plain_result(Messages.EQUIPMENT_ROD_REPAIR_NOT_FOUND.value)
            return

        # 检查鱼竿是否已损坏（耐久度为0）
        if rod_instance['durability'] > 0:
            yield event.plain_result(f"{Messages.EQUIPMENT_ROD_REPAIR_NOT_DAMAGED.value}，无需维修")
            return

        # 检查鱼竿是否有最大耐久度限制
        if rod_instance['max_durability'] is None:
            yield event.plain_result(f"{Messages.EQUIPMENT_ROD_REPAIR_NOT_NEEDED.value}，无需维修")
            return

        # 计算维修费用（根据鱼竿稀有度计算）
        repair_cost = rod_instance['rod_rarity'] * 100  # 1星100金币，2星200金币，以此类推

        # 检查金币是否足够
        if user.gold < repair_cost:
            yield event.plain_result(f"{Messages.EQUIPMENT_ROD_REPAIR_NOT_ENOUGH_GOLD.value}，您当前只有 {user.gold} 金币。")
            return

        # 扣除金币并恢复耐久度
        user.gold -= repair_cost
        user_service.update_user(user)

        # 恢复鱼竿耐久度到最大值
        self.db.execute_query(
            "UPDATE user_rod_instances SET durability = ? WHERE id = ?",
            (rod_instance['max_durability'], rod_id)
        )

        yield event.plain_result(f"{Messages.EQUIPMENT_ROD_REPAIR_SUCCESS.value}\n消耗金币: {repair_cost}\n当前耐久度: {rod_instance['max_durability']}")

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
