import os

from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split(file_path: str) -> list:
    """按扩展名选择加载器，解析后按语义分块。"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path, encoding="utf-8")
    else:  # .txt / .md 等
        loader = TextLoader(file_path, encoding="utf-8")

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )
    return splitter.split_documents(docs)
