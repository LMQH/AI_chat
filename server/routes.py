from fastapi import APIRouter, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import create_connection
from llm_utils import llm, llm_stream

router = APIRouter()
connection = create_connection()


@router.get("/test1")
def test1():
    return {"message": "Hello, World!"}


@router.get("/test2")
def test2(count: int, chat_text: str):
    return {"count": count, "chat_text": chat_text}


class Mydata(BaseModel):
    count: str
    chat_text: str


@router.post("/test3")
def test3(data: Mydata):
    return {"data": data}


@router.post("/test4")
async def test4(img1: UploadFile):
    with open(f"static/{img1.filename}", "wb") as f:
        content = await img1.read()
        f.write(content)
    return {"img": f"http://localhost:8000/static/{img1.filename}"}


@router.get("/chat")
def chat(text: str):
    ai_content = llm(text)
    return {"code": 2000, "content": ai_content}


@router.get("/stream")
def stream(text: str, subjectid: int):
    if subjectid == 0:
        title = llm(f"用户的对话内容是:{text},请帮我生成一个对话主题,只返回主题文字")
        cursor = connection.cursor()
        sql = f'INSERT INTO subject (title) VALUES ("{title}")'
        cursor.execute(sql)
        subjectid = cursor.lastrowid
    return StreamingResponse(llm_stream(text, subjectid), media_type="text/plain")


@router.get("/get_subject")
def get_subject():
    cursor = connection.cursor()
    sql = "select * from subject"
    cursor.execute(sql)
    return cursor.fetchall()


@router.get("/get_chatcontent_at_subjectid")
def get_chatcontent_at_subjectid(subjectid: int):
    cursor = connection.cursor()
    sql = f"SELECT * FROM chatcontent WHERE subjectid={subjectid} limit 0,20"
    cursor.execute(sql)
    return cursor.fetchall()



