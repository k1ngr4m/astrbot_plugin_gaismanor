"""
数据访问对象基类
"""
from ..models.database import DatabaseManager


class BaseDAO:
    """数据访问对象基类，提供通用的数据库操作方法"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager