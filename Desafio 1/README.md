# Desafio MBA Engenharia de Software com IA - Full Cycle

Sistema de RAG (Retrieval-Augmented Generation) que ingere documentos PDF em um banco vetorial PostgreSQL e permite consultas em linguagem natural via chat, respondendo exclusivamente com base no conteúdo do documento fornecido.

## Arquitetura

```
PDF → ingest.py → chunks → embeddings (OpenAI) → PostgreSQL + pgvector
                                                          ↓
Pergunta → chat.py → busca vetorial (similarity search) → LLM (OpenAI) → Resposta
```

**Componentes:**
- **PostgreSQL + pgvector** — banco vetorial para armazenar e buscar embeddings
- **LangChain** — orquestração do pipeline de ingestão e recuperação
- **OpenAI** — geração de embeddings (`text-embedding-3-small`) e respostas (`gpt-4o-mini`)

## Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução
- Python 3.11+
- Chave de API da OpenAI

## Configuração

### 1. Variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus valores:

```bash
cp .env.example src/.env
```

Edite `src/.env`:

```env
OPENAI_API_KEY=sk-...            # Chave da API OpenAI (obrigatório)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PGVECTOR_COLLECTION=minha_colecao
PDF_PATH=/caminho/absoluto/para/seu/documento.pdf
```

> `PDF_PATH` deve apontar para o PDF que será a fonte de dados do chat.

### 2. Instalar dependências Python

```bash
pip install -r requirements.txt
```

## Execução

### Passo 1 — Subir o banco de dados

```bash
docker compose up -d
```

Aguarde até todos os containers estarem saudáveis. Verifique com:

```bash
docker compose ps
```

Caso a extensão pgvector não seja ativada automaticamente, execute:

```bash
docker exec postgres_rag psql -U postgres -d rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Passo 2 — Ingerir o PDF

```bash
cd src
python ingest.py
```

O script carrega o PDF definido em `PDF_PATH`, divide o conteúdo em chunks, gera embeddings e armazena no PostgreSQL. Ao final exibe o total de chunks inseridos.

> **Atenção:** Re-executar `ingest.py` com um novo PDF **substitui** completamente a coleção anterior. Não é necessário limpar o banco manualmente.

### Passo 3 — Iniciar o chat

```bash
python chat.py
```

Digite perguntas sobre o conteúdo do documento. O sistema busca os trechos mais relevantes e usa o LLM para formular a resposta. Para encerrar, digite `sair`.

**Exemplo:**

```
Faça sua pergunta (ou digite 'sair'):

PERGUNTA: Quais são os principais tópicos abordados no documento?

RESPOSTA: ...
```

> O sistema responde **somente** com base no conteúdo do PDF. Perguntas fora do contexto retornam: `"Não tenho informações necessárias para responder sua pergunta."`

## Trocar o documento fonte

1. Atualize `PDF_PATH` em `src/.env` com o caminho do novo PDF
2. Execute `python ingest.py` novamente
3. Inicie `python chat.py` — o chat já reflete o novo documento

## Estrutura do projeto

```
.
├── docker-compose.yml       # PostgreSQL + pgvector
├── requirements.txt         # Dependências Python
├── .env.example             # Template de variáveis de ambiente
├── document.pdf             # PDF de exemplo
└── src/
    ├── .env                 # Variáveis de ambiente (não versionar)
    ├── ingest.py            # Ingestão do PDF no banco vetorial
    ├── search.py            # Busca vetorial e template de prompt
    └── chat.py              # Interface de chat interativo
```

## Parar o ambiente

```bash
docker compose down
```

Para remover também os dados persistidos:

```bash
docker compose down -v
```
