# 军事冲突与地缘态势智能分析系统

## 项目简介

本系统是一个基于 RAG（检索增强生成）技术的智能对话分析平台，专注于军事冲突与地缘政治领域的专业分析。系统结合了大语言模型（LLM）、向量数据库和 LoRA 微调技术，为用户提供准确、专业的军事态势分析服务。

### 核心特性

- **专业领域知识**：集成军事冲突与地缘政治专业知识库
- **RAG 增强**：基于 FAISS 向量数据库的检索增强生成
- **流式对话**：支持实时流式响应，提升用户体验
- **多模态支持**：支持文本、图片、PDF 等多种格式文件上传
- **会话管理**：完整的对话历史记录和主题管理
- **智能刷新**：增量式向量数据库更新机制

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                      前端层 (UniApp)                     │
│  - Vue.js 单页面应用                                      │
│  - 流式消息渲染                                           │
│  - Markdown 支持                                         │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/WebSocket
┌────────────────┴────────────────────────────────────────┐
│                   API 层 (FastAPI)	                      │
│  - RESTful API 接口                                      │
│  - 流式响应处理                                           │
│  - 文件上传管理                                           │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴─────────┐
        │                  │
┌───────┴────────┐  ┌─────┴──────────┐
│  RAG 服务层     │  │   LLM 服务层    │
│  - FAISS 检索   │  │  - 模型推理     │
│  - 向量化       │  │  - LoRA 微调    │
│  - 知识库管理    │  │  - 流式生成     │
└───────┬────────┘  └─────┬──────────┘
        │                  │
┌───────┴────────┐  ┌─────┴──────────┐
│  向量数据库      │  │   关系数据库    │
│  - FAISS Index │  │  - MySQL       │
│  - 文档索引     │  │  - 会话存储     │
└────────────────┘  └────────────────┘
```

### 技术栈

#### 后端技术
- **Web 框架**：FastAPI 0.104.1
- **数据库**：MySQL + PyMySQL
- **向量检索**：FAISS (Facebook AI Similarity Search)
- **嵌入模型**：HuggingFace Sentence Transformers / FlagEmbedding
- **语言处理**：LangChain + LangChain Community
- **大模型推理**：本地 LLM 服务（支持 OpenAI 兼容 API）
- **文档解析**：PyPDF、TextLoader

#### 前端技术
- **框架**：UniApp + Vue.js
- **UI 组件**：原生组件 + 自定义样式
- **Markdown 渲染**：自定义渲染器
- **状态管理**：Vue Data 响应式

#### AI/ML 技术
- **模型微调**：LoRA (Low-Rank Adaptation)
- **向量化**：Sentence Transformers
- **文本分割**：RecursiveCharacterTextSplitter
- **检索策略**：相似度检索 (k=3)

---

## 核心模块详解

### 1. RAG 服务模块 (`rag_service.py`)

负责知识库的构建、检索和查询增强。

#### 主要功能
- **知识库加载**：支持 `.txt`、`.md`、`.pdf` 格式
- **文档分块**：智能文本分割（chunk_size=500, overlap=50）
- **向量化**：使用 HuggingFace 嵌入模型
- **FAISS 索引**：高效相似度检索
- **增量更新**：智能检测新文件并更新索引

#### 关键代码流程
```python
# 初始化 -> 加载文档 -> 文本分割 -> 向量化 -> 构建 FAISS 索引
RAGService.initialize()
  ├── initialize_models()        # 加载嵌入模型
  ├── load_knowledge_base()      # 遍历知识库目录
  ├── create_vector_store()      # 创建 FAISS 向量存储
  └── save_vector_store()        # 持久化到磁盘
```

### 2. LLM 调用模块 (`llm_utils.py`)

处理与大语言模型的交互，支持同步和流式调用。

#### 核心特性
- **身份认知**：军事分析专家系统提示词
- **RAG 增强**：自动检索相关知识并注入上下文
- **动态 Token 控制**：根据输入长度自适应调整 max_tokens
- **流式响应**：逐块返回生成内容
- **数据库同步**：自动保存对话记录

#### 流式对话流程
```python
llm_stream(text, subjectid)
  ├── enhance_query_with_rag()   # RAG 增强查询
  ├── 构建消息列表（system + user）
  ├── 流式请求 LLM API
  ├── 逐块 yield 返回前端
  └── 保存 AI 回复到数据库
