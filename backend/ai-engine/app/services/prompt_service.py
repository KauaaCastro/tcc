from pathlib import Path
from typing import List, Dict, Any
from app.schemas.chat import ProfileType
from app.utils.logger import logger


class PromptService:
    """
    Serviço que orquestra e monta os Prompts Adaptativos do MedInteract.
    Lê os templates clínicos de arquivos externos (.txt) e injeta o
    contexto das bulas da ANVISA recuperadas via RAG.
    """

    def __init__(self):
        # Localiza a pasta app/prompts relativa a este arquivo
        self.prompts_dir = Path(__file__).resolve().parent.parent / "prompts"

    def _load_prompt_template(self, profile: ProfileType) -> str:
        """Carrega o texto do arquivo correspondente ao perfil."""
        filename = "professional.txt" if profile == ProfileType.PROFESSIONAL else "patient.txt"
        file_path = self.prompts_dir / filename

        try:
            return file_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error(f"[PROMPT] Erro ao carregar template {file_path}: {e}")
            # Fallback seguro caso o arquivo não seja encontrado
            return "Você é o assistente clínico MedInteract. Analise as interações medicamentosas com segurança."

    def format_retrieved_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formata os fragmentos de bulas do PGVector em um bloco estruturado.
        """
        if not chunks:
            return "Nenhum trecho de bula específico foi recuperado do acervo oficial para esta busca."

        lines = ["\n[BULAS OFICIAIS DA ANVISA - BASE DE CONHECIMENTO CLÍNICO]:"]
        for idx, chunk in enumerate(chunks, start=1):
            med = chunk.get("med_name", "Medicamento")
            content = chunk.get("content", "").strip()
            lines.append(f"\n--- FONTE OFICIAL {idx}: Bula de {med} ---")
            lines.append(content)

        return "\n".join(lines)

    def build_system_prompt(self, profile: ProfileType, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Gera o System Prompt completo:
        [Template do Perfil (.txt)] + [Trechos Oficiais ANVISA (RAG)]
        """
        base_prompt = self._load_prompt_template(profile)
        context_str = self.format_retrieved_context(retrieved_chunks)

        return f"{base_prompt}\n\n{context_str}"


# Instância global reutilizável
prompt_service = PromptService()


# Bloco para testar localmente
if __name__ == "__main__":
    exemplo = [
        {"med_name": "Dipirona", "content": "Indicada como analgésico e antipirético."}
    ]
    print("--- PROMPT PACIENTE CARREGADO DE TXT ---")
    print(prompt_service.build_system_prompt(ProfileType.PATIENT, exemplo)[:300] + "...")
