from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from routes import router  # 导入路由
from database import get_db_connection

# FastAPI 应用
app = FastAPI(title="My API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(router)

# 数据库连接(全局)
connection = get_db_connection()


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)
