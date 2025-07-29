from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import os

def load_knowledge_base(data_folder="./kb", persist_dir="./embeddings/chroma"):
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embedding_function)

    if not os.listdir(persist_dir):  # Build KB if empty
        for file in os.listdir(data_folder):
            if file.endswith(".txt"):
                with open(os.path.join(data_folder, file), "r", encoding="utf-8") as f:
                    raw_text = f.read()
                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                chunks = splitter.split_text(raw_text)
                docs = [Document(page_content=c, metadata={"source": file}) for c in chunks]
                vectorstore.add_documents(docs)
        vectorstore.persist()
    return vectorstore
