from threading import Thread, Timer
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

    def deleteRandomPeer(self):
        Timer(configs.SELECT_PEER_FOR_SILENT, self.deleteRandomPeer).start()
        peerNum = random.randint(0, len(self.availableNodes)-1)
        print("\nDELETE: " + str(self.availableNodes[peerNum][1]) + " TIME: ", time.time())
        self.closePeer(self.threadConnection[peerNum])
        del self.threadConnection[peerNum]
        Timer(configs.PEER_SILENT_PERIOD, self.createPeer, [self.availableNodes[peerNum][0], self.availableNodes[peerNum][1]]).start()
        del self.availableNodes[peerNum]

    def createPeer(self, IP, port):
        print("\nCREATE: " + str(port) + " TIME: ", time.time())
        self.availableNodes.append((IP, port))
        self.runThread((IP, port))

    def runThread(self, address):
        peerThread = Peer(address)
        self.threadConnection.append(peerThread)
        peerThread.start()

    def run(self):
        self.startTime = time.time()
        for i in range(configs.PEERS_NUM):
            self.runThread((configs.allNodes[i]))

    def closePeer(self, thread):
        thread.close()
        thread.join()

    def close(self):
        print('Closing server and clients connections..')
        for thread in self.threadConnection:
            thread.close()
            thread.join()
        for thread in self.threadConnection:
            self.threadConnection.remove(thread)
        self.checkTimer.cancel()

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
    server.checkPeers()
    time.sleep(11)
    # server.deleteRandomPeer()
    if input() == 'q':
        print("Exiting..")
        server.close()
        server.join()