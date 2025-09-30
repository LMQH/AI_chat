from langchain_openai import ChatOpenAI
from database import create_connection


connection = create_connection()


def llm(text):
    chat_model = ChatOpenAI(
        api_key="your_api_key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )
    result = chat_model.invoke(text)
    return result.content


def llm_stream(text, subjectid):
    chat_model = ChatOpenAI(
        api_key="your_api_key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )

    result = chat_model.stream(text)
    content = ""
    yield str(subjectid)
    for el in result:
        content += el.content
        yield el.content

    # 保存到数据库
    # cursor = connection.cursor()
    # sql1 = f'insert into chatcontent (subjectid,text,name) values ({subjectid},"{text}","user")'
    # sql2 = f'insert into chatcontent (subjectid,text,name) values ({subjectid},"{content}","ai")'
    # cursor.execute(sql1)
    # connection.commit()
    # cursor.execute(sql2)
    # connection.commit()

    # 防止SQL注入攻击的方案：
    sql1=f'insert into chatcontent (subjectid,text,name) values (%s,%s,%s)'
    sql2=f'insert into chatcontent (subjectid,text,name) values (%s,%s,%s)'
    cursor=connection.cursor()
    cursor.execute(sql1,(subjectid,text,"user"))
    # cursor.commit()
    cursor.execute(sql2,(subjectid,content,"ai"))
    cursor.commit()
