import re
from typing import Tuple, Optional, List
from app.schemas.chat import AlertType
from app.utils.logger import logger


# Serviço de barreira e contenção de escopo clínico (Guardrails)
class GuardrailService:

    def __init__(self):
        # Termos clínicos e farmacêuticos que indicam legitimidade médica
        self.health_keywords = {
            "remedio", "remedios", "medicamento", "medicamentos", "farmaco", "bula",
            "posologia", "dosagem", "dose", "comprimido", "capsula", "gotas", "xarope",
            "pomada", "injecao", "mg", "ml", "mcg", "interacao", "interacoes", "interagir",
            "contraindicacao", "contraindicacoes", "efeito", "efeitos", "colateral",
            "colaterais", "adverso", "adversos", "reacao", "reacoes", "alergia", "superdosagem",
            "dor", "dores", "febre", "infeccao", "inflamacao", "pressao", "hipertensao",
            "diabetes", "colesterol", "estomago", "figado", "hepatico", "rim", "renal",
            "gravidez", "gravida", "gestante", "lactante", "amamentacao", "crianca",
            "pediatrico", "idoso", "adulto", "sono", "ansiedade", "insonia", "nausea",
            "vomito", "diarreia", "tontura", "sangramento", "rabdomiolise", "muscular",
            "tomar", "beber", "ingerir", "misturar", "mistura", "junto", "juntos",
            "associar", "combinar", "prescricao", "receita", "medico", "farmaceutico",
            "serve", "indicado", "indicacao", "tratamento", "tratar", "usar", "uso",
            "sintoma", "sintomas", "doenca", "saude", "paciente", "clareance", "clearance"
        }

        # Sufixos farmacológicos típicos da DCB/ANVISA (ex: dipirona, sinvastatina, omeprazol)
        self.drug_suffix_pattern = re.compile(
            r"\b\w{3,}(ina|zol|pril|sartana|statina|cilina|floxacino|pam|lol|dipino|profeno|ofenaco|micina|vir|mab|ida|ona|ato|ol)\b"
        )

        # Termos flagrantes de fuga de assunto (fora do contexto de saúde)
        self.off_topic_patterns = [
            r"\b(receita de bolo|culinaria|futebol|campeonato|tabela do brasileirao)\b",
            r"\b(filme|cinema|musica|poema|poesia|piada|horoscopo|signo)\b",
            r"\b(programacao|javascript|python|java|html|css|sql|computador)\b",
            r"\b(politica|eleicao|partido|voto|presidente|deputado)\b",
            r"\b(criptomoeda|bitcoin|investimento|bolsa de valores)\b"
        ]

    # Remove acentuações e caracteres especiais para comparação flexível
    def _normalize_text(self, text: str) -> str:
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e',
            'í': 'i', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c'
        }
        normalized = text.lower()
        for char, repl in replacements.items():
            normalized = normalized.replace(char, repl)
        return normalized

    # Avalia se a pergunta e os medicamentos informados estão no escopo farmacológico
    def validate_scope(
        self,
        question: str,
        medications: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[AlertType]]:
        normalized = self._normalize_text(question)

        # 1. Checagem de fuga flagrante de assunto
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

        # 2. Checagem de relevância por palavras-chave, sufixos de fármacos ou chips selecionados
        words = set(re.findall(r"\b\w+\b", normalized))
        has_med_chips = bool(medications and any(str(m).strip() for m in medications))
        has_drug_suffix = bool(self.drug_suffix_pattern.search(normalized))
        has_health_context = bool(words & self.health_keywords) or has_drug_suffix or has_med_chips

        if len(words) >= 4 and not has_health_context:
            logger.info(f"[GUARDRAIL] Pergunta fora do contexto de saúde: '{question[:60]}...'")
            return (
                False,
                "Não identifiquei termos clínicos ou nomes de medicamentos em sua pergunta. "
                "Para ajudá-lo com segurança, informe o nome dos medicamentos que deseja consultar "
                "ou a dúvida farmacológica específica.",
                AlertType.INFO
            )

        return (True, None, None)


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
