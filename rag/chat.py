import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Filter noisy third-party warnings
warnings.filterwarnings("ignore")

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "rag-collection")
EMBEDDING_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash")

SYSTEM_PROMPT = """You are a helpful assistant answering questions based on the provided document context.
Use ONLY the supplied context. If the answer cannot be found in the context, respond with:
"I could not find the answer in the provided document."
Do not guess or use outside knowledge. Keep your answer clear, accurate, and concise."""


def get_vector_store() -> QdrantVectorStore:
    """Connect to existing Qdrant collection."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    return QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
    )


def get_chat_model() -> ChatGoogleGenerativeAI:
    """Initialize Gemini Chat model."""
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
    )


def _extract_text(response: Any) -> str:
    """Safely extract plain text from LLM response."""
    if hasattr(response, "text") and response.text:
        return str(response.text).strip()
    
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts).strip()
    return str(content).strip()


def ask_pdf(
    question: str,
    k: int = 4,
    vector_store: Optional[QdrantVectorStore] = None,
    llm: Optional[ChatGoogleGenerativeAI] = None,
) -> Dict[str, Any]:
    """
    Search vector database for relevant chunks and generate grounded answer.
    
    Returns:
        dict containing 'question', 'answer', and 'sources'.
    """
    if vector_store is None:
        vector_store = get_vector_store()
    if llm is None:
        llm = get_chat_model()

    matches = vector_store.similarity_search_with_score(question, k=k)

    if not matches:
        return {
            "question": question,
            "answer": "I could not find the answer in the provided document.",
            "sources": [],
        }

    context = "\n\n".join(
        f"[Passage {idx}]\n{doc.page_content}"
        for idx, (doc, _) in enumerate(matches, start=1)
    )

    prompt = f"{SYSTEM_PROMPT}\n\n--- Document Context ---\n{context}\n\n--- User Question ---\n{question}"
    raw_response = llm.invoke(prompt)
    answer_text = _extract_text(raw_response)

    sources: List[Dict[str, Any]] = []
    for idx, (doc, score) in enumerate(matches, start=1):
        raw_page = doc.metadata.get("page")
        page_num = str(raw_page + 1) if isinstance(raw_page, int) else "?"
        sources.append({
            "index": idx,
            "page": page_num,
            "score": round(float(score), 4),
            "content": doc.page_content,
        })

    return {
        "question": question,
        "answer": answer_text,
        "sources": sources,
    }


if __name__ == "__main__":
    from cli import main
    main()