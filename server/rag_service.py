"""
RAG 增强服务
"""
import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class RAGService:
    """RAG 增强服务类"""
    
    def __init__(self, knowledge_base_path: str = None):
        """
        初始化 RAG 服务
        
        Args:
            knowledge_base_path: 知识库文件路径，默认数据目录
        """
        self.knowledge_base_path = knowledge_base_path or os.path.join(os.path.dirname(__file__), "..", "datasets", "data")
        self.vector_store = None
        self.retriever = None
        self.embed_model = None
        self.initialized = False
        
        # 向量数据库存储路径
        self.vector_db_path = os.path.join(os.path.dirname(__file__), "vector_db")
        self.vector_index_path = os.path.join(self.vector_db_path, "faiss_index")
        self.vector_pkl_path = os.path.join(self.vector_db_path, "faiss_index.pkl")
        
        
    def initialize_models(self):
        """初始化嵌入模型和聊天模型"""
        try:
            # 检查本地 FlagEmbedding 模型
            local_model_path = os.path.join(os.path.dirname(__file__), "..", "FlagEmbedding")
            if os.path.exists(local_model_path):
                print(f"使用本地 FlagEmbedding 模型: {local_model_path}")
                try:
                    self.embed_model = HuggingFaceEmbeddings(
                        model_name=local_model_path,
                        model_kwargs={'device': 'cpu'}  # 使用 CPU
                    )
                    print("本地模型加载成功")
                except Exception as e:
                    print(f"本地模型加载失败: {e}")
                    print("回退到默认模型")
                    self.embed_model = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2",
                        model_kwargs={'device': 'cpu'}
                    )
            else:
                print("未找到本地 FlagEmbedding 模型，使用默认模型")
                # 初始化嵌入模型（使用默认模型）
                self.embed_model = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",  # 轻量级模型
                    model_kwargs={'device': 'cpu'}  # 使用 CPU
                )
            
            # 测试模型是否正常工作
            test_text = "测试文本"
            test_embedding = self.embed_model.embed_query(test_text)
            print(f"模型测试成功，嵌入维度: {len(test_embedding)}")
            return True
            
        except Exception as e:
            print(f"模型初始化失败: {e}")
            return False
    
    def load_knowledge_base(self, file_extensions: List[str] = None):
        """
        加载知识库文档
        
        Args:
            file_extensions: 支持的文件扩展名，默认为 ['.txt', '.md', '.pdf']
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.md', '.pdf']
            
        documents = []
        
        try:
            # 遍历知识库目录
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if any(file.endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file)
                        try:
                            # 根据文件类型选择加载器
                            if file.endswith('.pdf'):
                                loader = PyPDFLoader(file_path)
                            else:
                                loader = TextLoader(file_path, encoding="utf-8")
                            
                            docs = loader.load()
                            documents.extend(docs)
                            print(f"已加载: {file_path}")
                        except Exception as e:
                            print(f"加载文件失败 {file_path}: {e}")
                            
        except Exception as e:
            print(f"知识库加载失败: {e}")
            return []
            
        return documents
    
    def create_vector_store(self, documents: List[Document]):
        """
        创建向量存储（优化版）
        
        Args:
            documents: 文档列表
        """
        try:
            print(f"开始处理 {len(documents)} 个文档...")
            
            # 文本分割
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,  # 增大块大小以保持上下文
                chunk_overlap=50,  # 增加重叠以保持连贯性
                separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            print(f"文档分割完成，生成 {len(chunks)} 个文本块")
            
            # 分批处理大量文档，避免内存溢出
            batch_size = 100  # 每批处理100个文档块
            all_chunks = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                print(f"处理批次 {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} 个文档块)")
                
                if i == 0:
                    # 第一批，创建初始向量存储
                    self.vector_store = FAISS.from_documents(batch, self.embed_model)
                else:
                    # 后续批次，添加到现有存储
                    batch_store = FAISS.from_documents(batch, self.embed_model)
                    self.vector_store.merge_from(batch_store)
                
                # 强制垃圾回收，释放内存
                import gc
                gc.collect()
            
            # 创建检索器
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # 返回最相关的3个文档块
            )
            
            # 保存向量数据库到磁盘
            print("保存向量数据库到磁盘...")
            self.save_vector_store()
            
            print(f"向量存储创建成功，包含 {len(chunks)} 个文档块")
            return True
            
        except Exception as e:
            print(f"向量存储创建失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    def save_vector_store(self):
        """保存向量存储到磁盘"""
        try:
            if self.vector_store is None:
                return False
                
            # 确保目录存在
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # 保存FAISS索引
            self.vector_store.save_local(self.vector_index_path)
            print(f"向量数据库已保存到: {self.vector_index_path}")
            return True
            
        except Exception as e:
            print(f"保存向量数据库失败: {e}")
            return False
    
    def load_vector_store(self):
        """从磁盘加载向量存储（改进版）"""
        try:
            # 检查向量数据库目录是否存在
            if not os.path.exists(self.vector_db_path):
                print(f"向量数据库目录不存在: {self.vector_db_path}")
                return False
            
            # 检查FAISS索引文件
            index_files = [
                os.path.join(self.vector_index_path, "index.faiss"),
                os.path.join(self.vector_index_path, "index.pkl")
            ]
            
            for file_path in index_files:
                if not os.path.exists(file_path):
                    print(f"向量数据库文件不存在: {file_path}")
                    return False
            
            # 检查文件大小，避免加载空文件
            for file_path in index_files:
                if os.path.getsize(file_path) == 0:
                    print(f"向量数据库文件为空: {file_path}")
                    return False
            
            print(f"正在加载向量数据库: {self.vector_index_path}")
            
            # 加载FAISS索引
            self.vector_store = FAISS.load_local(
                self.vector_index_path, 
                self.embed_model,
                allow_dangerous_deserialization=True
            )
            
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            
            # 验证加载是否成功
            if self.vector_store is None or self.retriever is None:
                print("向量数据库加载后为空")
                return False
            
            print(f"✅ 向量数据库加载成功: {self.vector_index_path}")
            return True
            
        except Exception as e:
            print(f"❌ 加载向量数据库失败: {e}")
            # 详细错误信息
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    def create_qa_chain(self):
        """创建问答链（简化版本）"""
        try:
            # 简化问答链创建，直接使用检索器
            # 不需要复杂的 RetrievalQA 链，避免循环导入问题
            return True
            
        except Exception as e:
            print(f"问答链创建失败: {e}")
            return False
    
    def initialize(self):
        """初始化整个 RAG 服务"""
        print("正在初始化 RAG 服务...")
        
        try:
            # 1. 初始化模型
            if not self.initialize_models():
                print("模型初始化失败，RAG 功能将不可用")
                return False
            
            # 2. 尝试加载已存在的向量数据库
            if self.load_vector_store():
                print("成功加载已存在的向量数据库")
                self.initialized = True
                return True
            
            # 3. 如果加载失败，重新构建向量数据库
            print("向量数据库不存在或加载失败，开始重新构建...")
            documents = self.load_knowledge_base()
            if not documents:
                print("未找到知识库文档，RAG 功能将不可用")
                return False
                
            # 4. 创建向量存储
            if not self.create_vector_store(documents):
                print("向量存储创建失败，RAG 功能将不可用")
                return False
                
            # 5. 创建问答链
            if not self.create_qa_chain():
                print("问答链创建失败，RAG 功能将不可用")
                return False
                
            self.initialized = True
            print("RAG 服务初始化完成")
            return True
            
        except Exception as e:
            print(f"RAG 服务初始化过程中发生异常: {e}")
            return False
    
    def retrieve_relevant_docs(self, query: str, k: int = 3) -> List[Document]:
        """检索相关文档"""
        if not self.retriever:
            return []
            
        try:
            docs = self.retriever.get_relevant_documents(query)
            return docs[:k]
        except Exception as e:
            print(f"文档检索失败: {e}")
            return []
    
    def enhance_query(self, user_query: str) -> str:
        """使用 RAG 增强用户查询"""
        if not self.is_available():
            return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""
            
        try:
            relevant_docs = self.retrieve_relevant_docs(user_query)
            
            if not relevant_docs:
                return f"""用户问题：{user_query}

