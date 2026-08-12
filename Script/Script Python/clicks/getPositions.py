import pyautogui
import time

print("Você possui 5 segundos para clicar no back e retornar a tela anterior")
time.sleep(5)
print(f"Coordenada do backspace: {pyautogui.position()}")

print("Você possui 5 segundos para colocar o mouse em cima do label")
time.sleep(5)
print(f"Coordenadas da escrita do nome do medicamento: {pyautogui.position()}")

print("Você possui 10 segundos para colocar o mouse no botão de download do pdf")
time.sleep(10)
print(f"Coordenadas do botão de download do pdf {pyautogui.position()}")
