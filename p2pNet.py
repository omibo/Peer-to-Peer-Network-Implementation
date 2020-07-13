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

        self.nodes = []

    def createNodes(self):
        for i in range(configs.PEERS_NUM):
            peerIP, peerPort = f"127.0.0.1", 10001+i
            self.nodes.append((peerIP, peerPort))
            
    def deleteRandomPeer(self):
        Timer(configs.SELECT_PEER_FOR_SILENT, self.deleteRandomPeer).start()
        peerNum = random.randint(0, len(self.nodes)-1)
        print("\nDELETE: " + str(self.nodes[peerNum][1]))
        print(time.time())
        self.closePeer(self.threadConnection[peerNum])
        del self.threadConnection[peerNum]
        Timer(configs.PEER_SILENT_PERIOD, self.createPeer, [self.nodes[peerNum][0], self.nodes[peerNum][1]]).start()
        del self.nodes[peerNum]

    def createPeer(self, IP, port):
        print("\nCREATE: " + str(port))
        print(time.time())
        self.nodes.append((IP, port))
        peerThread = Peer((IP, port), self.nodes)
        self.threadConnection.append(peerThread)
        peerThread.start()

    def run(self):
        for i in range(configs.PEERS_NUM):
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
    server.start()
    time.sleep(11)
    server.deleteRandomPeer()
    if input() == 'q':
        print("IIIIIIII")
        server.close()
        server.join()