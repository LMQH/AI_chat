import pymysql
from pymysql import Error


def create_connection():
    """创建数据库连接"""
    try:
        connection = pymysql.connect(
            host="localhost",
            user="user",
            port=3306,
            password="123456",
            database="ai_project",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        print("成功连接到MySQL数据库")
        return connection
    except Error as e:
        print(f"连接错误: {e}")
        return None
