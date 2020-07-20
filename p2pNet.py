from threading import Thread, Timer, enumerate
import socket

import random

from peer import Peer

import time
import configs


class P2PNetwork(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.threadConnection = []
        self.availableNodes = configs.allNodes
        self.checkTimer = None

    def silentPeer(self):
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
        print("\nCREATE: " + str(self.threadConnection[peerNum].peerAddress[1]) + " TIME: ", time.time()%60)
        self.threadConnection[peerNum].restartPeer()
        self.restartThread.cancel()

    def run(self):
        self.startTime = time.time()
        for i in range(configs.PEERS_NUM):
            peerThread = Peer(configs.allNodes[i])
            self.threadConnection.append(peerThread)
            peerThread.start()

    def close(self):
        self.checkTimer.cancel()
        self.silentPeerThread.cancel()
        server.restartThread.cancel()
        print('Closing server and clients connections..')
        for thread in self.threadConnection:
            thread.close()
            thread.join()
        for thread in self.threadConnection:
            self.threadConnection.remove(thread)

    def checkPeers(self):
        self.checkTimer = Timer(2, self.checkPeers)
        self.checkTimer.start()
        notCompleted = configs.PEERS_NUM
        msg = ""
        for thread in self.threadConnection:
            msg += f"\n{thread.peerAddress[1]}"
            msg += "\tneighbours: {"
            for n in thread.neighboursAddress:
                msg += f" {n[1]}"
            msg += " } \trequested: {"
            for n in thread.requested:
                msg += f" {n[1]}"
            msg += " } \t oneDirNeighbour: {"
            for n in thread.oneDirNeighbours:
                msg += f" {n[1]}"
            msg += " } \t Time: " + str(time.time() % 60)
        print(msg + "\n")
        # for thread in self.threadConnection:
        #     print(thread.peerAddress ,thread.report())
        #     if thread.report() == 0:
        #         notCompleted -= 1
        # if notCompleted == 0:
        #     print(time.time() - self.startTime)
        #     self.close()

if __name__ == '__main__':
    server = P2PNetwork()
    server.start()
    time.sleep(1)
    server.checkPeers()
    time.sleep(9)
    server.silentPeer()

    if input() == 'q':
        print("Exiting..")
        server.close()
        server.join()
        while(len(enumerate()) > 1):
            pass
