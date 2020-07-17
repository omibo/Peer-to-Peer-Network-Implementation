from threading import Thread, Timer
import socket
import random
import time
import configs

class Peer(Thread):
    def __init__(self, peerAddress):
        Thread.__init__(self)

        self.peerAddress = peerAddress
        self.neighboursAddress = []
        self.requested = []

        self.lastSentTime = dict()
        self.lastRecievedTime = dict()

        self.sendThread = None
        self.rcvThread = None
        self.findThread = None

        self.sock = None

    def creatSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.peerAddress)

    def removeRequest(self, address): 
        if address in self.requested:
            self.requested.remove(address)

    def request(self, address):   
        if configs.NEIGHBOURS_NUM <= len(self.requested):
            return False
        Timer(configs.REMOVE_NEIGHBOUR_PERIOD, self.removeRequest, [address]).start()
        self.requested.append(address)
        self.lastSentTime[address] = time.time()
        self.sock.sendto(self.createHelloPacket(address), address)

    def report(self):
        reminded = configs.NEIGHBOURS_NUM - len(self.neighboursAddress) 
        return reminded

    def findNeighbours(self):
        self.findThread = Timer(configs.REMOVE_NEIGHBOUR_PERIOD, self.findNeighbours)
        self.findThread.setName("FindThread")
        self.findThread.start()

        # newNeighbours = []
        # for neighbour in self.neighboursAddress:
        #     if self.lastRecievedTime.get(neighbour) is not None:
        #         if time.time() - self.lastRecievedTime.get(neighbour) > configs.REMOVE_NEIGHBOUR_PERIOD:
        #             continue
        #     newNeighbours.append(neighbour)
        # self.neighboursAddress = newNeighbours

        reminded = configs.NEIGHBOURS_NUM - len(self.neighboursAddress) 
        for i in range(reminded):
            notNeighbours = list(set(configs.allNodes).difference(self.neighboursAddress).difference([self.peerAddress]))
            randomPeer = random.randint(0, len(notNeighbours)-1)
            self.request(notNeighbours[randomPeer])
    
    def removeOldNeighbours(self):
        self.removeNeighbourThread = Timer(1, self.removeOldNeighbours)
        self.removeNeighbourThread.setName("RemoveNeighbourThread")
        self.removeNeighbourThread.start()

        tempNeighbours = []
        for neighbour in self.neighboursAddress:
            if self.lastRecievedTime[neighbour] > configs.REMOVE_NEIGHBOUR_PERIOD:
                continue
            tempNeighbours.append(neighbour)
        self.neighboursAddress = tempNeighbours



    def sendData(self):
        self.sendThread = Timer(configs.SEND_PACKET_PERIOD, self.sendData)
        self.sendThread.setName("SendThread")
        self.sendThread.start()

        for neighbour in self.neighboursAddress:
            self.lastSentTime[neighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(neighbour) , neighbour)

    def recieveData(self):
        while True:
            msg = f"\nPeer {self.peerAddress}:\n"
            try:
                data, addr = self.sock.recvfrom(1024)
                
                if random.randint(1, 100) <= configs.DROP_PERCENT:
                    continue

                packet = self.decodeHelloPacket(data)

                if configs.NEIGHBOURS_NUM > len(self.neighboursAddress):
                    if addr in self.requested:
                        self.removeRequest(addr)
                        self.neighboursAddress.append(addr)           
                    elif self.peerAddress not in packet['neighbours']:
                        if configs.NEIGHBOURS_NUM > len(self.requested):
                            self.request(addr)

                msg += "\tpacket " + str(packet['neighbours']) + " SndPeer " + str(data) + "\n"
                msg += "\trequested " + str(self.requested) + "\n"
                self.lastRecievedTime[addr] = time.time()
            except socket.timeout:
                continue

            msg += "\tNEIGHBOURSLIST:   " + str(self.neighboursAddress) + "\n"
            msg += "\tLASTRECIEVEDTIME:   " + str(self.lastRecievedTime)
            # print(msg)



    def run(self):
        self.createSocket()
        time.sleep(1)
        self.findNeighbours()

        self.sendData()
        self.sock.settimeout(0.1)
        
        self.rcvThread = Thread(target=self.recieveData)
        self.rcvThread.setName("RcvThread")
        self.rcvThread.start()

        # self.sock.closse()

    def decodeHelloPacket(self, packet):
        packetData = pickle.loads(packet)
        return packetData

    def createHelloPacket(self, neighbour):
        packetData = {
            "senderId": "senderId",
            "senderAddress": self.peerAddress,
            "packetType": "packetType",
            "neighbours": self.neighboursAddress,
            "lastSentTime": self.lastSentTime.get(neighbour),
            "lastRecievedTime": self.lastRecievedTime.get(neighbour)
        }
        packetData = pickle.dumps(packetData)
        return packetData

    def close(self):
        self.sendThread.cancel()
        self.rcvThread.cancel()
        self.findThread.cancel()

        # self.sendThread.join()
        # self.rcvThread.join()
        # self.findThread.join()

        self.sock.close()
