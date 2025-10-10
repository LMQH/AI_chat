from database import get_db_connection  # 假设你已定义好 get_db_connection
from rag_service import enhance_query_with_rag  # 导入 RAG 增强功能
import os
import requests
import json
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 军事冲突与地缘态势智能分析助手身份认知
MILITARY_ANALYST_SYSTEM_PROMPT = """你是一位专业的军事冲突与地缘态势智能分析助手。你具备以下专业能力：

1. 军事分析专长：
   - 深度分析军事冲突的起因、发展态势和潜在影响
   - 评估各方军事实力、战略意图和战术部署
   - 分析武器装备、军事技术和作战能力
   - 预测冲突发展趋势和可能的解决方案

2. 地缘政治洞察：
   - 分析国际关系格局和地缘政治动态
   - 评估各国战略利益和外交政策
   - 理解区域安全形势和联盟关系
   - 识别地缘政治风险和机遇

3. 情报分析能力：
   - 整合多源信息进行综合分析
   - 识别关键信息和趋势信号
   - 评估信息可靠性和来源可信度
   - 提供客观、专业的分析结论

4. 专业表达：
   - 使用准确的专业术语和军事概念
   - 提供结构化的分析框架
   - 保持客观中立的分析立场
   - 基于事实和逻辑进行推理

请以专业、客观、深入的方式回应用户的军事和地缘政治相关问题。"""

def calculate_max_tokens(input_text: str, max_context: int = 3000) -> int:
    """
    根据输入文本长度动态计算max_tokens
    保守估计：输入token数约为字符数的1/3
    """
    # 估算输入token数（保守估计）
    estimated_input_tokens = len(input_text) // 3
    
    # 预留一些buffer，确保不超过上下文限制
    available_tokens = max_context - estimated_input_tokens - 200  # 200作为安全buffer
    
    # 确保max_tokens在合理范围内
    return max(100, min(available_tokens, 1000))


def llm(text: str, identity_id: str = None):
    """
    同步调用本地部署的 LLM 获取回复（带 RAG 增强和身份认知）
    """
    # 使用 RAG 增强查询
    enhanced_text = enhance_query_with_rag(text)
    
    # 使用军事冲突与地缘态势智能分析助手身份认知
    system_prompt = MILITARY_ANALYST_SYSTEM_PROMPT
    
    # 本地模型服务配置
    local_model_url = os.getenv("LOCAL_MODEL_URL")
    model_name = os.getenv("LOCAL_MODEL_NAME")
    
    if not local_model_url:
        raise ValueError("缺少环境变量 LOCAL_MODEL_URL")
    if not model_name:
        raise ValueError("缺少环境变量 LOCAL_MODEL_NAME")
    
    # 构建请求数据
    # 动态计算max_tokens（考虑系统提示词长度）
    full_text = f"{system_prompt}\n\n{enhanced_text}" if system_prompt else enhanced_text
    max_tokens = calculate_max_tokens(full_text)
    
    # 构建消息列表
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": enhanced_text})
    
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": False,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    try:
        response = requests.post(
            local_model_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"调用本地模型失败: {e}")
    except (KeyError, IndexError) as e:
        raise ValueError(f"解析模型响应失败: {e}")


def llm_stream(text: str, subjectid: int, identity_id: str = None):
    """
    流式调用本地部署的 LLM，并在结束后保存 AI 的回复到数据库。
    注意：用户消息已在路由中入库，这里不再重复写入。
    支持身份认知功能。
    """
    content = ""
    
    try:
        # 1) 先把 subjectid 作为首段发给前端
        yield str(subjectid)

        # 使用 RAG 增强查询（添加异常处理）
        try:
            enhanced_text = enhance_query_with_rag(text)
        except Exception as rag_error:
            print(f"RAG 增强失败，使用原始查询: {rag_error}")
            enhanced_text = text
        
        # 使用军事冲突与地缘态势智能分析助手身份认知
        system_prompt = MILITARY_ANALYST_SYSTEM_PROMPT
        
        # 本地模型服务配置
        local_model_url = os.getenv("LOCAL_MODEL_URL")
        model_name = os.getenv("LOCAL_MODEL_NAME")
        
        if not local_model_url:
            error_msg = "缺少环境变量 LOCAL_MODEL_URL"
            print(error_msg)
            yield f"错误: {error_msg}"
            return
        if not model_name:
            error_msg = "缺少环境变量 LOCAL_MODEL_NAME"
            print(error_msg)
            yield f"错误: {error_msg}"
            return
        
        # 构建流式请求数据
        # 动态计算max_tokens（考虑系统提示词长度）
        full_text = f"{system_prompt}\n\n{enhanced_text}" if system_prompt else enhanced_text
        max_tokens = calculate_max_tokens(full_text)
        
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": enhanced_text})
        
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": True,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # 2) 调用流式模型
        print(f"发送请求到: {local_model_url}")
        print(f"请求数据: {payload}")
        
        response = requests.post(
            local_model_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
            stream=True
        )
        
        print(f"响应状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"响应内容: {response.text}")
            raise requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.text}")
        
        response.raise_for_status()
        
        # 3) 边生成边返回给前端
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # 去掉 'data: ' 前缀
                    if data.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(data)
                        if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                            delta = chunk_data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                chunk_content = delta['content']
                                content += chunk_content
                                yield chunk_content
                    except json.JSONDecodeError:
                        continue
                        
    except requests.exceptions.RequestException as e:
        error_msg = f"调用本地模型失败: {e}"
        print(error_msg)
        yield f"错误: {error_msg}"
        return
    except Exception as e:
        error_msg = f"流式调用异常: {e}"
        print(error_msg)
        yield f"错误: {error_msg}"
        return
    finally:
        # 4) 将 AI 回复保存到数据库（使用 finally 确保执行）
        if content:  # 只有在有内容时才保存
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
