from app.schemas.user import UserProfileType

class PromptService:
    @staticmethod
    def build_system_prompt(profile_type: UserProfileType, rag_context: str = "") -> str:
        base_prompt = (
            "Você é o assistente virtual do sistema MedInteract, especializado em farmacologia, "
            "interações medicamentosas e análise de bulas de medicamentos da ANVISA.\n\n"
        )

        if rag_context:
            base_prompt += (
                "=== CONTEXTO OFICIAL EXTRAÍDO DAS BULAS (RAG) ===\n"
                f"{rag_context}\n"
                "=================================================\n"
                "Utilize as informações acima como fonte primária para fundamentar sua resposta.\n\n"
            )

        if profile_type == UserProfileType.PROFESSIONAL:
            prompt_instructions = (
                "DIRECTIVAS DE RESPOSTA (PERFIL: PROFISSIONAL DE SAÚDE / FARMACÊUTICO / MÉDICO):\n"
                "- Responda utilizando terminologia clínica e farmacológica precisa (ex: vias de metabolização hepática, citocromo P450/CYP, farmacocinética, farmacodinâmica, taxa de ligação proteica).\n"
                "- Detalhe mecanismos de ação, posologia de referência, ajustes para insuficiência renal/hepática e contraindicações formais.\n"
                "- Mantenha tom acadêmico, técnico e objetivo."
            )
        else:
            prompt_instructions = (
                "DIRECTIVAS DE RESPOSTA (PERFIL: PACIENTE / USUÁRIO COMUM):\n"
                "- Responda utilizando linguagem clara, simples, acessível e acolhedora.\n"
                "- Evite jargões médicos complexos sem explicá-los em palavras simples.\n"
                "- Destaque os cuidados principais com o medicamento, como tomar e o que fazer em caso de dúvidas.\n"
                "- INCLUA SEMPRE o alerta explícito de que esta orientação não substitui a consulta com um médico ou farmacêutico."
            )

        return f"{base_prompt}{prompt_instructions}"

prompt_service = PromptService()
