import re
from typing import Tuple, Optional, List
from app.schemas.chat import AlertType
from app.utils.logger import logger


# Validação de escopo clínico e farmacológico da pergunta
class GuardrailService:

    def __init__(self):
        self.health_keywords = {
            "remedio", "remedios", "medicamento", "medicamentos", "farmaco", "bula",
            "posologia", "dosagem", "dose", "comprimido", "capsula", "gotas", "xarope",
            "pomada", "injecao", "mg", "ml", "mcg", "interacao", "interacoes", "interagir",
            "contraindicacao", "contraindicacoes", "efeito", "efeitos", "colateral",
            "colaterais", "adverso", "adversos", "reacao", "reacoes", "alergia", "superdosagem",
            "dor", "dores", "febre", "infeccao", "inflamacao", "pressao", "hipertensao",
            "hipotensao", "diabetes", "hipoglicemia", "colesterol", "dislipidemia",
            "triglicerideos", "estomago", "gastrite", "ulcera", "refluxo", "azia",
            "figado", "hepatico", "cirrose", "hepatite", "esteatose", "rim", "renal",
            "nefrite", "cistite", "urinaria", "gravidez", "gravida", "gestante", "lactante",
            "amamentacao", "crianca", "pediatrico", "idoso", "adulto", "sono", "ansiedade",
            "depressao", "panico", "bipolar", "epilepsia", "convulsao", "insonia", "nausea",
            "vomito", "diarreia", "constipacao", "tontura", "vertigem", "labirintite",
            "enxaqueca", "cefaleia", "sangramento", "hemorragia", "trombose", "embolia",
            "infarto", "avc", "arritmia", "taquicardia", "cardiaco", "cardiaca",
            "asma", "bronquite", "rinite", "sinusite", "pneumonia", "tosse", "gripe",
            "resfriado", "dengue", "covid", "virose", "hipotireoidismo", "hipertireoidismo",
            "tireoide", "artrite", "artrose", "gota", "osteoporose", "fibromialgia",
            "lupus", "anemia", "glaucoma", "alergico", "alergica", "inchaco", "coceira",
            "rabdomiolise", "muscular", "tomar", "beber", "ingerir", "misturar", "mistura",
            "junto", "juntos", "associar", "combinar", "prescricao", "receita", "medico",
            "farmaceutico", "serve", "indicado", "indicacao", "tratamento", "tratar",
            "usar", "uso", "sintoma", "sintomas", "doenca", "doencas", "saude", "paciente",
            "clareance", "clearance", "aas", "aspirina", "tylenol", "novalgina", "dorflex",
            "advil", "rivotril", "omeprazol", "dipirona", "paracetamol", "ibuprofeno"
        }

        # Sufixos farmacológicos da DCB/ANVISA
        self.drug_suffix_pattern = re.compile(
            r"\b\w{3,}(ina|zol|pril|sartana|statina|cilina|floxacino|pam|lol|dipino|profeno|ofenaco|micina|vir|mab|ida|ona|ato|ol|mab|parina|gliptina|flozina|lukaste|setrona|triptana)\b"
        )

        # Sufixos clínicos de doenças e condições patológicas
        self.disease_suffix_pattern = re.compile(
            r"\b\w{3,}(ite|ose|mia|patia|algia|oma|penia|plegia|rragia|rreia)\b"
        )

        # Termos de fuga de assunto fora da área da saúde
        self.off_topic_patterns = [
            r"\b(receita de bolo|culinaria|futebol|campeonato|tabela do brasileirao)\b",
            r"\b(filme|cinema|musica|poema|poesia|piada|horoscopo|signo)\b",
            r"\b(programacao|javascript|python|java|html|css|sql|computador)\b",
            r"\b(politica|eleicao|partido|voto|presidente|deputado)\b",
            r"\b(criptomoeda|bitcoin|investimento|bolsa de valores)\b"
        ]

    def _normalize_text(self, text: str) -> str:
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'é': 'e', 'ê': 'e',
            'í': 'i', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c'
        }
        normalized = text.lower()
        for char, repl in replacements.items():
            normalized = normalized.replace(char, repl)
        return normalized

    def validate_scope(
        self,
        question: str,
        medications: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[AlertType]]:
        normalized = self._normalize_text(question)

        for pattern in self.off_topic_patterns:
            if re.search(pattern, normalized):
                logger.info(f"[GUARDRAIL] Pergunta fora do escopo bloqueada: '{question[:60]}...'")
                return (
                    False,
                    "O MedInteract atende exclusivamente dúvidas sobre medicamentos, bulas, "
                    "interações medicamentosas e condições de saúde. "
                    "Formule uma pergunta relacionada à área clínica ou farmacêutica.",
                    AlertType.INFO
                )

        words = set(re.findall(r"\b\w+\b", normalized))
        has_med_chips = bool(medications and any(str(m).strip() for m in medications))
        has_drug_suffix = bool(self.drug_suffix_pattern.search(normalized))
        has_disease_suffix = bool(self.disease_suffix_pattern.search(normalized))
        has_health_context = (
            bool(words & self.health_keywords)
            or has_drug_suffix
            or has_disease_suffix
            or has_med_chips
        )

        if len(words) >= 4 and not has_health_context:
            logger.info(f"[GUARDRAIL] Pergunta sem contexto clinico: '{question[:60]}...'")
            return (
                False,
                "Não identifiquei medicamentos, sintomas ou condições de saúde na sua pergunta. "
                "Informe o nome do medicamento ou a condição clínica que deseja consultar.",
                AlertType.INFO
            )

        return (True, None, None)


guardrail_service = GuardrailService()
