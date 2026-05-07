#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from search import PROMPT_TEMPLATE, get_store

load_dotenv(Path(__file__).resolve().parent / ".env")

for _k in ("OPENAI_API_KEY", "DATABASE_URL", "PGVECTOR_COLLECTION"):
    if not os.getenv(_k):
        print(f"Variável de ambiente {_k} não definida.")
        sys.exit(1)

_store = get_store()
_llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0,
)


def chat_once(question: str) -> str:
    results = _store.similarity_search_with_score(question, k=10)
    if not results:
        return "Não tenho informações necessárias para responder sua pergunta."
    context = "\n\n---\n\n".join(doc.page_content.strip() for doc, _ in results)
    prompt = PROMPT_TEMPLATE.format(contexto=context, pergunta=question)
    response = _llm.invoke(prompt)
    return response.content.strip() or "Não tenho informações necessárias para responder sua pergunta."


def main():
    print("Faça sua pergunta (ou digite 'sair'):\n")
    while True:
        try:
            user = input("PERGUNTA: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break
        if not user:
            continue
        if user.lower() in ("sair", "quit", "exit"):
            print("Encerrando.")
            break
        print(f"\nRESPOSTA: {chat_once(user)}\n")


if __name__ == "__main__":
    main()
