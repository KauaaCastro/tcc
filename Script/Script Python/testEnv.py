import sys
import os

print(f"Versão do Python: {sys.version}")
print(f"Caminho do Executável: {sys.executable}")

try:
    import cv2
    print("✅ SUCESSO: OpenCV (cv2) está instalado corretamente!")
except ImportError:
    print("❌ ERRO: OpenCV não encontrado neste ambiente.")
    print("\nExecute este comando EXATO no seu terminal:")
    print(f"{sys.executable} -m pip install opencv-python")