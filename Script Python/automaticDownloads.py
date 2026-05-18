import pyautogui
import os
import time
import glob

DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads", "estudos", "tcc", "Bulário")
REPORTS_PATH = os.path.join("C:\\", "workspace", "TCC", "Script Python", "Relatorio de erros")

# # Notebook
# RETURN_BUTTON = (76, 68)
# NAME_LABEL = (421, 505)
# PDF_DOWNLOAD = (1384, 568)

# Monitor 
RETURN_BUTTON = (60, 57)
NAME_LABEL = (661, 442)
PDF_DOWNLOAD = (1340, 493)


def garantir_pasta(caminho):
    """Cria a pasta se não existir. Retorna True se OK, False se falhar."""
    try:
        if not os.path.exists(caminho):
            os.makedirs(caminho, exist_ok=True)
            print(f"  📁 Pasta criada: {caminho}")
        return True
    except OSError as e:
        print(f"  ⚠️  Não foi possível criar a pasta '{caminho}': {e}")
        return False


def salvar_relatorio(falhas_ordenadas):
    """Tenta salvar o relatório no caminho definido. Se falhar, tenta no diretório atual."""
    pasta_ok = garantir_pasta(REPORTS_PATH)

    if pasta_ok:
        caminho_relatorio = os.path.join(REPORTS_PATH, "relatorio_erros.txt")
    else:
        print("  ⚠️  Salvando relatório no diretório atual como fallback.")
        caminho_relatorio = "relatorio_erros.txt"

    try:
        with open(caminho_relatorio, "w", encoding="utf-8") as log:
            log.write("RELATÓRIO DE FALHAS - TCC\n")
            log.write(f"Total não encontrados: {len(falhas_ordenadas)}\n")
            log.write("-" * 30 + "\n")
            for item in falhas_ordenadas:
                log.write(f"{item}\n")
        print(f"  Relatório salvo em: {caminho_relatorio}")
    except OSError as e:
        print(f"  ⚠️  Erro ao salvar relatório: {e}")


def downloads():
    print("Iniciando automação...")

    if not os.path.exists("ListaMedicamento.txt"):
        print("Arquivo 'ListaMedicamento.txt' não encontrado no diretório atual!")
        return

    if not garantir_pasta(DOWNLOAD_PATH):
        print("Não foi possível acessar/criar a pasta de downloads. Encerrando.")
        return

    with open("ListaMedicamento.txt", "r", encoding="utf-8") as f:
        remedios = [linha.strip() for linha in f if linha.strip()]

    falhas = []

    print(f"{len(remedios)} medicamento(s) encontrado(s) na lista.")
    print("Abra o navegador e deixe em tela cheia.")
    time.sleep(2)

    for i, name in enumerate(remedios, start=1):
        print(f"\n[{i}/{len(remedios)}] Buscando: {name}")

        horario_inicio_busca = time.time()

        pyautogui.click(NAME_LABEL)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(name, interval=0.05)
        pyautogui.press('enter')
        time.sleep(2)

        pyautogui.click(PDF_DOWNLOAD)
        time.sleep(2)

        pyautogui.click(RETURN_BUTTON)

        arquivo_encontrado = False

        for tentativa in range(1, 7):
            time.sleep(2)
            pdfList = glob.glob(os.path.join(DOWNLOAD_PATH, "*.pdf"))

            if pdfList:
                ultimo_pdf = max(pdfList, key=os.path.getctime)
                data_criacao = os.path.getctime(ultimo_pdf)

                if data_criacao > horario_inicio_busca:
                    new_name = f"bula_{name.lower().replace(' ', '-')}.pdf"
                    new_path = os.path.join(DOWNLOAD_PATH, new_name)

                    try:
                        os.rename(ultimo_pdf, new_path)
                        print(f"  ✅ SUCESSO: {new_name}")
                        arquivo_encontrado = True
                        break
                    except OSError:
                        print(f"  ⏳ Arquivo ainda bloqueado, tentativa {tentativa}/6...")
                        continue

        if not arquivo_encontrado:
            print(f"  ❌ FALHA: download não detectado para '{name}'")
            falhas.append(name)
            pyautogui.press('esc')

    # Relatório no terminal
    print("\n" + "=" * 40)
    print("         RELATÓRIO FINAL")
    print("=" * 40)
    print(f"Total de medicamentos : {len(remedios)}")
    print(f"Sucessos              : {len(remedios) - len(falhas)}")
    print(f"Falhas                : {len(falhas)}")

    if falhas:
        falhas_ordenadas = sorted(falhas)
        print("\nMedicamentos sem download (em ordem):")
        for idx, item in enumerate(falhas_ordenadas, start=1):
            print(f"  {idx:>3}. {item}")

        salvar_relatorio(falhas_ordenadas)
    else:
        print("\n🎉 Todos os downloads foram concluídos com sucesso!")

    print("=" * 40)


if __name__ == "__main__":
    downloads()