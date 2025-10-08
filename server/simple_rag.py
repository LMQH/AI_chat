# -*- coding: utf-8 -*-
"""
简化版 RAG 服务
当复杂模型加载失败时使用
"""
import os
import re
from typing import List

class SimpleRAGService:
    """简化版 RAG 服务"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.knowledge_base_path = knowledge_base_path or os.path.join(os.path.dirname(__file__), "..", "datasets", "data")
        self.documents = []
        self.initialized = False
        
    def load_documents(self):
        """加载文档内容"""
        try:
            documents = []
            if not os.path.exists(self.knowledge_base_path):
                print(f"知识库目录不存在: {self.knowledge_base_path}")
                return []
                
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        try:
                            # 简单的文本提取（这里只是示例，实际需要 PDF 解析）
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                # 简单的文本提取，实际项目中应该使用 PyPDF 等库
                                text_content = content.decode('utf-8', errors='ignore')
                                documents.append({
                                    'file': file,
                                    'content': text_content[:1000]  # 限制长度
                                })
                                print(f"已加载: {file}")
                        except Exception as e:
                            print(f"加载文件失败 {file}: {e}")
                            
            return documents
        except Exception as e:
            print(f"文档加载失败: {e}")
            return []
    
    def initialize(self):
        """初始化简化 RAG 服务"""
        try:
            print("正在初始化简化 RAG 服务...")
            self.documents = self.load_documents()
            if self.documents:
                self.initialized = True
                print(f"简化 RAG 服务初始化完成，加载了 {len(self.documents)} 个文档")
                return True
            else:
                print("未找到文档，简化 RAG 服务不可用")
                return False
        except Exception as e:
            print(f"简化 RAG 服务初始化失败: {e}")
            return False
    
    def search_documents(self, query: str, k: int = 3):
        """简单的文档搜索"""
        if not self.initialized:
            return []
            
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            # 简单的关键词匹配
            if any(word in content_lower for word in query_lower.split()):
                results.append(doc)
                
        return results[:k]
    
    def enhance_query(self, user_query: str) -> str:
        """增强用户查询"""
        if not self.initialized:
            return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""
            
        try:
            relevant_docs = self.search_documents(user_query)
            if not relevant_docs:
                print("简化RAG未找到相关文档，将基于通用知识回答")
                return f"""用户问题：{user_query}

注意：在简化知识库中未找到相关信息，请基于您的通用知识回答用户的问题。"""
                
            context = "\n\n".join([doc['content'] for doc in relevant_docs])
            enhanced_query = f"""基于以下简化知识库信息回答用户问题：

简化知识库信息：
{context}

用户问题：{user_query}

请结合知识库信息给出准确、详细的回答。如果知识库信息不足以完全回答问题，可以结合您的通用知识进行补充。"""
            
            print(f"简化 RAG 增强成功，检索到 {len(relevant_docs)} 个相关文档")
            return enhanced_query
            
        except Exception as e:
            print(f"简化 RAG 增强失败: {e}")
            return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.initialized and len(self.documents) > 0

# 全局简化 RAG 服务实例
simple_rag_service = None

def get_simple_rag_service():
    """获取简化 RAG 服务实例"""
    global simple_rag_service
    if simple_rag_service is None:
        simple_rag_service = SimpleRAGService()
    return simple_rag_service

def initialize_simple_rag():
    """初始化简化 RAG 服务"""
    try:
        service = get_simple_rag_service()
        return service.initialize()
    except Exception as e:
        print(f"简化 RAG 服务初始化异常: {e}")
        return False
