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

# 说明：不在全局持有数据库连接，按请求使用上下文管理器获取连接


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000)
