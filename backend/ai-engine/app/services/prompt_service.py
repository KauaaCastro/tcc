from pathlib import Path
import re
from typing import List, Dict, Any, Optional
from app.schemas.chat import ProfileType, AlertType


# Monta o Prompt Sanduíche com ancoragem em 2 camadas (bula + mecanismo farmacológico e doenças)
class PromptService:

    def __init__(self):
        self.prompts_dir = Path(__file__).resolve().parent.parent / "prompts"

    def load_profile_guidelines(self, profile: ProfileType) -> str:
        filename = "professional.txt" if profile == ProfileType.PROFESSIONAL else "patient.txt"
        file_path = self.prompts_dir / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8").strip()
        if profile == ProfileType.PROFESSIONAL:
            return "Responda com profundidade técnica para um profissional de saúde."
        return "Responda de forma clara e acessível para um paciente."

    @staticmethod
    def sanitize_xml(text: Any, default: str = "Não informado") -> str:
        if text is None:
            return default
        cleaned = str(text).replace("<", "").replace(">", "").strip()
        return cleaned if cleaned else default

    @staticmethod
    def calculate_bmi(peso: Optional[float], altura: Optional[float]) -> str:
        try:
            if peso is not None and altura is not None and float(altura) > 0 and float(peso) > 0:
                imc = float(peso) / (float(altura) ** 2)
                return f"{imc:.2f} kg/m²"
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return "Não informado"

    # Prioriza a tag explícita ([DANGER], [WARNING], [INFO]) antes de checar palavras-chave
    @staticmethod
    def detect_alert_type(response_text: str) -> AlertType:
        if not response_text:
            return AlertType.INFO
        head = response_text[:120].upper()
        if "[DANGER]" in head:
            return AlertType.DANGER
        if "[WARNING]" in head:
            return AlertType.WARNING
        if "[INFO]" in head:
            return AlertType.INFO
        upper = response_text[:300].upper()
        if "CONTRAINDICA" in upper or "RISCO GRAVE" in upper:
            return AlertType.DANGER
        if "CAUTELA" in upper or "ATENÇÃO" in upper:
            return AlertType.WARNING
        return AlertType.INFO

    # Remove a tag interna [DANGER]/[WARNING]/[INFO] do início do texto exibido ao usuário
    @staticmethod
    def clean_response_tags(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"^\s*\[(DANGER|WARNING|INFO)\]\s*:?\s*\n*", "", text, flags=re.IGNORECASE)

    def format_retrieved_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "Nenhum trecho específico de bula foi localizado para os termos informados."

        lines = []
        for idx, chunk in enumerate(chunks, start=1):
            med = self.sanitize_xml(chunk.get("med_name"), "Medicamento")
            chunk_idx = chunk.get("chunk_index", idx)
            content = self.sanitize_xml(chunk.get("content"), "")
            lines.append(f"--- FONTE OFICIAL #{idx}: Bula de {med} (Trecho #{chunk_idx}) ---")
            lines.append(content)

        return "\n\n".join(lines)

    def format_perfil_paciente_tag(self, perfil_data: Optional[Dict[str, Any]]) -> str:
        if not perfil_data:
            return (
                "<perfil_paciente>\n"
                "- Ficha clínica: Não preenchida.\n"
                "</perfil_paciente>"
            )

        idade = self.sanitize_xml(perfil_data.get("idade"), "Não informada")
        peso = perfil_data.get("peso")
        altura = perfil_data.get("altura")
        peso_str = f"{peso} kg" if peso is not None else "Não informado"
        altura_str = f"{altura} m" if altura is not None else "Não informada"
        imc_str = self.calculate_bmi(peso, altura)

        gestante_str = "Sim" if bool(perfil_data.get("gestanteLactante", False)) else "Não"
        alergias = self.sanitize_xml(perfil_data.get("alergias"), "Nenhuma")
        problemas_saude = self.sanitize_xml(perfil_data.get("problemasSaude"), "Nenhum")
        medicacoes_continuas = self.sanitize_xml(perfil_data.get("medicacoesContinuas"), "Nenhuma")
        pratica_esportes = self.sanitize_xml(perfil_data.get("praticaEsportes"), "Não informada")
        horas_sono = self.sanitize_xml(perfil_data.get("horasSono"), "Não informada")

        return (
            "<perfil_paciente>\n"
            f"- Idade: {idade} | Peso: {peso_str} | Altura: {altura_str} (IMC: {imc_str})\n"
            f"- Gestante ou Lactante: {gestante_str}\n"
            f"- Alergias: {alergias}\n"
            f"- Doenças / Problemas de Saúde: {problemas_saude}\n"
            f"- Medicações Contínuas: {medicacoes_continuas}\n"
            f"- Prática de Esportes: {pratica_esportes}\n"
            f"- Horas de Sono: {horas_sono}\n"
            "</perfil_paciente>"
        )

    def build_sandwich_prompt(
        self,
        question: str,
        retrieved_chunks: List[Dict[str, Any]],
        perfil_data: Optional[Dict[str, Any]] = None,
        profile: ProfileType = ProfileType.PATIENT,
        medications: Optional[List[str]] = None,
    ) -> str:
        perfil_tag = self.format_perfil_paciente_tag(perfil_data)
        bula_context = self.format_retrieved_context(retrieved_chunks)
        pergunta_limpa = self.sanitize_xml(question, "")
        meds_clean = [self.sanitize_xml(m, "") for m in (medications or []) if m and str(m).strip()]
        if meds_clean:
            pergunta_limpa = f"Medicamentos informados: {', '.join(meds_clean)}\nPergunta: {pergunta_limpa}"

        diretrizes_perfil = self.load_profile_guidelines(profile)

        return (
            f"{diretrizes_perfil}\n\n"
            "DIRETRIZES DE ANÁLISE FARMACOLÓGICA E CLÍNICA (EM 2 CAMADAS):\n"
            "1. CAMADA 1 - EVIDÊNCIA DA BULA (<bula>): Priorize e cite as informações presentes nos trechos oficiais da tag <bula>.\n"
            "2. CAMADA 2 - RACIOCÍNIO POR CLASSE FARMACOLÓGICA, MECANISMO E DOENÇAS: Bulas frequentemente descrevem interações pela CLASSE terapêutica (ex.: AINEs, ISRS, IECA, anticoagulantes, depressores do SNC) e não pelo nome individual de cada remédio. Portanto:\n"
            "   - Se a bula do medicamento X não citar nominalmente o medicamento Y, mas houver interação conhecida por classe farmacológica, duplicidade terapêutica (ex.: usar dois anti-inflamatórios juntos) ou soma de toxicidade/efeitos adversos (sobrecarga hepática, renal, gástrica, risco de sangramento, síndrome serotoninérgica ou sedação), VOCÊ DEVE ALERTAR O RISCO claramente explicando o motivo.\n"
            "   - Se a pergunta ou a tag <perfil_paciente> mencionar uma DOENÇA ou condição clínica (ex.: dengue, gastrite, úlcera, asma, hipertensão, diabetes, insuficiência renal/hepática, gravidez), avalie ativamente se os medicamentos consultados são contraindicados ou exigem cautela nessa doença (como o risco hemorrágico de AAS e anti-inflamatórios na dengue ou lesão gástrica na gastrite).\n"
            "3. TRANSPARÊNCIA DA FONTE (OBRIGATÓRIO): Separe sempre a origem de cada informação em duas seções com estes títulos exatos:\n"
            "   - '**📗 Segundo a bula:**' somente para o que estiver explicitamente nos trechos da tag <bula> (cite o medicamento).\n"
            "   - '**⚠️ Raciocínio farmacológico geral (não consta na bula):**' para tudo que vier da Camada 2 (classe, mecanismo, doenças). Nessa seção, inclua o aviso: 'Esta informação não foi encontrada nas bulas da base oficial; é um raciocínio geral e deve ser confirmado com um médico ou farmacêutico.'\n"
            "   - Se uma das seções não tiver conteúdo, omita-a. Nunca coloque na seção da bula algo que não esteja nos trechos fornecidos.\n"
            "4. ESTILO DIRETO: Não cumprimente o usuário com frases como 'Olá, Visitante', não repita títulos robóticos de instruções e vá direto à resposta da dúvida.\n\n"
            f"{perfil_tag}\n\n"
            "<bula>\n"
            f"{bula_context}\n"
            "</bula>\n\n"
            "<pergunta_usuario>\n"
            f"{pergunta_limpa}\n"
            "</pergunta_usuario>"
        )

    def build_system_prompt(
        self,
        profile: ProfileType,
        retrieved_chunks: List[Dict[str, Any]],
        question: str = "",
        perfil_data: Optional[Dict[str, Any]] = None,
        medications: Optional[List[str]] = None,
    ) -> str:
        return self.build_sandwich_prompt(
            question=question,
            retrieved_chunks=retrieved_chunks,
            perfil_data=perfil_data,
            profile=profile,
            medications=medications,
        )


prompt_service = PromptService()
