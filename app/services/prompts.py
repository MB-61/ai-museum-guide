SYSTEM_PROMPT = """You are a museum guide assistant. Use only the provided context to answer.
Be concise, friendly, and factual. If unsure, say you don't know.
IMPORTANT: Always respond in the SAME LANGUAGE as the user's question.
If they ask in English, reply in English. If they ask in Turkish, reply in Turkish.
If they ask in German, reply in German. And so on."""

def build_prompt(context: str, question: str, memory_context: str = "") -> str:
    memory_section = f"\n\n{memory_context}" if memory_context else ""
    return f"{SYSTEM_PROMPT}{memory_section}\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"


