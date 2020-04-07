from hugin.hugin import *
from odin.odin import *

if __name__ == '__main__':
    hugin = Hugin(50)
    odin = Odin(0)
    while True:
        try:
            #odin.set_velocidade(int(input("Velocidade: ")))
            #print(odin.velocidade)

            if odin.velocidade > 0:
                hugin.processa_velocidade(odin.velocidade)
            else: 
                break 
        except ValueError:
            print("Velocidade deve ser um numero inteiro.") 

"""
from threading import Thread
import time
from hugin.hugin import *
from odin.odin import *

hugin = Hugin(50)
odin = Odin(0)

tempo_ultima_velocidade = 0

rodar = True

def thread1(threadname):
    global hugin
    global odin
    global tempo_ultima_velocidade
    global rodar

    while True:
        if rodar == False:
            break

        if tempo_ultima_velocidade >= 10:
            hugin.zera_painel()
            tempo_ultima_velocidade = 0
        else:
            tempo_ultima_velocidade += 1
            time.sleep(1)

def thread2(threadname):
    global hugin
    global odin
    global tempo_ultima_velocidade
    global rodar

    while True:
        if rodar == False:
            break

        try:
            odin.set_velocidade(int(input("Velocidade: ")))

            if odin.velocidade > 0:
                hugin.processa_velocidade(odin.velocidade)
                tempo_ultima_velocidade = 0
            else: 
                rodar = False
        except ValueError:
            print("Velocidade deve ser um numero inteiro.") 

thread1 = Thread( target=thread1, args=("Thread-1", ) )
thread2 = Thread( target=thread2, args=("Thread-2", ) )

thread1.start()
thread2.start()

thread2.join()
"""
