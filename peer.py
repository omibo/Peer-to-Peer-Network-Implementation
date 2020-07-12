from threading import Thread, Timer
import socket

import time

PEERS_NUM = 6
NEIGHBOURS_NUM = 1

SEND_PACKET_PERIOD = 2.0
REMOVE_NEIGHBOUR_PERIOD = 8.0

PEER_SILENT_PERIOD = 20
SELECT_PERR_FOR_SILENT = 10

DROP_RATE = 5

class Peer(Thread):
    def __init__(self, peerAddress, neighboursAddress):
        Thread.__init__(self)

        self.peerAddress = peerAddress
        self.neighboursAddress = neighboursAddress

        self.lastSentTime = [0] * len(neighboursAddress)
        self.lastRecievedTime = [0] * len(neighboursAddress)

        self.sock = None

    def creatSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.peerAddress)

    def sendData(self):
        Timer(SEND_PACKET_PERIOD, self.sendData).start()
        for i in range(len(self.neighboursAddress)):
            self.lastSentTime[i] = time.time()
            self.sock.sendto(self.createHelloPacket(i) , self.neighboursAddress[i])

    def recieveData(self):
        Timer(SEND_PACKET_PERIOD, self.recieveData).start()
        for i in range(len(self.neighboursAddress)):
            a, b = self.sock.recvfrom(1024)
            print("I " + str(self.peerAddress) + " rcv " + str(a))
            self.lastRecievedTime[i] = time.time()

    def run(self):
        self.creatSocket()

        time.sleep(2)

        self.sendData()
        self.sock.settimeout(0.1)
        self.recieveData()

        # self.sock.closse()

    def createHelloPacket(self, i):
        pakcetData = f"SenderId, {self.peerAddress[0]}, {str(self.peerAddress[1])}, PacketType, Neighbours, {self.lastSentTime[i]}, {self.lastRecievedTime[i]}"
        return bytes(pakcetData, "utf-8")

    def close(self):
        self.sock.close()
