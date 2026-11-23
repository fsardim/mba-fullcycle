"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"
INPUT_VARIABLE = "bug_report"


def build_readme(prompt_data: dict) -> str:
    """Monta o README exibido na página do prompt no LangSmith Hub."""
    techniques = prompt_data.get("techniques_applied", [])
    lines = [
        f"# {PROMPT_KEY}",
        "",
        prompt_data.get("description", ""),
        "",
        f"**Versão:** {prompt_data.get('version', '')}",
        "",
        "## Técnicas aplicadas",
        "",
    ]
    lines += [f"- {t}" for t in techniques]
    return "\n".join(lines)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    messages = [("system", prompt_data["system_prompt"])]
    user_prompt = prompt_data.get("user_prompt", "").strip()
    if user_prompt:
        messages.append(("user", user_prompt))

    try:
        prompt = ChatPromptTemplate.from_messages(messages)
    except Exception as e:
        print(f"❌ Erro ao montar o ChatPromptTemplate: {e}")
        print("   Dica: chaves literais no texto (ex.: JSON) precisam ser escapadas como {{ e }}.")
        return False

    if prompt.input_variables != [INPUT_VARIABLE]:
        print(f"❌ Variáveis do template: {prompt.input_variables}. Esperado apenas: ['{INPUT_VARIABLE}']")
        print("   Dica: chaves literais no texto (ex.: JSON) precisam ser escapadas como {{ e }}.")
        return False

    techniques = prompt_data.get("techniques_applied", [])
    tags = list(dict.fromkeys(
        list(prompt_data.get("tags", []))
        + [prompt_data.get("version", "")]
        + [f"technique:{t}" for t in techniques]
    ))
    tags = [t for t in tags if t]

    client = Client()
    try:
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=prompt_data.get("description", ""),
            readme=build_readme(prompt_data),
            tags=tags,
        )
    except Exception as e:
        if "Nothing to commit" in str(e):
            print("ℹ️  O prompt não mudou desde o último push. Nada a enviar.")
            return True
        print(f"❌ Erro ao fazer push do prompt: {e}")
        return False

    print(f"✅ Push concluído: {prompt_name}")
    print(f"   URL: {url}")
    print(f"   Tags: {', '.join(tags)}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    full_text = f"{prompt_data.get('system_prompt', '')}\n{prompt_data.get('user_prompt', '')}"
    if f"{{{INPUT_VARIABLE}}}" not in full_text:
        errors.append(f"O prompt precisa conter a variável {{{INPUT_VARIABLE}}}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{PROMPT_KEY}"
    print_section_header(f"Push do prompt: {prompt_name}")

    data = load_yaml(str(PROMPT_PATH))
    if not data:
        return 1

    # Aceita o formato com chave raiz (como no v1) ou o formato plano
    prompt_data = data.get(PROMPT_KEY, data)

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
