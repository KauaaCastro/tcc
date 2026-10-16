import re
from typing import Tuple, Optional
from app.schemas.chat import AlertType
from app.utils.logger import logger


class GuardrailService:
    """
    Serviço de barreira e contenção de escopo clínico (Guardrails).
    Garante que o MedInteract processe apenas perguntas pertinentes
    à farmacologia, medicamentos, interações e saúde humana.
    """

    def __init__(self):
        # 1. Termos e radicais clínicos que indicam legitimidade médica
        self.health_keywords = {
            # Vocabulário farmacêutico comum
            "remedio", "medicamento", "farmaco", "bula", "posologia", "dosagem",
            "dose", "comprimido", "capsula", "gotas", "xarope", "pomada", "injecao",
            "mg", "ml", "interacao", "interagir", "contraindicacao", "efeito",
            "colateral", "adverso", "reacao", "alergia", "superdosagem",
            
            # Sintomas e condições clínicas frequentes
            "dor", "febre", "infeccao", "inflamacao", "pressao", "hipertensao",
            "diabetes", "colesterol", "estomago", "figado", "rim", "renal",
            "gravidez", "gravida", "lactante", "amamentacao", "crianca", "idoso",
            "sono", "ansiedade", "insonia", "nausea", "vomito", "diarreia",
            
            # Verbos e ações de uso clínico
            "tomar", "beber", "ingerir", "misturar", "junto", "associar",
            "prescricao", "receita", "medico", "farmaceutico"
        }

        # 2. Termos flagrantes de fuga de assunto (fora do contexto de saúde)
        self.off_topic_patterns = [
            r"\b(receita de bolo|culinaria|futebol|campeonato|tabela do brasileirao)\b",
            r"\b(filme|cinema|musica|poema|poesia|piada|horoscopo|signo)\b",
            r"\b(programacao|javascript|python|java|html|css|sql|computador)\b",
            r"\b(politica|eleicao|partido|voto|presidente|deputado)\b",
            r"\b(criptomoeda|bitcoin|investimento|bolsa de valores)\b"
        ]

    def _normalize_text(self, text: str) -> str:
        """Remove acentuações e caracteres especiais para comparação flexível."""
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e',
            'í': 'i', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c'
        }
        normalized = text.lower()
        for char, repl in replacements.items():
            normalized = normalized.replace(char, repl)
        return normalized

    def validate_scope(self, question: str) -> Tuple[bool, Optional[str], Optional[AlertType]]:
        """
        Avalia se a pergunta está no escopo de saúde e farmacologia.
        
        Retorna:
            (is_valid: bool, mensagem_bloqueio: Optional[str], alert_type: Optional[AlertType])
        """
        normalized = self._normalize_text(question)

        # 1. Checagem de Fuga Flagrante de Assunto
        for pattern in self.off_topic_patterns:
            if re.search(pattern, normalized):
                logger.info(f"[GUARDRAIL] Pergunta bloqueada por fuga flagrante: '{question[:60]}...'")
                return (
                    False,
                    "Olá! O MedInteract é um assistente clínico especializado exclusivamente em "
                    "farmacologia, análise de bulas oficiais e interações medicamentosas. "
                    "Por favor, formule perguntas relacionadas a medicamentos, dosagens ou sintomas de saúde.",
                    AlertType.INFO
                )

        # 2. Checagem de Relevância por Palavras-Chave de Saúde
        words = set(re.findall(r"\b\w+\b", normalized))
        has_health_context = bool(words & self.health_keywords)

        # Se a pergunta tem mais de 4 palavras e nenhuma relação médica, sugere reformulação
        if len(words) >= 4 and not has_health_context:
            logger.info(f"[GUARDRAIL] Pergunta fora do contexto de saúde: '{question[:60]}...'")
            return (
                False,
                "Não identifiquei termos clínicos ou nomes de medicamentos em sua pergunta. "
                "Para ajudá-lo com segurança, informe o nome dos medicamentos que deseja consultar "
                "ou a dúvida farmacológica específica.",
                AlertType.INFO
            )

        # Pergunta aprovada para processamento no RAG
        return (True, None, None)


# Instância global reutilizável
guardrail_service = GuardrailService()


# Bloco de teste executável
if __name__ == "__main__":
    testes = [
        "Posso tomar dipirona com paracetamol?",
        "Qual a receita de bolo de chocolate com morango?",
        "Como programar uma função assíncrona em Python?",
        "A atorvastatina pode causar dor muscular?",
        "Quem é o melhor jogador de futebol da história?"
    ]

    print("--- TESTE DO SERVIÇO DE GUARDRAILS ---")
    for teste in testes:
        aprovado, motivo, alerta = guardrail_service.validate_scope(teste)
        status = "[APROVADO]" if aprovado else "[BLOQUEADO]"
        print(f"\nPergunta: '{teste}'")
        print(f"Status: {status}")
        if not aprovado:
            print(f"Resposta ao Usuário: {motivo}")
