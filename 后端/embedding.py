import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config', 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    embedding = json.load(f)["embedding"]
with open(config_path, 'r', encoding='utf-8') as f:
    llm = json.load(f)["llm"]

import traceback
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# ---------- 辅助加载函数 ----------
def load_txt(file_path):
    loader = TextLoader(file_path, encoding='utf-8')
    return loader.load()

def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    return loader.load()

def load_docx(file_path):
    loader = Docx2txtLoader(file_path)
    return loader.load()

# 后缀->加载函数映射
LOADER_MAP = {
    '.txt': load_txt,
    '.pdf': load_pdf,
    '.docx': load_docx,
}

# ---------- 1. 遍历文件夹并加载文档 ----------
print("📚知识库搭建步骤 1：加载 files 文件夹中的文档...")
base_dir = "files"
if not os.path.isdir(base_dir):
    print(f"错误：文件夹 '{base_dir}' 不存在，请检查路径。")
    exit(1)

all_files = []
for root, _, files in os.walk(base_dir):
    for f in files:
        all_files.append(os.path.join(root, f))

docs = []
skipped = []
for file_path in all_files:
    ext = os.path.splitext(file_path)[1].lower()
    loader_func = LOADER_MAP.get(ext)
    if loader_func is None:
        skipped.append(file_path)
        continue
    try:
        loaded = loader_func(file_path)
        if loaded:
            docs.extend(loaded)
            print(f"  [成功] {file_path}")
        else:
            print(f"  [空内容] {file_path}")
    except Exception as e:
        print(f"  [跳过] {file_path}，原因: {e}")

print(f"加载完成，共加载 {len(docs)} 个文档片段")
if skipped:
    print(f"跳过的文件（不支持的类型）: {len(skipped)} 个")

if not docs:
    print("错误：未能加载任何有效内容，无法继续。")
    exit(1)

# ---------- 2. 文本分割 ----------
print("📚知识库搭建步骤 2：文本分割...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
split_docs = text_splitter.split_documents(docs)
print(f"原始文档片段: {len(docs)} 个，分割后文本块: {len(split_docs)} 个")

# ---------- 3. 构建嵌入模型 ----------
print("📚知识库搭建步骤 3：初始化嵌入模型...")
try:
    embeddings = OpenAIEmbeddings(
        model=embedding['model'],
        base_url=embedding['base_url'] if embedding['base_url'] != "" else llm["base_url"],
        api_key=embedding['api_key'] if embedding['api_key'] != "" else llm["api_key"],
        timeout=60,
        max_retries=2,
    )
    print("嵌入模型初始化成功")
except Exception as e:
    print(f"嵌入模型初始化失败: {e}")
    exit(1)

# ---------- 4. 向量化并构建 FAISS 索引 ----------
print("📚知识库搭建步骤 4：向量化并构建索引...")
try:
    test_vec = embeddings.embed_query("测试")
    print(f"API 连通性测试成功，向量维度: {len(test_vec)}")

    print(f"正在向量化 {len(split_docs)} 个文本块，请稍候...")
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    print("向量索引构建成功")

    # ---------- 5. 保存本地 ----------
    print("📚知识库搭建步骤 5：保存索引到 knowledge_base 文件夹...")
    vectorstore.save_local("knowledge_base")
    print("索引已保存至 knowledge_base 文件夹")
    print("———————————————————— 📚知识库搭建完成！ ————————————————————")
except Exception as e:
    print(f"向量化或保存失败: {e}")
    traceback.print_exc()
    exit(1)