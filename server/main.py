from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path

from routes import router  # 导入路由

# FastAPI 应用
app = FastAPI(title="My API", version="1.0.0")

# CORS，允许所有源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源（使用绝对路径，若不存在则创建）
_static_dir = Path(__file__).parent / "static"
_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# 注册路由
app.include_router(router)


if __name__ == "__main__":
    print("正在启动 AI 聊天系统...")
    
    # 1. 首先测试数据库连接
    print("检查数据库连接...")
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请检查数据库配置和环境变量")
        exit(1)
    
    # 2. 数据库连接正常后，再检查RAG
    print("检查RAG向量数据库...")
    try:
        from rag_service import check_and_initialize_vector_db
        vector_db_success = check_and_initialize_vector_db()
        
        if vector_db_success:
            print("✅ 向量数据库准备就绪，RAG 功能可用")
        else:
            print("⚠️  向量数据库初始化失败，将使用基础 LLM 功能")
    except Exception as e:
        print(f"⚠️  向量数据库检查异常: {e}")
        print("系统将使用基础 LLM 功能继续运行")

    # 3. 启动服务器
    print("🌐 启动 FastAPI 服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
