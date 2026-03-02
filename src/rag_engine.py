from openai import OpenAI
from src.config import LLM_API_KEY, CHAT_MODEL
from src.vector_db import retrieve_context

client = OpenAI(api_key=LLM_API_KEY)

SYSTEM_PROMPT = (
    "You are an expert technical support assistant for Jäppinen Ltd. field mechanics. "
    "You must answer the user's question ONLY using the provided context from the technical documentation. "
    "The context may include wiring diagrams and schematics extracted as plain text - these appear as "
    "fragmented labels and values (e.g. 'WATER VALVES\\n890 TO 1.3 kΩ\\nRD HOT\\nCOLD BU'). "
    "Resistance values, voltages, and other specifications found in wiring diagrams are valid answers - "
    "extract and report them directly. "
    "If the context does not contain the answer, politely state: "
    "'I am sorry, but the provided documentation does not contain the answer to this question.' "
    "Do not guess or provide outside information."
)


def _build_context_block(documents: list[str], metadatas: list[dict]) -> str:
    sections = []
    for doc, meta in zip(documents, metadatas):
        sections.append(f"[Source: {meta['source']}, Page {meta['page']}]\n{doc}")
    return "\n\n---\n\n".join(sections)


def _deduplicate_sources(metadatas: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for meta in metadatas:
        key = (meta["source"], meta["page"])
        if key not in seen:
            seen.add(key)
            sources.append({"source": meta["source"], "page": meta["page"]})
    return sources


def _rewrite_query(user_input: str, history: list[dict]) -> str:
    """
    If history exists, rewrite the query to be fully self-contained for retrieval.
    If the query is already standalone, the LLM returns it unchanged.
    The rewritten query is used only for retrieval - the original is used for the answer.
    """
    history_text = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in history
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a query rewriting assistant. Given a conversation history and a follow-up query, "
                    "rewrite the query to be fully self-contained so it can be understood without the conversation history. "
                    "If the query is already self-contained, return it exactly unchanged. "
                    "Return ONLY the rewritten query - no explanation, no punctuation changes, nothing else."
                ),
            },
            {
                "role": "user",
                "content": f"Conversation history:\n{history_text}\n\nQuery: {user_input}",
            },
        ],
        temperature=0,
        max_tokens=120,
    )

    return response.choices[0].message.content.strip()


def _prepare_messages(
    user_input: str,
    history: list[dict] | None,
    filter_source: str | None,
) -> tuple[list[dict], list[dict], float]:
    """
    Shared retrieval + message-building logic for query() and query_stream().

    Returns:
        messages:      List of message dicts ready for the chat completions API.
        sources:       Deduplicated list of {source, page} dicts.
        best_distance: Cosine distance of the top retrieved result.
    """
    retrieval_query = _rewrite_query(user_input, history) if history else user_input
    results = retrieve_context(retrieval_query, filter_source=filter_source)

    context_block = _build_context_block(results["documents"], results["metadatas"])

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history)

    messages.append({
        "role": "user",
        "content": f"Context:\n{context_block}\n\nQuestion: {user_input}",
    })

    sources = _deduplicate_sources(results["metadatas"])
    best_distance = results["distances"][0] if results["distances"] else 1.0

    return messages, sources, best_distance


def query(user_input: str, history: list[dict] | None = None, filter_source: str | None = None) -> dict:
    """
    Retrieve relevant context and query the LLM.

    Args:
        user_input:    The mechanic's question.
        history:       Optional list of prior message dicts [{"role": ..., "content": ...}].
        filter_source: Optional PDF filename to restrict retrieval to one manual.

    Returns a dict with:
        - answer:        str
        - sources:       list of unique {"source": str, "page": str} dicts
        - best_distance: float (cosine distance of top result; lower = more confident)
    """
    messages, sources, best_distance = _prepare_messages(user_input, history, filter_source)

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0,
    )

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
        "best_distance": best_distance,
    }


def query_stream(user_input: str, history: list[dict] | None = None, filter_source: str | None = None):
    """
    Retrieve relevant context and stream the LLM response token by token.

    Args:
        user_input:    The mechanic's question.
        history:       Optional list of prior message dicts.
        filter_source: Optional PDF filename to restrict retrieval to one manual.

    Returns:
        sources:       list of unique {"source": str, "page": str} dicts
        best_distance: float
        stream:        OpenAI streaming completion iterator - yields chunks with .choices[0].delta.content
    """
    messages, sources, best_distance = _prepare_messages(user_input, history, filter_source)

    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0,
        stream=True,
    )

    return sources, best_distance, stream