import json
import os

import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB
from contextlib import contextmanager
from typing import List, Sequence
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_CACHE = None

def _config():
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        config_path = os.path.join(BASE_DIR, '..', 'config', 'config.json')
        with(open(config_path, 'r')) as config_file:
            _CONFIG_CACHE = json.load(config_file)["database"]
    return _CONFIG_CACHE

class MySQLPool:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            cls._pool = PooledDB(
                creator=pymysql,
                maxconnections=10,
                host=_config()["host"],
                port=_config()["port"],
                user=_config()["user"],
                password=_config()["password"],
                database=_config()["database"],
                charset='utf8mb4',
                cursorclass=DictCursor,
            )
        return cls._pool

    @classmethod
    @contextmanager
    def get_conn(cls):
        pool = cls.get_pool()
        conn = pool.connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

class MySQLChatMessageHistory(BaseChatMessageHistory):
    """将多轮对话历史持久化到 MySQL 表中，每轮消息存为一行"""
    def __init__(self, session_id: str):
        super().__init__()
        self.session_id = session_id

    @property
    def messages(self) -> List[BaseMessage]:
        """从数据库按插入顺序读取该 session 的所有消息"""
        with MySQLPool.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT role, content FROM chat_history "
                    "WHERE session_id = %s ORDER BY id ASC",
                    (self.session_id,)
                )
                rows = cursor.fetchall()

        msgs = []
        for row in rows:
            role = row['role']
            content = row['content']
            if role == 'human':
                msgs.append(HumanMessage(content=content))
            elif role == 'ai':
                msgs.append(AIMessage(content=content))
            # 如有 system 等角色可在此扩展
        return msgs

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """批量插入多条消息（单次数据库写入）"""
        if not messages:
            return
        # 准备批量数据
        values = [(self.session_id, msg.type, msg.content) for msg in messages]
        with MySQLPool.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    "INSERT INTO chat_history (session_id, role, content) "
                    "VALUES (%s, %s, %s)",
                    values
                )

    def clear(self) -> None:
        """清空当前 session 的所有历史"""
        with MySQLPool.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM chat_history WHERE session_id = %s",
                    (self.session_id,)
                )

if __name__ == '__main__':
    print(_config())
    print(MySQLChatMessageHistory("001"))