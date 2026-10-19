from pathlib import Path
from typing import List, Dict, Any, Optional
from app.schemas.chat import ProfileType, AlertType


# Orquestra o Prompt Sanduíche com sanitização XML e cálculo de IMC
class PromptService:

    def __init__(self):
        self.prompts_dir = Path(__file__).resolve().parent.parent / "prompts"

    # Carrega as diretrizes de perfil (patient.txt ou professional.txt)
    def load_profile_guidelines(self, profile: ProfileType) -> str:
        filename = "professional.txt" if profile == ProfileType.PROFESSIONAL else "patient.txt"
        file_path = self.prompts_dir / filename
        if file_path.exists():
            return file_path.read_text(encoding="utf-8").strip()
        if profile == ProfileType.PROFESSIONAL:
            return "Adapte a profundidade técnica para um PROFISSIONAL DE SAÚDE (farmacodinâmica, farmacocinética e mecanismos da bula)."
        return "Adapte a linguagem de forma clara, acolhedora e acessível para um PACIENTE, mantendo rigor técnico."

    # Remove '<' e '>' das entradas do usuário para evitar Prompt Injection
    @staticmethod
    def sanitize_xml(text: Any, default: str = "Não informado") -> str:
        if text is None:
            return default
        cleaned = str(text).replace("<", "").replace(">", "").strip()
        return cleaned if cleaned else default

    # Calcula o IMC (peso / altura²) quando peso e altura são maiores que zero
    @staticmethod
    def calculate_bmi(peso: Optional[float], altura: Optional[float]) -> str:
        try:
            if peso is not None and altura is not None and float(altura) > 0 and float(peso) > 0:
                imc = float(peso) / (float(altura) ** 2)
                return f"{imc:.2f} kg/m²"
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return "Não calculado (peso/altura não informados)"

    # Identifica o nível de alerta clínico ([DANGER], [WARNING], [INFO]) no texto gerado pela IA
    @staticmethod
    def detect_alert_type(response_text: str) -> AlertType:
        if not response_text:
            return AlertType.INFO
        upper = response_text[:300].upper()
        if "[DANGER]" in upper or "CONTRAINDICA" in upper or "RISCO GRAVE" in upper:
            return AlertType.DANGER
        if "[WARNING]" in upper or "CAUTELA" in upper or "ATENÇÃO" in upper:
            return AlertType.WARNING
        return AlertType.INFO

    # Formata os trechos de bula recuperados do PGVector para a tag <bula>
    def format_retrieved_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "Nenhum trecho de bula específico foi encontrado no acervo oficial para esta consulta."

        lines = []
        for idx, chunk in enumerate(chunks, start=1):
            med = self.sanitize_xml(chunk.get("med_name"), "Medicamento")
            chunk_idx = chunk.get("chunk_index", idx)
            content = self.sanitize_xml(chunk.get("content"), "")
            lines.append(f"--- FONTE OFICIAL #{idx}: Bula de {med} (Chunk #{chunk_idx}) ---")
            lines.append(content)

        return "\n\n".join(lines)

    # Monta a tag <perfil_paciente> com os dados higienizados e o IMC calculado
    def format_perfil_paciente_tag(self, perfil_data: Optional[Dict[str, Any]]) -> str:
        if not perfil_data:
            return (
                "<perfil_paciente>\n"
                "- Apelido: Visitante Anônimo\n"
                "- Dados Clínicos: Perfil não preenchido (avaliar alertas gerais da bula).\n"
                "</perfil_paciente>"
            )

        apelido = self.sanitize_xml(perfil_data.get("apelido"), "Visitante")
        idade = self.sanitize_xml(perfil_data.get("idade"), "Não informada")
        peso = perfil_data.get("peso")
        altura = perfil_data.get("altura")
        peso_str = f"{peso}" if peso is not None else "Não informado"
        altura_str = f"{altura}" if altura is not None else "Não informada"
        imc_str = self.calculate_bmi(peso, altura)

        gestante_str = "Sim" if bool(perfil_data.get("gestanteLactante", False)) else "Não"
        alergias = self.sanitize_xml(perfil_data.get("alergias"), "Nenhuma informada")
        problemas_saude = self.sanitize_xml(perfil_data.get("problemasSaude"), "Nenhum informado")
        medicacoes_continuas = self.sanitize_xml(perfil_data.get("medicacoesContinuas"), "Nenhuma informada")
        pratica_esportes = self.sanitize_xml(perfil_data.get("praticaEsportes"), "Não informada")
        horas_sono = self.sanitize_xml(perfil_data.get("horasSono"), "Não informada")

        return (
            "<perfil_paciente>\n"
            f"- Apelido: {apelido}\n"
            f"- Idade: {idade} anos | Peso: {peso_str} kg | Altura: {altura_str} m (IMC calculado: {imc_str})\n"
            f"- Gestante ou Lactante: {gestante_str}\n"
            f"- Alergias Conhecidas: {alergias}\n"
            f"- Problemas de Saúde Preexistentes: {problemas_saude}\n"
            f"- Medicações de Uso Contínuo: {medicacoes_continuas}\n"
            f"- Prática de Esportes / Atividade Física: {pratica_esportes}\n"
            f"- Média de Sono: {horas_sono} horas/noite\n"
            "</perfil_paciente>"
        )

    # Monta o Template Oficial do Prompt Sanduíche (<perfil_paciente>, <bula>, <pergunta_usuario>)
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
            pergunta_limpa = f"Medicamentos selecionados: {', '.join(meds_clean)}\nDúvida: {pergunta_limpa}"

        diretrizes_perfil = self.load_profile_guidelines(profile)

        return (
            f"{diretrizes_perfil}\n\n"
            "REGRAS DE OURO E RESTRIÇÕES NEGATIVAS:\n"
            "1. GROUNDING (ANCORAGEM): Responda ESTRITAMENTE com base nas informações contidas dentro da tag <bula>. NÃO utilize conhecimentos externos, memória prévia ou suposições fora do texto fornecido.\n"
            "2. PROIBIÇÃO DE DIAGNÓSTICO: Nunca realize diagnósticos clínicos e nunca deduza causas de sintomas combinando fatores externos que não estejam previstos na bula. Utilize os dados da tag <perfil_paciente> EXCLUSIVAMENTE como um filtro de leitura para destacar alertas que já estejam literalmente escritos na <bula>.\n"
            "3. HONESTIDADE CIENTÍFICA: Se a resposta para a dúvida ou a relação com o perfil do paciente não constar no texto de <bula>, declare explicitamente que a informação não foi encontrada nos trechos oficiais consultados.\n\n"
            "CHAIN OF THOUGHT (Raciocínio Passo a Passo Obrigatório):\n"
            "Antes de redigir a resposta final, processe internamente:\n"
            "- Passo 1: Identifique o princípio ativo/medicamento na <bula> e a dúvida central em <pergunta_usuario>.\n"
            "- Passo 2: Cruze o texto da <bula> com os dados de <perfil_paciente>, verificando se a bula menciona alertas específicos para:\n"
            "  * Idade e Peso/IMC (Posologia, limites de faixa etária ou ajustes de dose);\n"
            "  * Alergias e Problemas de Saúde (Contraindicações, advertências e excipientes da fórmula);\n"
            "  * Medicações Contínuas (Interações medicamentosas descritas na bula);\n"
            "  * Gestante ou Lactante (Categoria de risco na gravidez e amamentação);\n"
            "  * Prática de Esportes (Alertas oficiais de doping ou riscos musculares/tendíneos citados na bula);\n"
            "  * Rotina de Sono (Alertas da bula sobre sedação, sonolência diurna, precaução ao operar máquinas/dirigir ou insônia como reação adversa).\n"
            "- Passo 3: Elabore uma resposta clara, técnica e acessível, citando de qual seção da bula a informação foi extraída, e encerre OBRIGATORIAMENTE com o aviso legal recomendando a consulta presencial a um médico ou farmacêutico.\n\n"
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
