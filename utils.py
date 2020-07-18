import random

def generateRandomIndices(start, end, N):
    selectedIndices = set()
    while len(selectedIndices) < N:
        i = random.randint(start, end)
        if i not in selectedIndices:
            selectedIndices.add(i)
    return list(selectedIndices)