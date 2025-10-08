from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from pathlib import Path
import mimetypes
import os
from uuid import uuid4

from database import get_db_connection
from llm_utils import llm_stream, llm
from rag_service import get_rag_status

router = APIRouter()


# 内部工具：保存上传文件并返回 URL
async def _save_upload(img1: UploadFile) -> JSONResponse:
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    allowed = {"image/png", "image/jpeg", "image/webp", "application/pdf", "application/zip",
               "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if img1.content_type and img1.content_type not in allowed:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    suffix = Path(img1.filename).suffix or ""
    safe_name = f"{uuid4().hex}{suffix}"
    dst = static_dir / safe_name
    content = await img1.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大，超过10MB")
    with open(dst, "wb") as f:
        f.write(content)
    return JSONResponse({"img": f"/static/{safe_name}"}, status_code=200, headers={"Cache-Control": "no-store"})


# 测试路由
@router.get("/test1")
def test1():
    return {"message": "Hello, World!"}


# 测试路由，测试参数
@router.get("/test2")
def test2(count: int, chat_text: str):
    return {"count": count, "chat_text": chat_text}


# 定义模型
class Mydata(BaseModel):
    count: str
    chat_text: str


# 测试路由，测试参数
@router.post("/test3")
def test3(data: Mydata):
    return {"data": data}


# 上传文件
@router.post("/upload")
async def upload_lower(img1: UploadFile):
    try:
        return await _save_upload(img1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")


# 简单聊天
@router.get("/chat")
def chat(text: str):
    try:
        ai_content = llm(text)
        return {"code": 2000, "content": ai_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {e}")


# 提取主题（去除非文本字符）
def extract_clean_title(raw_title: str) -> str:
    """清理 LLM 返回的主题，只保留纯文本"""
    return raw_title.strip().strip('\"\'').replace('\n', '').replace('\r', '')[:100]


# 流式对话
@router.get("/stream")
def stream(text: str, subjectid: int):
    try:
        # 确保subjectid有效
        final_subjectid = subjectid
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 如果是新对话，创建主题
                    if subjectid == 0:
                        raw_title = llm(f"用户的对话内容是:{text},请帮我生成一个对话主题,要求概括对话内容，只返回主题文字,文字越少越好")
                        title = extract_clean_title(raw_title)

                        # 插入主题
                        insert_subject_sql = "INSERT INTO subject (title) VALUES (%s)"
                        cursor.execute(insert_subject_sql, (title,))
                        final_subjectid = cursor.lastrowid
                        
                        # 验证主题是否创建成功
                        if final_subjectid == 0:
                            cursor.execute("SELECT id FROM subject WHERE title = %s ORDER BY id DESC LIMIT 1", (title,))
                            result = cursor.fetchone()
                            if result:
                                final_subjectid = result['id']

                        # 保存用户消息（事务内）
                        insert_chat_sql = "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                        cursor.execute(insert_chat_sql, (final_subjectid, text, "user"))

                        conn.commit()  # 提交事务
                        print(f"用户消息已保存，subjectid: {final_subjectid}")

                    else:
                        # 验证现有主题是否存在
                        cursor.execute("SELECT id FROM subject WHERE id = %s", (subjectid,))
                        if not cursor.fetchone():
                            print(f"主题ID {subjectid} 不存在，创建新主题")
                            raw_title = llm(f"用户的对话内容是:{text},请帮我生成一个对话主题,只返回主题文字")
                            title = extract_clean_title(raw_title)
                            cursor.execute("INSERT INTO subject (title) VALUES (%s)", (title,))
                            final_subjectid = cursor.lastrowid
                        
                        # 保存用户消息
                        insert_chat_sql = "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                        cursor.execute(insert_chat_sql, (final_subjectid, text, "user"))
                        conn.commit()
                        print(f"用户消息已保存，subjectid: {final_subjectid}")
                        
        except Exception as db_err:
            # 不中断流式对话，记录错误并继续
            print(f"用户消息入库失败: {db_err}")
            # 如果数据库操作失败，使用默认subjectid
            if final_subjectid == 0:
                final_subjectid = 1  # 使用默认主题ID

        # 流式返回 AI 回复（llm_stream 内部会保存 AI 回复）
        return StreamingResponse(
            llm_stream(text, final_subjectid),
            media_type="text/plain"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式对话失败: {e}")


# 获取主题
@router.get("/get_subject")
def get_subject():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT id, title, created_at FROM subject ORDER BY created_at DESC"
                cursor.execute(sql)
                return cursor.fetchall()
    except Exception as e:
        # 回退逻辑：兼容历史表结构缺少 created_at 的情况
        print(f"获取主题失败（将启用回退查询）：{e}")
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, title FROM subject ORDER BY id DESC")
                    rows = cursor.fetchall()
                    # 补齐 created_at 字段，避免前端取值报错
                    for r in rows:
                        if "created_at" not in r:
                            r["created_at"] = None
                    return rows
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"获取主题失败: {e2}")


# 获取主题下的聊天记录
@router.get("/get_chatcontent_at_subjectid")
def get_chatcontent_at_subjectid(subjectid: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 使用参数化查询防止注入
                sql = "SELECT * FROM chatcontent WHERE subjectid = %s ORDER BY id LIMIT 20"
                cursor.execute(sql, (subjectid,))
                return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天记录失败: {e}")


# 删除主题（兼容未启用 ON DELETE CASCADE 的环境）
@router.delete("/subject/{subject_id}")
def delete_subject(subject_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 先删除子表，避免 1451 外键约束错误
                cursor.execute("DELETE FROM chatcontent WHERE subjectid = %s", (subject_id,))
                # 再删除父表
                cursor.execute("DELETE FROM subject WHERE id = %s", (subject_id,))
                conn.commit()
                return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除主题失败: {e}")

# RAG 状态检查接口
@router.get("/rag_status")
def rag_status():
    """获取 RAG 服务状态"""
    try:
        status = get_rag_status()
        return status
    except Exception as e:
        return {"error": f"获取 RAG 状态失败: {e}"}

# 向量数据库管理接口
@router.get("/vector_db_info")
def vector_db_info():
    """获取向量数据库信息"""
    try:
        from rag_service import get_rag_service
        service = get_rag_service()
        info = service.get_vector_db_info()
        return info
    except Exception as e:
        return {"error": f"获取向量数据库信息失败: {e}"}

# 重建向量数据库接口
@router.post("/rebuild_vector_db")
def rebuild_vector_db():
    """重建向量数据库"""
    try:
        from rag_service import get_rag_service
        service = get_rag_service()
        success = service.rebuild_vector_db()
        if success:
            return {"message": "向量数据库重建成功", "success": True}
        else:
            return {"message": "向量数据库重建失败", "success": False}
    except Exception as e:
        return {"error": f"重建向量数据库失败: {e}", "success": False}

# 智能刷新向量数据库接口
@router.post("/refresh_vector_db")
def refresh_vector_db():
    """智能刷新向量数据库（优化版）"""
    try:
        from rag_service import get_rag_service
        import time
        
        start_time = time.time()
        service = get_rag_service()
        
        print("=" * 50)
        print("开始智能刷新向量数据库...")
        print("=" * 50)
        
        # 1. 检查当前状态
        print("检查向量数据库健康状态...")
        health_status = service.check_vector_db_health()
        
        if health_status["healthy"]:
            # 如果数据库健康，尝试增量更新新文件
            print("向量数据库健康，尝试增量更新新文件...")
            success = service.update_vector_db_with_new_files()
            if success:
                elapsed = time.time() - start_time
                print(f"增量更新完成，耗时: {elapsed:.2f}秒")
                return {
                    "message": "向量数据库已更新新文件",
                    "success": True,
                    "action": "update",
                    "elapsed_time": round(elapsed, 2)
                }
            else:
                print("增量更新失败，尝试重新加载...")
                # 增量更新失败，尝试重新加载
                if service.load_vector_store():
                    elapsed = time.time() - start_time
                    print(f"重新加载完成，耗时: {elapsed:.2f}秒")
                    return {
                        "message": "向量数据库状态良好，已重新加载",
                        "success": True,
                        "action": "reload",
                        "elapsed_time": round(elapsed, 2)
                    }
                else:
                    print("重新加载失败，开始完全重建...")
                    # 加载失败，需要重建
                    success = service.rebuild_vector_db()
                    elapsed = time.time() - start_time
                    if success:
                        print(f"完全重建完成，耗时: {elapsed:.2f}秒")
                        return {
                            "message": "向量数据库加载失败，已重建",
                            "success": True,
                            "action": "rebuild",
                            "elapsed_time": round(elapsed, 2)
                        }
                    else:
                        print(f"完全重建失败，耗时: {elapsed:.2f}秒")
                        return {
                            "message": "向量数据库重建失败",
                            "success": False,
                            "action": "rebuild_failed",
                            "elapsed_time": round(elapsed, 2)
                        }
        else:
            # 数据库不健康，需要重建
            print("向量数据库不健康，开始重建...")
            for issue in health_status["issues"]:
                print(f"问题: {issue}")
            
            success = service.rebuild_vector_db()
            elapsed = time.time() - start_time
            if success:
                print(f"重建完成，耗时: {elapsed:.2f}秒")
                return {
                    "message": "向量数据库已重建",
                    "success": True,
                    "action": "rebuild",
                    "issues": health_status["issues"],
                    "elapsed_time": round(elapsed, 2)
                }
            else:
                print(f"重建失败，耗时: {elapsed:.2f}秒")
                return {
                    "message": "向量数据库重建失败",
                    "success": False,
                    "action": "rebuild_failed",
                    "issues": health_status["issues"],
                    "elapsed_time": round(elapsed, 2)
                }
                
    except Exception as e:
        import traceback
        print(f"刷新向量数据库异常: {e}")
        print(f"详细错误: {traceback.format_exc()}")
        return {
            "error": f"刷新向量数据库失败: {e}",
            "success": False,
            "action": "error"
        }

# 查看文件处理状态接口
@router.get("/file_processing_status")
def file_processing_status():
    """查看文件处理状态"""
    try:
        from rag_service import get_rag_service
        service = get_rag_service()
        
        # 获取当前知识库中的所有文件
        current_files = set()
        for root, dirs, files in os.walk(service.knowledge_base_path):
            for file in files:
                if any(file.endswith(ext) for ext in ['.txt', '.md', '.pdf']):
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)
        
        # 获取已处理的文件列表
        processed_files = service.get_processed_files_list()
        
        # 找出新文件和已删除文件
        new_files = current_files - processed_files
        deleted_files = processed_files - current_files
        
        return {
            "total_files": len(current_files),
            "processed_files": len(processed_files),
            "new_files": len(new_files),
            "deleted_files": len(deleted_files),
            "new_file_list": list(new_files),
            "deleted_file_list": list(deleted_files),
            "needs_update": len(new_files) > 0 or len(deleted_files) > 0
        }
    except Exception as e:
        return {"error": f"获取文件处理状态失败: {e}"}
