from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from database import get_db_connection
from llm_utils import llm_stream, llm

router = APIRouter()


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


# 测试路由，测试上传文件
@router.post("/test4")
async def test4(img1: UploadFile):
    try:
        with open(f"static/{img1.filename}", "wb") as f:
            content = await img1.read()
            f.write(content)
        return {"img": f"http://localhost:8000/static/{img1.filename}"}
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
    return raw_title.strip().strip('"\'').replace('\n', '').replace('\r', '')[:100]


# 流式对话
@router.get("/stream")
def stream(text: str, subjectid: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 如果是新对话，创建主题
                if subjectid == 0:
                    raw_title = llm(f"用户的对话内容是:{text},请帮我生成一个对话主题,只返回主题文字")
                    title = extract_clean_title(raw_title)

                    # 插入主题
                    insert_subject_sql = "INSERT INTO subject (title) VALUES (%s)"
                    cursor.execute(insert_subject_sql, (title,))
                    subjectid = cursor.lastrowid

                    # 保存用户消息（事务内）
                    insert_chat_sql = "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                    cursor.execute(insert_chat_sql, (subjectid, text, "user"))

                    conn.commit()  # 提交事务

                else:
                    # 已有主题，仅保存用户消息
                    insert_chat_sql = "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                    cursor.execute(insert_chat_sql, (subjectid, text, "user"))
                    conn.commit()

        # 流式返回 AI 回复（llm_stream 内部会保存 AI 回复）
        return StreamingResponse(
            llm_stream(text, subjectid),
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
        raise HTTPException(status_code=500, detail=f"获取主题失败: {e}")


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