```

### 3. API 路由模块 (`routes.py`)

提供前端所需的所有 HTTP 接口。

#### 主要接口

| 接口路径 | 方法 | 功能描述 |
|---------|------|---------|
| `/stream` | POST | 流式对话（主接口） |
| `/chat` | POST | 同步对话（降级接口） |
| `/upload` | POST | 文件上传 |
| `/get_subject` | GET | 获取对话主题列表 |
| `/get_chatcontent_at_subjectid` | GET | 获取指定主题的历史消息 |
| `/subject/{id}` | DELETE | 删除对话主题 |
| `/refresh_vector_db` | POST | 智能刷新向量数据库 |
| `/rag_status` | GET | 查询 RAG 服务状态 |

### 4. 数据库模块 (`database.py`)

管理 MySQL 连接和事务。

#### 设计亮点
- **上下文管理器**：自动管理连接生命周期
- **重试机制**：连接失败自动重试（最多 3 次）
- **字符集处理**：强制使用 utf8mb4 避免乱码
- **超时控制**：设置合理的连接/读写超时

#### 数据库表结构

```sql
-- 对话主题表
CREATE TABLE subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话内容表
CREATE TABLE chatcontent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subjectid INT NOT NULL,
    content TEXT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subjectid) REFERENCES subject(id) ON DELETE CASCADE
);
```

### 5. 前端应用 (`chat.vue`)

基于 UniApp 的跨平台聊天界面。

#### 核心功能
- **流式渲染**：逐字显示 AI 回复
- **Markdown 支持**：代码块、列表、粗体等格式
- **侧边栏**：对话历史管理
- **附件支持**：图片/文件预览
- **滑动删除**：主题项左滑删除
- **智能刷新**：向量库状态监控

---

## 项目部署指南

以下部署指南由 Claude 辅助生成，可参考

### 环境要求

#### 硬件要求
- **CPU**：4 核及以上
- **内存**：8GB+（推荐 16GB）
- **存储**：20GB+（用于模型和向量库）
- **GPU**（可选）：用于加速嵌入模型推理

#### 软件要求
- **操作系统**：Linux / macOS / Windows
- **Python**：3.8 - 3.11
- **Node.js**：14.0+（前端开发）
- **MySQL**：5.7+ / 8.0+
- **本地 LLM 服务**：支持 OpenAI 兼容 API

---

### 后端部署步骤

#### 1. 克隆项目
```bash
git clone <repository_url>
cd military-analysis-system
```

#### 2. 创建 Python 虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

创建 `.env` 文件（根目录）：
```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=military_analysis

# LLM 服务配置
LOCAL_MODEL_URL=http://localhost:8080/v1/chat/completions
LOCAL_MODEL_NAME=your-model-name

# 可选配置
KNOWLEDGE_BASE_PATH=./datasets/data
```

#### 5. 初始化数据库

登录 MySQL 并执行：
```sql
CREATE DATABASE military_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE military_analysis;

