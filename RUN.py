from threading import Thread
import os

def diceApplier():
    os.system("python diceApplier.py --headless")

def monsterApplier():
    os.system("python monsterApplier.py --headless")


diceThread = Thread(target=diceApplier)
monsterThread = Thread(target=monsterApplier)

diceThread.start()
monsterThread.start()
