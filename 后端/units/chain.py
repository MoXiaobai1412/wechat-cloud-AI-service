import json
from operator import itemgetter

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import MySQLChatMessageHistory

class Chain:
    def __init__(self):
        self.chat_model = self.chatModel()
        self.embedding_model = self.embeddingModel()
        self.rag = self.ragInit("knowledge_base")
        self.parser = self.parserInit()
        self.prompt = self.promptInit()

    async def replyCustomersChain(self, session_id: str, content: str):
        chain = self.rag | self.prompt | self.chat_model | self.parser

        def get_session_history(session_id: str) -> MySQLChatMessageHistory:
            return MySQLChatMessageHistory(session_id)

        with_history = RunnableWithMessageHistory(
            runnable=chain,
            get_session_history = get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        config = {"configurable": {"session_id": session_id}}

        res = await with_history.ainvoke({"input": content}, config=config)
        return res
    def getConfig(self, settings):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, '..', 'config', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)[settings]

    def chatModel(self):
        config = self.getConfig("llm")
        print(config)
        model = ChatOpenAI(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model'],
            temperature=config['temperature']
        )
        return model

    def embeddingModel(self):
        config = self.getConfig("embedding")
        if config['base_url'] == '':
            config_n = self.getConfig("llm")
            config["base_url"] = config_n['base_url']
        if config['api_key'] == '':
            config_n = self.getConfig("llm")
            config["api_key"] = config_n['api_key']
        embeddings = OpenAIEmbeddings(
            model=config['model'],
            base_url=config['base_url'],
            api_key=config['api_key'],
            timeout=60,
            max_retries=2,
        )
        return embeddings

    def ragInit(self, knowledge_base):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        kb_path = os.path.join(base_dir, '..', knowledge_base)
        vectorstore = FAISS.load_local(
            folder_path=kb_path,
            embeddings=self.embedding_model,
            allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        rag = {
            "context": itemgetter("input") | retriever,
            "input": itemgetter("input"),
            "history": itemgetter("history")
        }
        return rag

    def promptInit(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(base_dir, '..', 'config', 'prompt.md')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n请基于以下内容回答用户问题：\n{context}"),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{input}"),
        ])
        return prompt

    def parserInit(self):
        return StrOutputParser()

if __name__ == '__main__':
    import asyncio
    chat = Chain()
    user_id = "001"
    while True:
        print("-" * 20)
        user_input = input("human: ")
        print("-" * 20)
        res = asyncio.run(chat.replyCustomersChain(
            session_id=user_id,
            content=user_input
        ))
        print("AI: " + res)