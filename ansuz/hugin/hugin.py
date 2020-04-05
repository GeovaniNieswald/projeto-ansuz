import tkinter as tk

class Hugin():

    def __init__(self, limite_velocidade):
        self.limite_velocidade = limite_velocidade
        self.window = tk.Tk()

    def processa_velocidade(self, velocidade):
        mensagem = ""
        if self.limite_velocidade >= velocidade:
            mensagem = "Tudo tranquilo"
        else:
            mensagem = "Acima do limite de velocidade"

        greeting = tk.Label(text=mensagem)
        greeting.pack()