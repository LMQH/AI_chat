from langchain_openai import ChatOpenAI
from database import get_db_connection  # 假设你已定义好 get_db_connection
import os


def llm(text: str):
    """
    同步调用 LLM 获取回复
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("缺少环境变量 DEEPSEEK_API_KEY")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    chat_model = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    result = chat_model.invoke(text)
    return result.content


def llm_stream(text: str, subjectid: int):
    """
    流式调用 LLM，并在结束后保存 AI 的回复到数据库。
    注意：用户消息已在路由中入库，这里不再重复写入。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("缺少环境变量 DEEPSEEK_API_KEY")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    chat_model = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )

    # 1) 先把 subjectid 作为首段发给前端
    yield str(subjectid)

    # 2) 调用流式模型
    result = chat_model.stream(text)
    content = ""

    # 3) 边生成边返回给前端
    for chunk in result:
        if chunk.content:
            content += chunk.content
            yield chunk.content

    # 4) 将 AI 回复保存到数据库
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                insert_sql = (
                    "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                )
                cursor.execute(insert_sql, (subjectid, content, "assistant"))
                conn.commit()
                print(f"AI 回复已保存：subjectid={subjectid}, length={len(content)}")
    except Exception as e:
        # 出现字符集等问题时记录日志，但不再向上抛出，避免前端体验受影响
        print(f"保存 AI 回复失败: {e}")
