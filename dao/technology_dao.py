"""
科技数据访问对象
"""
import json
import time
from typing import List, Optional
from ..models.tech import Technology, UserTechnology
from ..models.database import DatabaseManager
from .base_dao import BaseDAO


class TechnologyDAO(BaseDAO):
    """科技数据访问对象，封装所有科技相关的数据库操作"""

    def get_all_technologies(self) -> List[Technology]:
        """获取所有科技"""
        results = self.db.fetch_all("SELECT * FROM technologies ORDER BY id")
        technologies = []
        for row in results:
            tech = Technology(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                required_level=row['required_level'],
                required_gold=row['required_gold'],
                required_tech_ids=json.loads(row['required_tech_ids'] or "[]"),
                effect_type=row['effect_type'],
                effect_value=row['effect_value'],
                display_name=row['display_name']
            )
            technologies.append(tech)
        return technologies

    def get_user_technologies(self, user_id: str) -> List[UserTechnology]:
        """获取用户已解锁的科技"""
        results = self.db.fetch_all(
            "SELECT * FROM user_technologies WHERE user_id = ?",
            (user_id,)
        )
        return [
            UserTechnology(
                id=row['id'],
                user_id=row['user_id'],
                tech_id=row['tech_id'],
                unlocked_at=row['unlocked_at']
            ) for row in results
        ]

    def get_technology_by_id(self, tech_id: int) -> Optional[Technology]:
        """根据ID获取科技"""
        result = self.db.fetch_one(
            "SELECT * FROM technologies WHERE id = ?",
            (tech_id,)
        )
        if result:
            tech = Technology(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                required_level=result['required_level'],
                required_gold=result['required_gold'],
                required_tech_ids=json.loads(result['required_tech_ids'] or "[]"),
                effect_type=result['effect_type'],
                effect_value=result['effect_value'],
                display_name=result['display_name']
            )
            return tech
        return None

    def get_technology_by_name(self, name: str) -> Optional[Technology]:
        """根据名称获取科技"""
        result = self.db.fetch_one(
            "SELECT * FROM technologies WHERE name = ?",
            (name,)
        )
        if result:
            tech = Technology(
                id=result['id'],
                name=result['name'],
                description=result['description'],
                required_level=result['required_level'],
                required_gold=result['required_gold'],
                required_tech_ids=json.loads(result['required_tech_ids'] or "[]"),
                effect_type=result['effect_type'],
                effect_value=result['effect_value'],
                display_name=result['display_name']
            )
            return tech
        return None

    def is_technology_unlocked(self, user_id: str, tech_id: int) -> bool:
        """检查用户是否已解锁指定科技"""
        result = self.db.fetch_one(
            "SELECT id FROM user_technologies WHERE user_id = ? AND tech_id = ?",
            (user_id, tech_id)
        )
        return result is not None

    def unlock_technology(self, user_id: str, tech_id: int) -> bool:
        """解锁科技"""
        try:
            self.db.execute_query(
                """INSERT INTO user_technologies
                       (user_id, tech_id, unlocked_at)
                   VALUES (?, ?, ?)""",
                (user_id, tech_id, int(time.time()))
            )
            return True
        except Exception as e:
            print(f"解锁科技失败: {e}")
            return False