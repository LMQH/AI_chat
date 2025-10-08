import os
import pymysql
from pymysql import Error
from dotenv import load_dotenv
from contextlib import contextmanager


# 加载环境变量
load_dotenv()

# 创建数据库连接,使用上下文管理器
@contextmanager
def get_db_connection():
    connection = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            connection = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER"),
                port=int(os.getenv("DB_PORT", 3306)),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=30,  # 增加连接超时时间
                read_timeout=30,     # 增加读取超时时间
                write_timeout=30,    # 增加写入超时时间
                # 移除不兼容的参数
            )
            # 强制设置本次连接使用 utf8mb4，避免 1366 错误
            try:
                with connection.cursor() as _c:
                    _c.execute("SET NAMES utf8mb4")
                    _c.execute("SET character_set_connection = utf8mb4")
                    _c.execute("SET collation_connection = utf8mb4_unicode_ci")
                    # 设置会话超时
                    _c.execute("SET SESSION wait_timeout = 28800")
                    _c.execute("SET SESSION interactive_timeout = 28800")
            except Exception as _:
                pass
            print("成功连接到MySQL数据库")
            yield connection
            break  # 成功连接，跳出重试循环
            
        except Exception as e:
            retry_count += 1
            print(f"数据库连接错误 (尝试 {retry_count}/{max_retries}): {e}")
            if connection:
                try:
                    connection.rollback()
                    connection.close()
                except:
                    pass
                connection = None
            
            if retry_count >= max_retries:
                print(f"数据库连接失败，已重试 {max_retries} 次")
                raise
            else:
                import time
                time.sleep(1)  # 等待1秒后重试


# 测试连接
if __name__ == "__main__":
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("数据库可访问:", cursor.fetchone())
    except Exception as e:
        print("测试失败:", e)