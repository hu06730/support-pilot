"""RetrievalQA chain（独立文档问答场景，可选）。"""

from __future__ import annotations

from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from app.config import settings
from app.rag.vectorstore import get_retriever


def build_qa_chain():
    """构建 RetrievalQA chain。"""
    llm = ChatOpenAI(
        model=settings.openai_model,
        openai_api_key=settings.openai_api_key,
        temperature=0,
    )
    retriever = get_retriever()
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
