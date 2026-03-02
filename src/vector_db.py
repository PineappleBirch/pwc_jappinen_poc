import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from src.config import DB_DIR, EMBEDDING_MODEL, LLM_API_KEY, TOP_K


def _get_collection():
    client = chromadb.PersistentClient(path=DB_DIR)
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=LLM_API_KEY,
        model_name=EMBEDDING_MODEL,
    )
    return client.get_or_create_collection(
        name="manuals",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_chunks(chunks: list[dict]) -> None:
    """
    Embed and store chunks in ChromaDB. Skips ingestion if the
    collection already contains documents.
    """
    collection = _get_collection()

    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        return

    print(f"Ingesting {len(chunks)} chunks into vector store...")

    ids = [f"{c['source']}_p{c['page']}_{i}" for i, c in enumerate(chunks)]
    documents = [c["text"] for c in chunks]
    metadatas = [{"source": c["source"], "page": c["page"]} for c in chunks]

    # Add in batches to avoid hitting API limits
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )
        print(f"  Ingested {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    print("Ingestion complete.")


def get_collection_stats() -> dict:
    """
    Returns {source_filename: chunk_count} for all manuals in the vector store.
    """
    collection = _get_collection()
    all_docs = collection.get(include=["metadatas"])
    stats = {}
    for meta in all_docs["metadatas"]:
        source = meta["source"]
        stats[source] = stats.get(source, 0) + 1
    return stats


def retrieve_context(query: str, top_k: int = TOP_K, filter_source: str | None = None) -> dict:
    """
    Retrieve the most relevant chunks for a query.

    Args:
        query:         The search query.
        top_k:         Number of results to return.
        filter_source: Optional PDF filename to restrict retrieval to one manual.

    Returns a ChromaDB query result dict with keys:
      - documents: list of text chunks
      - metadatas: list of metadata dicts (source, page)
      - distances: list of cosine distances (lower = more similar)
    """
    collection = _get_collection()
    where = {"source": {"$eq": filter_source}} if filter_source else None
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        where=where,
    )
    return {
        "documents": results["documents"][0],
        "metadatas": results["metadatas"][0],
        "distances": results["distances"][0],
    }