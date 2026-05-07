import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv(Path(__file__).resolve().parent / ".env")


def ingest_pdf():
    for k in ("OPENAI_API_KEY", "DATABASE_URL", "PGVECTOR_COLLECTION", "PDF_PATH"):
        if not os.getenv(k):
            raise RuntimeError(f"Variável de ambiente {k} não definida")

    docs = PyPDFLoader(os.getenv("PDF_PATH")).load()

    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    ).split_documents(docs)

    if not splits:
        raise SystemExit("Nenhum conteúdo encontrado no PDF.")

    enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)},
        )
        for d in splits
    ]

    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )

    # pre_delete_collection=True garante que re-executar o script não gera duplicatas
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PGVECTOR_COLLECTION"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
        pre_delete_collection=True,
    )

    store.add_documents(documents=enriched)
    print(f"Ingestão concluída: {len(enriched)} chunks inseridos.")


if __name__ == "__main__":
    ingest_pdf()
