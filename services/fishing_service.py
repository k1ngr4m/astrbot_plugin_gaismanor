from typing import Optional, List, Tuple
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate, FishingResult
from ..models.database import DatabaseManager
import random
import time

class FishingService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_fish_templates(self) -> List[FishTemplate]:
        """获取所有鱼类模板"""
        results = self.db.fetch_all("SELECT * FROM fish_templates")
        return [
            FishTemplate(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                rarity=row['rarity'],
                base_value=row['base_value'],
                min_weight=row['min_weight'],
                max_weight=row['max_weight'],
                icon_url=row['icon_url']
            ) for row in results
        ]

    def get_rod_templates(self) -> List[RodTemplate]:
        """获取所有鱼竿模板"""
        results = self.db.fetch_all("SELECT * FROM rod_templates")
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

    def get_accessory_templates(self) -> List[AccessoryTemplate]:
        """获取所有饰品模板"""
        results = self.db.fetch_all("SELECT * FROM accessory_templates")
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

    def get_bait_templates(self) -> List[BaitTemplate]:
        """获取所有鱼饵模板"""
        results = self.db.fetch_all("SELECT * FROM bait_templates")
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

    def can_fish(self, user: User) -> Tuple[bool, str]:
        """检查用户是否可以钓鱼"""
        # 检查冷却时间 (默认3分钟)
        current_time = int(time.time())
        cooldown = 180  # 3分钟冷却时间
        if current_time - user.last_fishing_time < cooldown:
            remaining = cooldown - (current_time - user.last_fishing_time)
            return False, f"还在冷却中，请等待 {remaining} 秒后再钓鱼"

        # 检查金币 (默认10金币)
        if user.gold < 10:
            return False, "金币不足，无法钓鱼"

        return True, "可以钓鱼"

    def fish(self, user: User) -> FishingResult:
        """执行钓鱼操作"""
        # 检查是否可以钓鱼
        can_fish, message = self.can_fish(user)
        if not can_fish:
            return FishingResult(success=False, message=message)

        # 扣除钓鱼费用
        user.gold -= 10
        user.fishing_count += 1
        user.last_fishing_time = int(time.time())

        # 获取用户装备的鱼竿和饰品
        equipped_rod = self._get_equipped_rod(user.user_id)
        equipped_accessory = self._get_equipped_accessory(user.user_id)

        # 计算钓鱼成功率加成
        catch_rate_bonus = 1.0
        if equipped_rod:
            catch_rate_bonus *= equipped_rod.quality_mod
        if equipped_accessory and equipped_accessory.quality_mod:
            catch_rate_bonus *= equipped_accessory.quality_mod

        # 随机决定是否钓到鱼 (基础成功率50%)
        base_catch_rate = 0.5
        final_catch_rate = min(base_catch_rate * catch_rate_bonus, 0.95)  # 最高95%成功率

        if random.random() > final_catch_rate:
            # 钓鱼失败
            return FishingResult(success=False, message="这次没有钓到鱼，再试试看吧！")

        # 钓鱼成功，随机选择一种鱼
        fish_templates = self.get_fish_templates()
        if not fish_templates:
            return FishingResult(success=False, message="暂无鱼类数据")

        # 根据稀有度权重选择鱼类
        # 稀有度越高，权重越低（越难钓到）
        weights = [1.0 / (fish.rarity ** 2) for fish in fish_templates]
        caught_fish = random.choices(fish_templates, weights=weights)[0]

        # 计算鱼的重量和价值
        final_weight = random.uniform(caught_fish.min_weight / 1000.0, caught_fish.max_weight / 1000.0)
        final_value = int(caught_fish.base_value * (final_weight * 2))

        # 添加到用户鱼类库存
        self.db.execute_query(
            """INSERT INTO user_fish_inventory
               (user_id, fish_template_id, weight, value, caught_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user.user_id, caught_fish.id, final_weight, final_value, int(time.time()))
        )

        # 更新用户统计数据
        user.total_fish_weight += final_weight
        user.total_income += final_value
        user.gold += final_value

        # 记录钓鱼日志
        self.db.execute_query(
            """INSERT INTO fishing_logs
               (user_id, fish_template_id, fish_weight, fish_value, success, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user.user_id, caught_fish.id, final_weight, final_value, True, int(time.time()))
        )

        # 更新用户数据到数据库
        self.db.execute_query(
            """UPDATE users SET
                gold=?, fishing_count=?, last_fishing_time=?, total_fish_weight=?, total_income=?
                WHERE user_id=?""",
            (user.gold, user.fishing_count, user.last_fishing_time,
             user.total_fish_weight, user.total_income, user.user_id)
        )

        # 返回钓鱼结果
        message = f"恭喜！你钓到了一条 {caught_fish.name} ({caught_fish.description})\n重量: {final_weight:.2f}kg\n价值: {final_value}金币"
        return FishingResult(success=True, fish=caught_fish, weight=final_weight, value=final_value, message=message)

    def _get_equipped_rod(self, user_id: str) -> Optional[RodTemplate]:
        """获取用户装备的鱼竿"""
        result = self.db.fetch_one(
            """SELECT rt.* FROM user_rod_instances uri
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
                icon_url=result['icon_url']
            )
        return None

    def _get_equipped_accessory(self, user_id: str) -> Optional[AccessoryTemplate]:
        """获取用户装备的饰品"""
        result = self.db.fetch_one(
            """SELECT at.* FROM user_accessory_instances uai
               JOIN accessory_templates at ON uai.accessory_template_id = at.id
               WHERE uai.user_id = ? AND uai.is_equipped = TRUE""",
            (user_id,)
        )
        if result:
            return AccessoryTemplate(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                rarity=result['rarity'],
                slot_type=result['slot_type'],
                quality_mod=result['quality_mod'],
                quantity_mod=result['quantity_mod'],
                rare_mod=result['rare_mod'],
                coin_mod=result['coin_mod'],
                other_desc=result['other_desc'],
                icon_url=result['icon_url']
            )
        return None