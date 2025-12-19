SYSTEM_PROMPT = """You are a museum guide assistant. Use only the provided context to answer.
Be concise, friendly, and factual. If unsure, say you don't know.
IMPORTANT: Always respond in the SAME LANGUAGE as the user's question.
If they ask in English, reply in English. If they ask in Turkish, reply in Turkish.
If they ask in German, reply in German. And so on."""

def build_prompt(context: str, question: str, memory_context: str = "", history_context: str = "") -> str:
    parts = [SYSTEM_PROMPT]
    
    if memory_context:
        parts.append(f"\n{memory_context}")
    
    if history_context:
        parts.append(f"\n{history_context}")
    
    parts.append(f"\nContext:\n{context}")
    parts.append(f"\nQuestion: {question}\nAnswer:")
    
    return "".join(parts)


