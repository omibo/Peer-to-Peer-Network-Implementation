from threading import Thread, Timer
import socket

import random

from peer import Peer

import time

PEERS_NUM = 4
NEIGHBOURS_NUM = 1

SEND_PACKET_PERIOD = 2.0
REMOVE_NEIGHBOUR_PERIOD = 8.0

PEER_SILENT_PERIOD = 20
SELECT_PERR_FOR_SILENT = 10

DROP_RATE = 5


class P2PNetwork(Thread):

    def __init__(self):
        Thread.__init__(self)

        self.threadConnection = []

        self.nodes = []

    def createNodes(self):
        for i in range(PEERS_NUM):
            peerIP, peerPort = f"127.0.0.1", 10221+i
            self.nodes.append((peerIP, peerPort))
            
    def deleteRandomPeer(self):
        Timer(SELECT_PERR_FOR_SILENT, self.deleteRandomPeer).start()
        peerNum = random.randint(0, len(self.nodes)-1)
        print("\nRANDOM NUM: " + str(peerNum))
        print("DELETE: " + self.nodes[peerNum][0] + " " + str(self.nodes[peerNum][1]))
        print(time.time())
        self.closePeer(self.threadConnection[peerNum])
        del self.threadConnection[peerNum]
        Timer(PEER_SILENT_PERIOD, self.createPeer, [self.nodes[peerNum][0], self.nodes[peerNum][1]]).start()
        del self.nodes[peerNum]

    def createPeer(self, IP, port):
        print("\nCREATE: " + IP + str(port))
        print(time.time())
        self.nodes.append((IP, port))
        peerThread = Peer((IP, port), self.nodes)
        self.threadConnection.append(peerThread)
        peerThread.start()

    def run(self):
        for i in range(PEERS_NUM):
            peerThread = Peer(self.nodes[i], self.nodes[0:i] + self.nodes[i+1:])
            self.threadConnection.append(peerThread)
            peerThread.start()

        # self.close()

    def closePeer(self, thread):
        thread.close()
        thread.join()

    def close(self):
        print('Close server and all clients connection')
        for thread in self.threadConnection:
            thread.close()
            thread.join()


if __name__ == '__main__':
    server = P2PNetwork()
    server.createNodes()
    # server.selectRandomPeer()
    server.start()
    time.sleep(10)
    server.deleteRandomPeer()
    if input() == 'q':
        print("IIIIIIII")
        server.close()
        server.join()