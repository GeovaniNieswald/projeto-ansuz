import threading
import tkinter as tk
import time
import queue
from hugin.hugin import *
from odin.odin import *

class ThreadedClient():

    def __init__(self, master):
        self.odin = Odin(0)
        self.master = master

        self.tempo_ultima_velocidade = 0

        self.queue = queue.Queue()

        self.hugin = Hugin(master, self.queue, 50)

        self.running = 1
        self.thread1 = threading.Thread(target=self.worker_thread1)
        self.thread1.start()

        self.thread2 = threading.Thread(target=self.worker_thread2)
        self.thread2.start()

        self.periodic_call()

    def periodic_call(self):
        self.hugin.process_incoming()

        if not self.running:
            import sys
            sys.exit(1)

        self.master.after(200, self.periodic_call)

    def worker_thread1(self):
        while self.running:
            try:
                #self.odin.set_velocidade(int(input("Velocidade: ")))

                time.sleep(2)

                if self.odin.get_velocidade() > 0:
                    self.queue.put(self.odin.velocidade)
                    self.tempo_ultima_velocidade = 0
                else: 
                    self.end_application()
            except ValueError:
                print("Velocidade deve ser um numero inteiro.") 

    def worker_thread2(self):
        while self.running:
            if self.tempo_ultima_velocidade >= 10:
                self.queue.put(-99)
                self.tempo_ultima_velocidade = 0
            else:
                self.tempo_ultima_velocidade += 1
                time.sleep(1)

    def end_application(self):
        self.running = 0

root = tk.Tk()
client = ThreadedClient(root)
root.mainloop()