注意：在专业知识库中未找到相关信息，请基于您的通用知识回答用户的问题。"""
                
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            return f"""基于以下专业知识库信息回答用户问题：

专业知识库信息：
{context}

用户问题：{user_query}

请结合专业知识库信息给出准确、详细的回答。如果知识库信息不足以完全回答问题，可以结合您的通用知识进行补充。"""
            
        except Exception as e:
            print(f"查询增强失败: {e}")
            return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""
    
    def is_available(self) -> bool:
        """检查 RAG 服务是否可用"""
        return self.initialized and self.retriever is not None
    
    
    def get_vector_db_info(self):
        """获取向量数据库信息"""
        try:
            return {
                "vector_db_path": self.vector_db_path,
                "initialized": self.initialized,
                "has_retriever": self.retriever is not None,
                "embed_model_available": self.embed_model is not None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_vector_db_health(self):
        """检查向量数据库健康状态"""
        try:
            if not os.path.exists(self.vector_index_path):
                return {"healthy": False, "issues": ["向量数据库不存在"]}
            
            faiss_file = os.path.join(self.vector_index_path, "index.faiss")
            pkl_file = os.path.join(self.vector_index_path, "index.pkl")
            
            if not os.path.exists(faiss_file) or not os.path.exists(pkl_file):
                return {"healthy": False, "issues": ["向量数据库文件不完整"]}
            
            if os.path.getsize(faiss_file) == 0 or os.path.getsize(pkl_file) == 0:
                return {"healthy": False, "issues": ["向量数据库文件为空"]}
            
            return {"healthy": True, "issues": []}
            
        except Exception as e:
            return {"healthy": False, "issues": [f"健康检查失败: {e}"]}
    
    def rebuild_vector_db(self):
        """重建向量数据库（优化版）"""
        try:
            print("开始重建向量数据库...")
            
            # 删除旧的向量数据库
            if os.path.exists(self.vector_db_path):
                import shutil
                shutil.rmtree(self.vector_db_path)
                print("已删除旧的向量数据库")
            
            # 重新初始化
            self.initialized = False
            
            # 分步骤初始化，添加进度反馈
            print("### 步骤1: 初始化嵌入模型...")
            if not self.initialize_models():
                print("模型初始化失败")
                return False
            
            print("### 步骤2: 加载知识库文档...")
            documents = self.load_knowledge_base()
            if not documents:
                print("未找到知识库文档")
                return False
            
            print(f"### 步骤3: 处理 {len(documents)} 个文档...")
            if not self.create_vector_store(documents):
                print("向量存储创建失败")
                return False
            
            print("### 步骤4: 创建问答链...")
            if not self.create_qa_chain():
                print("问答链创建失败")
                return False
            
            self.initialized = True
            print("向量数据库重建完成")
            
            # 更新已处理文件列表
            print("### 步骤5: 更新已处理文件列表...")
            all_files = set()
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if any(file.endswith(ext) for ext in ['.txt', '.md', '.pdf']):
                        file_path = os.path.join(root, file)
                        all_files.add(file_path)
            
            if all_files:
                self.save_processed_files_list(all_files)
            else:
                print("警告: 没有找到任何文件，无法更新文件列表")
            
            return True
            
        except Exception as e:
            print(f"重建向量数据库失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False

    def get_processed_files_list(self):
        """获取已处理文件列表"""
        processed_files_path = os.path.join(self.vector_db_path, "processed_files.txt")
        processed_files = set()
        
        if os.path.exists(processed_files_path):
            try:
                with open(processed_files_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        file_path = line.strip()
                        if file_path and os.path.exists(file_path):
                            processed_files.add(file_path)
            except Exception as e:
                print(f"读取已处理文件列表失败: {e}")
        
        return processed_files
    
    def save_processed_files_list(self, file_paths):
        """保存已处理文件列表"""
        try:
            os.makedirs(self.vector_db_path, exist_ok=True)
            processed_files_path = os.path.join(self.vector_db_path, "processed_files.txt")
            
            print(f"保存文件列表到: {processed_files_path}")
            print(f"文件数量: {len(file_paths)}")
            
            with open(processed_files_path, 'w', encoding='utf-8') as f:
                for file_path in sorted(file_paths):
                    f.write(file_path + '\n')
            
            print(f"已保存 {len(file_paths)} 个已处理文件到列表")
            print(f"文件路径: {processed_files_path}")
            return True
        except Exception as e:
            print(f"保存已处理文件列表失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    def update_vector_db_with_new_files(self):
        """真正的增量更新向量数据库（只处理新文件）"""
        try:
            print("开始增量更新向量数据库...")
            
            # 1. 获取当前知识库中的所有文件
            current_files = set()
            for root, dirs, files in os.walk(self.knowledge_base_path):
                for file in files:
                    if any(file.endswith(ext) for ext in ['.txt', '.md', '.pdf']):
                        file_path = os.path.join(root, file)
                        current_files.add(file_path)
            
            print(f"知识库中共有 {len(current_files)} 个文件")
            
            # 2. 获取已处理的文件列表
            processed_files = self.get_processed_files_list()
            print(f"已处理文件: {len(processed_files)} 个")
            
            # 3. 找出真正的新文件（存在但未处理过的）
            new_files = set()
            for file_path in current_files:
                if file_path not in processed_files:
                    new_files.add(file_path)
            
            # 4. 找出已删除的文件（已处理但不存在了）
            deleted_files = set()
            for file_path in processed_files:
                if file_path not in current_files:
                    deleted_files.add(file_path)
            
            print(f"发现新文件: {len(new_files)} 个")
            print(f"发现已删除文件: {len(deleted_files)} 个")
            
            if not new_files and not deleted_files:
                print("没有文件变化，无需更新")
                return True
            
            # 5. 如果有文件变化，需要完全重建（因为FAISS不支持真正的增量更新）
            if new_files:
                print("新文件列表:")
                for file_path in new_files:
                    print(f"  + {file_path}")
            
            if deleted_files:
                print("已删除文件列表:")
                for file_path in deleted_files:
                    print(f"  - {file_path}")
            
            print("由于文件变化，执行完全重建...")
            success = self.rebuild_vector_db()
            
            if success:
                # 6. 更新已处理文件列表
                self.save_processed_files_list(current_files)
                print("已更新文件处理记录")
            
            return success
                
        except Exception as e:
            print(f"增量更新失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            print("回退到完全重建...")
            return self.rebuild_vector_db()


# 全局 RAG 服务实例（延迟初始化）
rag_service = None
_rag_initialized = False

def get_rag_service() -> RAGService:
    """获取 RAG 服务实例"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService(knowledge_base_path=os.path.join(os.path.dirname(__file__), "..", "datasets", "data"))
    return rag_service

