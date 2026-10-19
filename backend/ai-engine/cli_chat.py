import asyncio
import os
import sys

# Garante que o diretório do ai-engine esteja no sys.path para importar os módulos da aplicação
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.api.endpoints.chat import ai_query_endpoint
from app.schemas.chat import ProfileType, QueryRequest


# Loop interativo no terminal para testar perguntas ao Gemini com RAG e Prompt Sanduíche
async def interactive_cli():
    profile = ProfileType.PATIENT
    medications = []

    print("\n" + "=" * 65)
    print("🤖 MEDINTERACT - CHAT DE TESTE NO TERMINAL (GEMINI + RAG)")
    print("=" * 65)
    print("Comandos rápidos:")
    print("  /meds Dipirona, Ibuprofeno  -> Define medicamentos em uso")
    print("  /perfil pro                 -> Muda para perfil PROFESSIONAL")
    print("  /perfil pac                 -> Muda para perfil PATIENT")
    print("  /sair                       -> Encerra o chat")
    print("=" * 65)

    while True:
        try:
            meds_label = ", ".join(medications) if medications else "Nenhum definido (busca automática)"
            print(f"\n[Perfil: {profile.value} | Medicamentos: {meds_label}]")
            user_input = input("👉 Digite sua pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando chat de teste. Até logo!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/sair", "sair", "exit", "quit"):
            print("Encerrando chat de teste. Até logo!")
            break

        if user_input.lower().startswith("/meds"):
            raw_meds = user_input[5:].strip()
            medications = [m.strip() for m in raw_meds.split(",") if m.strip()] if raw_meds else []
            print(f"✅ Medicamentos atualizados: {medications or 'Limpo'}")
            continue

        if user_input.lower().startswith("/perfil"):
            arg = user_input[7:].strip().lower()
            if "pro" in arg:
                profile = ProfileType.PROFESSIONAL
            else:
                profile = ProfileType.PATIENT
            print(f"✅ Perfil alterado para: {profile.value}")
            continue

        if len(user_input) < 3:
            print("⚠️ Digite uma pergunta com pelo menos 3 caracteres.")
            continue

        print("\n⏳ Consultando bulas no PGVector e gerando resposta no Gemini...\n")
        req = QueryRequest(
            question=user_input,
            profile=profile,
            medications=medications,
        )
        res = await ai_query_endpoint(req)

        print("-" * 65)
        print(f"🚨 Nível de Alerta (alert_type): [{res.alert_type.value.upper()}]")
        if res.sources:
            print(f"📚 Fontes (RAG): {', '.join(res.sources)}")
        print("-" * 65)
        print(res.response)
        print("-" * 65)


if __name__ == "__main__":
    asyncio.run(interactive_cli())
