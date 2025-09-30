from langchain_openai import ChatOpenAI
from database import get_db_connection  # 假设你已定义好 get_db_connection


def llm(text: str):
    """
    同步调用 LLM 获取回复
    """
    chat_model = ChatOpenAI(
        api_key="your_api_key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )
    result = chat_model.invoke(text)
    return result.content


def llm_stream(text: str, subjectid: int):
    """
    流式调用 LLM，并将用户和 AI 的对话保存到数据库
    """
    chat_model = ChatOpenAI(
        api_key="your_api_key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )

    # 1. 先流式输出 subjectid（前端用于识别会话）
    yield str(subjectid)

    # 2. 调用流式模型
    result = chat_model.stream(text)
    content = ""

    # 3. 边生成边返回给前端
    for chunk in result:
        if chunk.content:
            content += chunk.content
            yield chunk.content

    # 4. 将对话保存到数据库（使用 with 管理连接）
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 使用正确的字段名：content, role
                insert_sql = """
                    INSERT INTO chatcontent (subjectid, content, role) 
                    VALUES (%s, %s, %s)
                """

                # 插入用户消息
                cursor.execute(insert_sql, (subjectid, text, "user"))
                # 插入 AI 回复
                cursor.execute(insert_sql, (subjectid, content, "assistant"))

                # 统一提交事务（两个操作一起成功或失败）
                conn.commit()
                print(f"对话已保存：subjectid={subjectid}")

    except Exception as e:
        print(f"保存对话失败: {e}")
        # conn 会由上下文自动关闭
        raise  # 可选择是否向上抛出
