from typing import Optional, List, Tuple
from ..models.user import User, FishInventory
from ..models.fishing import FishTemplate, RodTemplate, AccessoryTemplate, BaitTemplate, FishingResult
from ..models.database import DatabaseManager
import random
import time

class FishingService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._init_fish_templates()
        self._init_equipment_templates()

    def _init_fish_templates(self):
        """初始化鱼类模板数据"""
        # 检查是否已有数据
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM fish_templates")
        if result and result['count'] > 0:
            return

        # 插入默认鱼类模板
        fish_data = [
            ("小鲫鱼", 1, 10, "常见的小鲫鱼", 0.8),
            ("草鱼", 2, 25, "普通的草鱼", 0.6),
            ("鲤鱼", 2, 30, "金色的鲤鱼", 0.5),
            ("鲈鱼", 3, 50, "鲜美的鲈鱼", 0.4),
            ("石斑鱼", 3, 70, "海中的石斑鱼", 0.3),
            ("金枪鱼", 4, 120, "珍贵的金枪鱼", 0.2),
            ("鲨鱼", 5, 200, "凶猛的鲨鱼", 0.1),
        ]

        for name, rarity, base_value, description, catch_rate in fish_data:
            self.db.execute_query(
                "INSERT INTO fish_templates (name, rarity, base_value, description, catch_rate) VALUES (?, ?, ?, ?, ?)",
                (name, rarity, base_value, description, catch_rate)
            )

    def _init_equipment_templates(self):
        """初始化装备模板数据"""
        # 检查是否已有鱼竿数据
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM rod_templates")
        if not result or result['count'] == 0:
            # 插入默认鱼竿模板
            rod_data = [
                ("新手鱼竿", 1, "刚入门的鱼竿", 50, 1.0, 1.0),
                ("中级鱼竿", 2, "进阶钓鱼者的鱼竿", 150, 1.2, 1.1),
                ("高级鱼竿", 3, "专业钓鱼者的鱼竿", 300, 1.5, 1.3),
                ("专家鱼竿", 4, "大师级鱼竿", 600, 2.0, 1.5),
                ("传说鱼竿", 5, "传说中的神竿", 1200, 3.0, 2.0),
            ]

            for name, rarity, description, price, catch_bonus, weight_bonus in rod_data:
                self.db.execute_query(
                    "INSERT INTO rod_templates (name, rarity, description, price, catch_bonus, weight_bonus) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, rarity, description, price, catch_bonus, weight_bonus)
                )

        # 检查是否已有饰品数据
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM accessory_templates")
        if not result or result['count'] == 0:
            # 插入默认饰品模板
            accessory_data = [
                ("幸运吊坠", 2, "增加钓鱼幸运度", 100, "catch_rate", 0.1),
                ("力量手套", 3, "增加鱼竿力量", 200, "weight_bonus", 0.2),
                ("海洋之心", 4, "海洋的神秘力量", 500, "rare_fish_bonus", 0.15),
                ("海神之眼", 5, "洞察深海的宝物", 1000, "legendary_fish_bonus", 0.25),
            ]

            for name, rarity, description, price, effect_type, effect_value in accessory_data:
                self.db.execute_query(
                    "INSERT INTO accessory_templates (name, rarity, description, price, effect_type, effect_value) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, rarity, description, price, effect_type, effect_value)
                )

        # 检查是否已有鱼饵数据
        result = self.db.fetch_one("SELECT COUNT(*) as count FROM bait_templates")
        if not result or result['count'] == 0:
            # 插入默认鱼饵模板
            bait_data = [
                ("普通鱼饵", 1, "普通的鱼饵", 20, 1.2, 300),
                ("高级鱼饵", 2, "效果更好的鱼饵", 50, 1.5, 600),
                ("超级鱼饵", 3, "吸引力极强的鱼饵", 100, 2.0, 900),
                ("神秘鱼饵", 4, "来自深海的神秘鱼饵", 200, 2.5, 1200),
                ("传说鱼饵", 5, "传说中的鱼饵", 500, 3.0, 1800),
            ]

            for name, rarity, description, price, catch_rate_bonus, duration in bait_data:
                self.db.execute_query(
                    "INSERT INTO bait_templates (name, rarity, description, price, catch_rate_bonus, duration) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, rarity, description, price, catch_rate_bonus, duration)
                )

    def get_fish_templates(self) -> List[FishTemplate]:
        """获取所有鱼类模板"""
        results = self.db.fetch_all("SELECT * FROM fish_templates")
        return [
            FishTemplate(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                base_value=row['base_value'],
                description=row['description'],
                catch_rate=row['catch_rate']
            ) for row in results
        ]

    def get_rod_templates(self) -> List[RodTemplate]:
        """获取所有鱼竿模板"""
        results = self.db.fetch_all("SELECT * FROM rod_templates")
        return [
            RodTemplate(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                catch_bonus=row['catch_bonus'],
                weight_bonus=row['weight_bonus']
            ) for row in results
        ]

    def get_accessory_templates(self) -> List[AccessoryTemplate]:
        """获取所有饰品模板"""
        results = self.db.fetch_all("SELECT * FROM accessory_templates")
        return [
            AccessoryTemplate(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                effect_type=row['effect_type'],
                effect_value=row['effect_value']
            ) for row in results
        ]

    def get_bait_templates(self) -> List[BaitTemplate]:
        """获取所有鱼饵模板"""
        results = self.db.fetch_all("SELECT * FROM bait_templates")
        return [
            BaitTemplate(
                id=row['id'],
                name=row['name'],
                rarity=row['rarity'],
                description=row['description'],
                price=row['price'],
                catch_rate_bonus=row['catch_rate_bonus'],
                duration=row['duration']
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
            catch_rate_bonus *= equipped_rod.catch_bonus
        if equipped_accessory and equipped_accessory.effect_type == "catch_rate":
            catch_rate_bonus *= (1 + equipped_accessory.effect_value)

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
        weights = [fish.catch_rate for fish in fish_templates]
        caught_fish = random.choices(fish_templates, weights=weights)[0]

        # 计算鱼的重量和价值
        base_weight = random.uniform(0.5, 5.0)
        weight_bonus = 1.0
        if equipped_rod:
            weight_bonus *= equipped_rod.weight_bonus
        if equipped_accessory and equipped_accessory.effect_type == "weight_bonus":
            weight_bonus *= (1 + equipped_accessory.effect_value)

        final_weight = base_weight * weight_bonus
        final_value = int(caught_fish.base_value * (final_weight / 2.0))

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
                rarity=result['rarity'],
                description=result['description'],
                price=result['price'],
                catch_bonus=result['catch_bonus'],
                weight_bonus=result['weight_bonus']
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
                rarity=result['rarity'],
                description=result['description'],
                price=result['price'],
                effect_type=result['effect_type'],
                effect_value=result['effect_value']
            )
        return None