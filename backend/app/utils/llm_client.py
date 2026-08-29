"""
Unified LLM client. Supports Groq (cloud) and Ollama (local).
Switch via LLM_PROVIDER in .env -- nothing else changes.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from app import config


def _build_groq_client():
    from langchain_groq import ChatGroq
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model=config.GROQ_MODEL,
        temperature=0.2,
    )


def _build_ollama_client():
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_BASE_URL,
        temperature=0.2,
    )


def get_llm():
    if config.LLM_PROVIDER == "ollama":
        return _build_ollama_client()
    return _build_groq_client()


def ask_llm(system_prompt: str, user_prompt: str) -> str:
    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    return response.content