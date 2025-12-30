import os, chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction  # <-- ekle

def get_chroma():
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./storage/chroma")
    client = chromadb.Client(Settings(persist_directory=persist_dir, is_persistent=True))
    return client

def get_collection(name: str = "exhibits"):
    client = get_chroma()
    model = os.getenv("EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    emb_fn = SentenceTransformerEmbeddingFunction(model_name=model)  # <-- ekle
    return client.get_or_create_collection(
        name=name,
        embedding_function=emb_fn,    # <-- ekle
        metadata={"hnsw:space": "cosine"},
    )