def initialize_rag_service():
    """初始化 RAG 服务（延迟初始化）"""
    global _rag_initialized
    if _rag_initialized:
        return True
    
    try:
        service = get_rag_service()
        result = service.initialize()
        _rag_initialized = result
        if result:
            print("RAG 服务初始化成功")
        else:
            print("RAG 服务初始化失败，将使用基础 LLM 功能")
        return result
    except Exception as e:
        print(f"RAG 服务初始化异常: {e}")
        print("RAG 服务将不可用，使用基础 LLM 功能")
        return False

def check_and_initialize_vector_db():
    """检查并初始化向量数据库"""
    try:
        service = get_rag_service()
        
        health_status = service.check_vector_db_health()
        
        if health_status["healthy"]:
            if service.load_vector_store():
                return True
        
        if not os.path.exists(service.knowledge_base_path):
            return False
        
        documents = service.load_knowledge_base()
        if not documents:
            return False
        
        return service.initialize()
            
    except Exception as e:
        print(f"向量数据库检查失败: {e}")
        return False


def enhance_query_with_rag(user_query: str) -> str:
    """使用 RAG 增强用户查询"""
    try:
        if not _rag_initialized:
            initialize_rag_service()
        
        service = get_rag_service()
        if service.is_available():
            return service.enhance_query(user_query)
        else:
            return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""
    except Exception as e:
        print(f"RAG 增强查询失败: {e}")
        return f"""用户问题：{user_query}

请基于您的知识回答用户的问题。"""

def get_rag_status():
    """获取 RAG 服务状态"""
    try:
        service = get_rag_service()
        return {
            "initialized": _rag_initialized,
            "available": service.is_available(),
            "knowledge_base_path": service.knowledge_base_path
        }
    except Exception as e:
        return {"error": str(e)}