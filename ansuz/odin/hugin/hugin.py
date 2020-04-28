import tkinter as tk
import random
import queue

class Hugin():

    mensagens_positivas = ['VOCÊ ESTÁ DENTRO DO LIMITE DE VELOCIDADE', 'VOCÊ TORNA O TRÂNSITO MAIS SEGURO', 'SUA RESPONSABILIDADE É O MELHOR EXEMPLO', 'SUA ATITUDE PODE SALVAR VIDAS']
    mensagens_negativas = ['A VIDA PASSA RÁPIDO. NÃO A ACELERE MAIS', 'RESPEITAR OS LIMITES DE VELOCIDADE PODE SALVAR VIDAS', 'VOCÊ ESTÁ COLOCANDO A SUA E A VIDA DOS OUTROS EM RISCO', 'AO DIRIGIR, ESQUEÇA A PRESSA: A VELOCIDADE MATA']

    def __init__(self, window, queue, limite_velocidade):
        self.queue = queue
        
        self.limite_velocidade = limite_velocidade

        self.window = window
        self.window.title('Módulo Hugin')
        self.window.attributes('-fullscreen', True) 

        width = window.winfo_screenwidth()
        height = window.winfo_screenheight()

        #self.window.geometry('500x500')
        #self.window.resizable(0, 0)
        #width = 500
        #height = 500

        self.frame = tk.Frame(self.window, bg = 'black', width = width, height = height)
        self.frame.grid(row = 0, column = 0, sticky = 'NW')
        self.frame.grid_propagate(0)
        self.frame.update()

        centro_x = width / 2
        centro_y = height / 2
        font_size = int(height / 20)

        self.label_mensagem = tk.Label(self.frame, text = '', bg = 'black', fg = 'red', font = ("Helvetica", font_size), wraplength = width - 20, justify = 'center')
        self.label_mensagem.place(x = centro_x, y = centro_y, anchor='center')

    def process_incoming(self):
        while self.queue.qsize():
            try:
                parametro = self.queue.get(0)

                if parametro == -99:
                    self.__zera_painel()
                else: 
                    mensagem = str(parametro) + ' KM/H'
                    cor = ''

                    if self.limite_velocidade >= parametro:
                        mensagem += ' - PARABÉNS \n\n' + Hugin.mensagens_positivas[self.__msg_rand()]
                        cor = 'green'
                    else:
                        mensagem += ' - ATENÇÃO \n\n' + Hugin.mensagens_negativas[self.__msg_rand()]
                        cor = 'red'

                    self.label_mensagem.configure(text = mensagem, fg = cor)
            except queue.Empty:
                pass

    def __zera_painel(self):
        self.label_mensagem.configure(text = '')

    def __msg_rand(self):
        limite = len(Hugin.mensagens_negativas) - 1
        rand_num = random.randint(0, limite)
 
        return rand_num