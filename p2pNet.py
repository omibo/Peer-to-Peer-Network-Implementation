from threading import Thread, Timer, enumerate
import socket

import random

from peer import Peer

import time
import configs

import utils

class P2PNetwork(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.threadConnection = []
        self.availableNodes = configs.allNodes
        self.checkTimer = None

    def silentPeer(self):
        if (utils.run):
            self.silentPeerThread = Timer(configs.SELECT_PEER_FOR_SILENT, self.silentPeer)
            self.silentPeerThread.start()
            peerNum = None

            while True:
                peerNum = random.randint(0, len(self.availableNodes)-1)
                if self.threadConnection[peerNum].peerIsOnline:
                    break

            print("\nDELETE: " + str(self.availableNodes[peerNum][1]) + " TIME: ", time.time()%60)
            self.threadConnection[peerNum].silentPeer()
            self.restartThread = Timer(configs.PEER_SILENT_PERIOD + 0.01, self.restartPeer, [peerNum])
            self.restartThread.start()

    def restartPeer(self, peerNum):
        if utils.run:
            print("\nCREATE: " + str(self.threadConnection[peerNum].peerAddress[1]) + " TIME: ", time.time()%60)
            self.threadConnection[peerNum].restartPeer()

    def run(self):
        self.startTime = time.time()
        for i in range(configs.PEERS_NUM):
            address = configs.allNodes[i]
            id = configs.allNodes[i][1] - configs.startPort
            peerThread = Peer(address, id)
            self.threadConnection.append(peerThread)
            peerThread.start()

    def close(self):
        utils.run = False
        print('Closing server and clients connections..')
        self.checkTimer.cancel()
        for thread in self.threadConnection:
            self.threadConnection.remove(thread)

    def checkPeers(self):
        self.checkTimer = Timer(2, self.checkPeers)
        self.checkTimer.start()
        msg =  "\nTime: " + str(time.time() % 60)
        for thread in self.threadConnection:
            msg += f"\n{thread.peerAddress[1]} id: {thread.id} ({'on ' if thread.peerIsOnline else 'off'})"
            msg += "\tneighbours: {"
            for n in thread.neighboursAddress:
                msg += f" {n[1]}"
            msg += " } \trequested: {"
            for n in thread.requested:
                msg += f" {n[1]}"
            msg += " } \t oneDirNeighbour: {"
            for n in thread.oneDirNeighbours:
                msg += f" {n[1]}"
            msg += " }"
        print(msg + "\n")

if __name__ == '__main__':
    try:
        startTime = time.time()
        server = P2PNetwork()
        server.start()
        time.sleep(1)
        server.checkPeers()
        time.sleep(9)
        server.silentPeer()

        deltaT = time.time() - startTime
        time.sleep(configs.RUNNING_DURATION - deltaT)

    except KeyboardInterrupt as e:
        pass

    print(f"Exiting after ({int(time.time() - startTime)}) seconds...")
    server.close()
    server.join()
    while(len(enumerate()) > 1):
        pass
