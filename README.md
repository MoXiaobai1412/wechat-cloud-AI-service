# Wechat AI Service（微信小程序客服自动回复）

基于 微信云函数 + Flask + LangChain 的微信 AI 客服后端系统，支持知识库检索（RAG）和多轮对话历史持久化。

## 功能特性

- **智能问答**：基于 RAG 技术，结合知识库回答用户问题
- **多轮对话**：支持多轮对话，历史记录持久化到 MySQL
- **知识库管理**：支持 PDF、DOCX、TXT 格式文档
- **异步处理**：API 接口采用异步设计，提升并发性能

## 技术栈

- **Web 框架**：Flask 3.x
- **LLM 框架**：LangChain
- **向量数据库**：FAISS
- **数据库**：MySQL
- **嵌入模型**：OpenAI 兼容 API（如 SiliconFlow、DeepSeek 等）

## 快速开始

### 环境要求

- Python 3.9+
- MySQL

### 1. 克隆项目

```bash
git clone <repository-url>
cd "Wechat AI service"
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 准备知识库/提示词

- 将知识库文档（PDF/DOCX/TXT）放入 `files/` 文件夹。
- 编辑 `config/prompt.md` 文件，定义 AI 助手的角色和行为：
```markdown
你是一个专业的客服助手，请根据知识库内容回答用户问题。
回答时请遵循以下原则：
1. 基于提供的知识库内容回答
2. 如果知识库中没有相关信息，请礼貌告知
3. 保持友好、专业的语气
```

### 4. 进入`start.ipynb`进行进一步配置（可选）

配置内容包括：
- **LLM 配置**：模型名称、API 地址、密钥
- **Embedding 配置**：嵌入模型配置（可复用 LLM 配置）
- **数据库配置**：MySQL 连接信息
- **服务端口**：API 服务监听端口

### 4. 手动配置（可选）
- 进入`config/config.json`配置好参数
- 运行`embedding.py`执行数据库向量化操作
- 使用如下代码注册数据库
```sql
CREATE TABLE IF NOT EXISTS chat_history (
    id          INT             NOT NULL AUTO_INCREMENT,
    session_id  VARCHAR(255)    NOT NULL,
    role        VARCHAR(20)     NOT NULL,
    content     TEXT            NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. 一键启动

```bash
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

服务启动后，默认监听 `http://0.0.0.0:8000`

### 6. 小程序配置

将`云函数`文件夹中的内容上传至微信云函数，并在其中配置好服务器地址。

## 配置说明

`config.json` 格式：

```json
{
    "llm": {
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "api_key": "your-api-key",
        "temperature": 0.7
    },
    "embedding": {
        "model": "Qwen/Qwen3-Embedding-4B",
        "base_url": "",
        "api_key": ""
    },
    "database": {
        "host": "localhost",
        "port": 3306,
        "database": "tutor",
        "user": "bot",
        "password": "your-password"
    },
    "port": 8000
}
```

> **注意**：Embedding 配置中的 `base_url` 和 `api_key` 留空时，会自动使用 LLM 的配置。
