from langchain_openai import ChatOpenAI
from database import get_db_connection  # 假设你已定义好 get_db_connection
from rag_service import enhance_query_with_rag  # 导入 RAG 增强功能
import os


def llm(text: str):
    """
    同步调用 LLM 获取回复（带 RAG 增强）
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("缺少环境变量 DEEPSEEK_API_KEY")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    # 使用 RAG 增强查询
    enhanced_text = enhance_query_with_rag(text)

    chat_model = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    result = chat_model.invoke(enhanced_text)
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

    # 使用 RAG 增强查询
    enhanced_text = enhance_query_with_rag(text)
    
    # 2) 调用流式模型
    result = chat_model.stream(enhanced_text)
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
                # 验证subjectid是否存在
                cursor.execute("SELECT id FROM subject WHERE id = %s", (subjectid,))
                if not cursor.fetchone():
                    print(f"主题ID {subjectid} 不存在，创建默认主题")
                    cursor.execute("INSERT INTO subject (title) VALUES (%s)", ("默认对话",))
                    new_subjectid = cursor.lastrowid
                    if new_subjectid:
                        subjectid = new_subjectid
                    else:
                        # 如果还是失败，使用ID=1
                        subjectid = 1
                
                insert_sql = (
                    "INSERT INTO chatcontent (subjectid, content, role) VALUES (%s, %s, %s)"
                )
                cursor.execute(insert_sql, (subjectid, content, "assistant"))
                conn.commit()
                print(f"AI 回复已保存：subjectid={subjectid}, length={len(content)}")
    except Exception as e:
        # 出现字符集等问题时记录日志，但不再向上抛出，避免前端体验受影响
        print(f"保存 AI 回复失败: {e}")
        # 尝试使用默认主题ID
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 确保存在ID=1的主题
                    cursor.execute("SELECT id FROM subject WHERE id = 1")
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO subject (id, title) VALUES (1, %s)", ("默认对话",))
                    
                    insert_sql = (
                        "INSERT INTO chatcontent (subjectid, content, role) VALUES (1, %s, %s)"
                    )
                    cursor.execute(insert_sql, (content, "assistant"))
                    conn.commit()
                    print(f"AI 回复已保存到默认主题：length={len(content)}")
        except Exception as e2:
            print(f"保存到默认主题也失败: {e2}")
