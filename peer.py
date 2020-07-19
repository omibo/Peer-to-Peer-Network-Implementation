from threading import Thread, Timer
import socket, pickle
import random
import time

from utils import generateRandomIndices
import configs

from stoppableThread import StoppableThread

class Peer(Thread):
    def __init__(self, peerAddress):
        Thread.__init__(self)

        self.peerAddress = peerAddress

        self.oneDirNeighbours = []
        self.neighboursAddress = []
        self.requested = []

        self.lastSentTime = dict()
        self.lastRecievedTime = dict()

        self.peerIsOnline = False

        self.sock = None

    def creatSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.peerAddress)

    def findNewNeighbour(self):
        notNeighbours = list(set(configs.allNodes).difference(self.neighboursAddress).difference([self.peerAddress]))
        indices = generateRandomIndices(0, len(notNeighbours)-1, 1)

        if notNeighbours[indices[0]] not in self.requested:
            self.requested.append(notNeighbours[indices[0]])

        self.lastSentTime[notNeighbours[indices[0]]] = time.time()
        return notNeighbours[indices[0]]

    def sendOthers(self):
        if configs.NEIGHBOURS_NUM <= len(self.neighboursAddress):
            return

        a = self.findNewNeighbour()
        print(f"{self.peerAddress} has New Requested {a} Time: {time.time() % 60}")
        for tempNeighbour in self.oneDirNeighbours + self.requested:
            self.lastSentTime[tempNeighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(tempNeighbour) , tempNeighbour)

    def removeOldNeighbours(self):
        self.removeNeighbourThread = Timer(1, self.removeOldNeighbours)
        self.removeNeighbourThread.setName("RemoveNeighbourThread")
        self.removeNeighbourThread.start()

        self.neighboursAddress = [neighbour for neighbour in self.neighboursAddress if (time.time()-self.lastRecievedTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]
        self.requested = [neighbour for neighbour in self.requested if (time.time()-self.lastSentTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]
        self.oneDirNeighbours = [neighbour for neighbour in self.oneDirNeighbours if (time.time()-self.lastRecievedTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]

    def sendData(self):
        self.sendThread = Timer(configs.SEND_PACKET_PERIOD, self.sendData)
        self.sendThread.setName("SendThread")
        self.sendThread.start()

        for neighbour in self.neighboursAddress:
            self.lastSentTime[neighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(neighbour) , neighbour)
        self.sendOthers()

    def recieveData(self):
        while True:
            msg = f"\nPeer {self.peerAddress}: {time.time()} \n"
            try:
                data, addr = self.sock.recvfrom(1024)

                # if random.randint(1, 100) <= configs.DROP_PERCENT:
                #     continue

                packet = self.decodeHelloPacket(data)
                msg += self.handlePacketState(packet)

                msg += "\tpacket " + str(packet) + "\n"
                msg += "\trequested " + str(self.requested) + "\n"
                self.lastRecievedTime[addr] = time.time()
            except socket.timeout:
                continue

            msg += "\tNEIGHBOURSLIST:   " + str(self.neighboursAddress) + "\n"
            msg += "\tLASTRECIEVEDTIME:   " + str(self.lastRecievedTime) + "\n"
            # print(msg)

    def handlePacketState(self, packet):
        msg = ""
        addr = packet['senderAddress']

        if (configs.NEIGHBOURS_NUM > len(self.neighboursAddress)) and (addr not in self.neighboursAddress):
            if addr in self.requested:
                
                try:
                    self.oneDirNeighbours.remove(addr)
                except ValueError:
                    pass

                self.requested.remove(addr)
                self.neighboursAddress.append(addr)
                msg += f"\tNewNighbour Hoooora: {addr}\n"
            elif self.peerAddress in packet['neighbours']:
                self.neighboursAddress.append(addr)
                
                try:
                    self.oneDirNeighbours.remove(addr)
                except ValueError:
                    pass
                
                msg += f"\tNewNighbour Hoooora: {addr}\n"
            elif self.peerAddress not in packet['neighbours']:
                if configs.NEIGHBOURS_NUM > len(self.requested):
                    if addr not in self.oneDirNeighbours:
                        self.oneDirNeighbours.append(addr)
        return msg

    def run(self):
        self.creatSocket()
        self.peerIsOnline = True
        # self.findNeighbours()

        self.sendData()
        self.sock.settimeout(0.1)

        self.rcvThread = StoppableThread(target=self.recieveData)
        self.rcvThread.setName("RcvThread")
        self.rcvThread.start()
        self.removeOldNeighbours()

        # self.sock.closse()

    def decodeHelloPacket(self, packet):
        packetData = pickle.loads(packet)
        return packetData

    def createHelloPacket(self, neighbour):
        packetData = {
            "senderId": "",
            "senderAddress": self.peerAddress,
            "packetType": "Hello",
            "neighbours": self.neighboursAddress,
            "lastSentTime": self.lastSentTime.get(neighbour),
            "lastRecievedTime": self.lastRecievedTime.get(neighbour)
        }
        packetData = pickle.dumps(packetData)
        return packetData

    def silentPeer(self):
        self.peerIsOnline = False
        self.close()
    
    def restartPeer(self):
        self.run()

    def close(self):

        self.neighboursAddress.clear()
        self.oneDirNeighbours.clear()
        self.requested.clear()

        self.sendThread.cancel()
        self.rcvThread.stop()
        self.removeNeighbourThread.cancel()

        # self.sendThread.join()
        # self.rcvThread.join()

        self.sock.close()
