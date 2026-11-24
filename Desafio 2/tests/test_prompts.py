"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / f"{PROMPT_KEY}.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data() -> dict:
    """Dados do prompt otimizado (v2), aceitando o formato com ou sem chave raiz."""
    assert PROMPT_PATH.exists(), f"Arquivo não encontrado: {PROMPT_PATH}"
    data = load_prompts(str(PROMPT_PATH))
    assert isinstance(data, dict), "O YAML deve conter um mapeamento"
    return data.get(PROMPT_KEY, data)


@pytest.fixture(scope="module")
def system_prompt(prompt_data) -> str:
    return prompt_data.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não existe"
        assert isinstance(prompt_data["system_prompt"], str), "'system_prompt' deve ser texto"
        assert prompt_data["system_prompt"].strip(), "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        role_pattern = re.compile(
            r"\b(voc[êe] [ée] (um|uma)|atue como|aja como|you are (a|an))\b",
            re.IGNORECASE,
        )
        assert role_pattern.search(system_prompt), (
            "O system_prompt não define uma persona (ex.: 'Você é um Product Manager...')"
        )

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = system_prompt.lower()
        mentions_markdown = "markdown" in text
        mentions_user_story = all(
            term in text for term in ("como", "eu quero", "para que")
        )
        assert mentions_markdown or mentions_user_story, (
            "O system_prompt deve exigir Markdown ou o formato padrão de User Story "
            "('Como [usuário], eu quero [ação], para que [benefício]')"
        )

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        text = system_prompt.lower()
        assert re.search(r"\bexemplos?\b|\bexamples?\b", text), (
            "O system_prompt não apresenta exemplos"
        )

        input_markers = len(re.findall(
            r"(bug_report|relato( de bug)?|entrada|input)\s*:", text
        ))
        output_markers = len(re.findall(
            r"(user_story|user story( gerada)?|sa[íi]da|output)\s*:", text
        ))
        assert input_markers >= 2 and output_markers >= 2, (
            "Few-shot exige pelo menos 2 pares de entrada/saída "
            f"(entradas encontradas: {input_markers}, saídas: {output_markers})"
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field in ("description", "system_prompt", "user_prompt"):
            value = prompt_data.get(field) or ""
            assert "TODO" not in value.upper(), f"O campo '{field}' ainda contém TODO"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied")
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"

        valid = [t for t in techniques if isinstance(t, str) and t.strip()]
        assert len(valid) >= 2, (
            f"Mínimo de 2 técnicas em 'techniques_applied', encontradas: {len(valid)}"
        )

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
