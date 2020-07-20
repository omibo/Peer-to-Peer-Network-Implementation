import random

def generateRandomIndex(start, end):
    try:
        return random.randint(start, end)
    except:
        pass