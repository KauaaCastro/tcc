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
            f"- Doenças e Condições Clínicas (com descrição de como afetam o paciente): {problemas_saude}\n"
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
            "DIRETRIZES DE ANÁLISE ESTREITA E ANCORAGEM NAS BULAS (GROUNDING FECHADO):\n"
            "1. ANCORAGEM EXCLUSIVA NA BULA (<bula>): Todas as suas afirmações sobre medicamentos, posologia, contraindicações, advertências e reações adversas devem se basear EXCLUSIVAMENTE nos trechos oficiais fornecidos na tag <bula>. É terminantemente proibido inventar dados ou buscar informações externas fora desses trechos.\n"
            "2. CRUZAMENTO DE DOENÇAS BASEADO NA DESCRIÇÃO DO USUÁRIO (<perfil_paciente>):\n"
            "   - NÃO utilize conhecimento médico pré-treinado externo sobre patologias ou doenças.\n"
            "   - Baseie-se ESTRITAMENTE na descrição que o próprio usuário forneceu no campo de doenças da tag <perfil_paciente> (onde ele relata como a condição afeta seu corpo, quais órgãos estão envolvidos ou quais sintomas possui).\n"
            "   - Se a descrição fornecida pelo usuário indicar comprometimento de determinado órgão ou função (ex.: rins, fígado, estômago, pressão arterial, sangramento) e os trechos da <bula> apontarem contraindicação, cautela, toxicidade ou sobrecarga para esse mesmo órgão/função, ALERTE o risco explicando claramente essa correlação direta entre o relato do paciente e a bula oficial.\n"
            "   - Se os trechos da <bula> não mencionarem restrição ou risco para o órgão/função descrita pelo usuário, declare explicitamente que, segundo os trechos da bula oficial consultada, não há menção ou contraindicação expressa para essa condição.\n"
            "3. LÓGICA BÁSICA E ESTILO DIRETO: Utilize lógica dedutiva elementar e linguagem clara para explicar a correlação encontrada. Não utilize saudações robóticas como 'Olá, Visitante', não repita comandos internos e vá direto à resposta objetiva da dúvida.\n\n"
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
