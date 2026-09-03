import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore


import warnings

# Filter noisy third-party warnings
warnings.filterwarnings("ignore")

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


# Check API key
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

print("Gemini API key loaded:", api_key[:10] + "...")


# PDF path
pdf_path = Path(__file__).parent / "Solution.pdf"


# Load the PDF
loader = PyPDFLoader(str(pdf_path))
docs = loader.load()


# Split documents into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)

chunks = text_splitter.split_documents(docs)


# Create Gemini embedding model
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)


# Store embeddings in Qdrant
vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embeddings_model,
    url="http://localhost:6333",
    collection_name="rag-collection"
)


# Done
print("Indexing completed successfully.")