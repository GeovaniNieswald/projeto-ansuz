import tkinter as tk
import random
import queue

class Hugin():

    mensagens_positivas = ['Tudo tranquilo', 'Tudo certo', 'Parabéns você está dentro do limite de velocidade', 'É isso ai']
    mensagens_negativas = ['Acima do limite de velocidade', 'Atenção você está acima do limite de velocidade', 'Você está colocando a sua e a vida dos outros em risco', 'Devagar cabeça']

    def __init__(self, window, queue, limite_velocidade):
        self.queue = queue
        
        self.limite_velocidade = limite_velocidade

        self.window = window
        self.window.title('Módulo Hugin')
        self.window.geometry('500x500')
        self.window.resizable(0, 0)
        
        self.frame = tk.Frame(self.window, bg='black', width=500, height=500)
        self.frame.grid(row=0, column=0, sticky="NW")
        self.frame.grid_propagate(0)
        self.frame.update()

        self.label_velocidade = tk.Label(self.frame, text="", bg='black', fg='red')
        self.label_velocidade.place(x=250, y=230, anchor='center')

        self.label_mensagem = tk.Label(self.frame, text="", bg='black', fg='red')
        self.label_mensagem.place(x=250, y=250, anchor='center')

    def process_incoming(self):
        while self.queue.qsize():
            try:
                parametro = self.queue.get(0)

                if parametro == -99:
                    self.__zera_painel()
                else: 
                    mensagem = ''
                    cor = ''
                    if self.limite_velocidade >= parametro:
                        mensagem = Hugin.mensagens_positivas[self.__msg_rand()]
                        cor = 'green'
                    else:
                        mensagem = Hugin.mensagens_negativas[self.__msg_rand()]
                        cor = 'red'

                    self.label_velocidade.configure(text=parametro, fg=cor) 
                    self.label_mensagem.configure(text=mensagem, fg=cor)
            except queue.Empty:
                pass

    def __zera_painel(self):
        self.label_velocidade.configure(text='') 
        self.label_mensagem.configure(text='')

    def __msg_rand(self):
        limite = len(Hugin.mensagens_negativas) - 1
        rand_num = random.randint(0, limite)
 
        return rand_num