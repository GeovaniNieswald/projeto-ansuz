from hugin.hugin import *
from odin.odin import *

if __name__ == '__main__':
    hugin = Hugin(50)
    odin = Odin(0)
    
    while True:
        try:
            odin.set_velocidade(int(input("Velocidade: ")))

            if odin.velocidade > 0:
                hugin.processa_velocidade(odin.velocidade)
            else: 
                break 
        except ValueError:
            print("Velocidade deve ser um numero inteiro.")            