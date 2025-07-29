from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import uvicorn
import importlib
from kb.load_kb import load_knowledge_base
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub

# ---------------------------
# FastAPI Config
# ---------------------------
app = FastAPI(title="AI Counsel Backend", version="1.0")

# ---------------------------
# Request & Response Models
# ---------------------------
class QueryRequest(BaseModel):
    agent: str
    question: str
    jurisdiction: str
    facts: str

class Citation(BaseModel):
    title: str
    url: str

class QueryResponse(BaseModel):
    agent: str
    answer: str
    citations: List[Citation]
    confidence: float

# ---------------------------
# Load Knowledge Base
# ---------------------------
vectorstore = load_knowledge_base()
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# HuggingFace LLM (free)
llm = HuggingFaceHub(repo_id="google/flan-t5-large", model_kwargs={"temperature": 0.1, "max_length": 512})

# ---------------------------
# API Endpoint
# ---------------------------
@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        agent_module = importlib.import_module(f"agents.{request.agent.lower()}")
        prompt = agent_module.build_prompt(request.facts, request.jurisdiction, request.question)
    except ModuleNotFoundError:
        return {"error": f"Agent {request.agent} not found."}

    # RAG Pipeline
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    result = qa_chain({"query": prompt})
    answer = result["result"] or "⚠ No verified authority found in the Knowledge Base."

    sources = [{"title": doc.metadata.get("source", "Unknown"), "url": ""} for doc in result["source_documents"]]

    return QueryResponse(agent=request.agent, answer=answer, citations=sources, confidence=0.95)

# ---------------------------
# Run Server
# ---------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