CREATE TABLE subject (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE chatcontent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subjectid INT NOT NULL,
    content TEXT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_subjectid (subjectid),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (subjectid) REFERENCES subject(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6. 准备知识库

将军事/地缘政治相关文档放入知识库目录：
```
datasets/
└── data/
    ├── military_conflicts.pdf
    ├── geopolitical_analysis.txt
    └── strategic_reports.md
```

#### 7. 下载嵌入模型（可选）

如果使用本地 FlagEmbedding 模型：
```bash
# 从 HuggingFace 下载模型到项目根目录
git lfs clone https://huggingface.co/BAAI/bge-small-zh-v1.5 FlagEmbedding
```

或使用默认的 `sentence-transformers/all-MiniLM-L6-v2`（首次运行自动下载）。

#### 8. 启动后端服务
```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动。

首次启动会自动：
- 测试数据库连接
- 初始化向量数据库
- 加载嵌入模型
- 构建 FAISS 索引

---

### 前端部署步骤

#### 1. 安装 HBuilderX

下载并安装 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（UniApp 官方 IDE）

#### 2. 导入项目

将 `chat.vue` 文件放入 UniApp 项目的 `pages` 目录：
```
uniapp-project/
├── pages/
│   └── chat/
│       └── chat.vue
├── static/
│   └── icons/  # 图标资源
└── App.vue
```

#### 3. 配置后端地址

修改 `chat.vue` 中的 `backendBase`：
```javascript
data() {
  return {
    backendBase: 'http://your-server-ip:8000',  // 修改为实际后端地址
    // ...
  }
}
```

#### 4. 运行项目

在 HBuilderX 中：
- 选择运行到浏览器（H5）
- 或运行到微信开发者工具（小程序）
- 或运行到手机模拟器（App）

---

### Docker 部署（推荐生产环境）

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: military_analysis
      MYSQL_USER: app_user
      MYSQL_PASSWORD: app_password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  backend:
    build: .
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: app_user
      DB_PASSWORD: app_password
      DB_NAME: military_analysis
      LOCAL_MODEL_URL: http://llm-service:8080/v1/chat/completions
      LOCAL_MODEL_NAME: your-model
    volumes:
      - ./datasets:/app/datasets
      - ./vector_db:/app/vector_db
    ports:
      - "8000:8000"
    depends_on:
      - mysql

volumes:
  mysql_data:
```

#### 3. 启动服务
```bash
docker-compose up -d
```

---

## 本地 LLM 服务配置

系统需要一个兼容 OpenAI API 格式的本地 LLM 服务。推荐方案：

（本项目使用的是VLLM配置方案）

### 方案 1：Ollama
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull qwen2:7b

# 启动服务（默认端口 11434）
ollama serve
```

配置 `.env`：
```env
LOCAL_MODEL_URL=http://localhost:11434/v1/chat/completions
LOCAL_MODEL_NAME=qwen2:7b
```

### 方案 2：vLLM
```bash
# 安装 vLLM
pip install vllm

# 启动服务
python -m vllm.entrypoints.openai.api_server \
  --model your-model-path \
  --host 0.0.0.0 \
  --port 8080
```

### 方案 3：LM Studio
下载 [LM Studio](https://lmstudio.ai/)，加载模型后启动本地服务器。

---

## 常见问题排查

### 1. 向量数据库初始化失败

**症状**：启动时提示"向量数据库初始化失败"

**解决方案**：
```bash
# 检查知识库目录是否存在
ls datasets/data

# 手动重建向量库
curl -X POST http://localhost:8000/rebuild_vector_db
```

### 2. 数据库连接失败

**症状**：`pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**：
- 确认 MySQL 服务已启动
- 检查 `.env` 中的数据库配置
- 确认防火墙允许 3306 端口

### 3. 流式响应中断

**症状**：AI 回复显示不完整

**解决方案**：
- 检查 LLM 服务是否正常运行
- 增加请求超时时间（`llm_utils.py` 中的 `timeout`）
- 查看后端日志排查错误

### 4. 中文乱码

**症状**：数据库中存储的中文显示为 `???`

**解决方案**：
- 确认数据库使用 `utf8mb4` 字符集
- 检查数据库连接是否设置了 `charset="utf8mb4"`
- 重新创建表并指定字符集

### 5. 嵌入模型下载缓慢

**解决方案**：
```bash
# 使用国内镜像站
export HF_ENDPOINT=https://hf-mirror.com
pip install -U huggingface_hub
```

---

## 性能优化建议

### 1. 向量检索优化
- 调整 `k` 值（相关文档数量）：3-5 之间
- 使用 GPU 加速嵌入模型（安装 `faiss-gpu`）
- 定期清理过期向量索引

### 2. 数据库优化
```sql
-- 为高频查询字段添加索引
CREATE INDEX idx_role ON chatcontent(role);
CREATE INDEX idx_composite ON chatcontent(subjectid, created_at);

-- 定期清理旧数据
DELETE FROM chatcontent WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### 3. LLM 服务优化
- 使用量化模型（INT8/INT4）减少显存占用
- 启用 KV Cache 缓存
- 调整 batch size 和 max_tokens

### 4. 前端优化
- 启用虚拟滚动（长对话历史）
- 图片懒加载
- 本地缓存对话历史

---

## 扩展功能建议

### 1. 多模型切换
在 `llm_utils.py` 中添加模型选择逻辑：
```python
def llm_stream(text: str, subjectid: int, model_name: str = "default"):
    model_url = get_model_url_by_name(model_name)
    # ...
```

### 2. 用户认证
集成 JWT 认证：
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

### 3. 分布式部署
- 使用 Redis 做会话共享
- Nginx 负载均衡多个后端实例
- 向量库使用 Milvus 替代 FAISS

### 4. 监控告警
- 集成 Prometheus + Grafana
- 添加日志聚合（ELK Stack）
- 设置异常告警通知

---

## 开发团队与贡献

### 项目维护者
[项目负责人信息]  LMQH

### 贡献指南
欢迎提交 Issue 和 Pull Request！

### 许可证
[根据实际情况填写]

---

## 附录

### A. 完整依赖列表
详见 `requirements.txt`

### B. API 接口文档
访问 `http://localhost:8000/docs` 查看自动生成的 Swagger 文档

### C. 参考资料
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LangChain 文档](https://python.langchain.com/)
- [FAISS 介绍](https://github.com/facebookresearch/faiss)
- [UniApp 开发指南](https://uniapp.dcloud.net.cn/)

---

**最后更新时间**：2025-10-17