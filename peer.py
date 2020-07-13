from threading import Thread, Timer
import socket

import time

PEERS_NUM = 4
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

        self.lastSentTime = dict()
        self.lastRecievedTime = dict()

        self.sendThread = None
        self.rcvThread = None

        self.sock = None

    def creatSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.peerAddress)

    def sendData(self):
        self.sendThread = Timer(SEND_PACKET_PERIOD, self.sendData)
        self.sendThread.start()
        for neighbour in self.neighboursAddress:
            self.lastSentTime[neighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(neighbour) , neighbour)

    def recieveData(self):
        self.rcvThread = Timer(SEND_PACKET_PERIOD, self.recieveData)
        self.rcvThread.start()

        newNeighbours = []

        msg = f"Peer {self.peerAddress}:\n"

        for neighbour in self.neighboursAddress:
            if self.lastRecievedTime.get(neighbour) is not None:
                if time.time() - self.lastRecievedTime.get(neighbour) > 8:
                    continue
            newNeighbours.append(neighbour)
            try:
                a, b = self.sock.recvfrom(1024)
                msg += "\tpacket " + str(a) + " SndPeer " + str(b) + "\n"
                self.lastRecievedTime[b] = time.time()
            except socket.timeout:
                pass
        self.neighboursAddress = newNeighbours
        
        msg += "\tNEIGHBOURSLIST:   " + str(self.neighboursAddress) + "\n"
        msg += "\tLASTRECIEVEDTIME:   " + str(self.lastRecievedTime)
        print(msg)


    def run(self):
        self.creatSocket()

        time.sleep(1)

        self.sendData()
        self.sock.settimeout(0.1)
        self.recieveData()
        

        # self.sock.closse()

    def createHelloPacket(self, neighbour):
        pakcetData = f"SenderId, {self.peerAddress[0]}, {str(self.peerAddress[1])}, PacketType, Neighbours, {self.lastSentTime.get(neighbour)}, {self.lastRecievedTime.get(neighbour)}"
        return bytes(pakcetData, "utf-8")

    def close(self):
        self.sendThread.cancel()
        self.rcvThread.cancel()
        self.sock.close()
