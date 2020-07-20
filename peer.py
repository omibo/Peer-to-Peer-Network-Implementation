from threading import Thread, Timer
import socket, pickle
import random
import time

from utils import generateRandomIndex
import configs

from stoppableThread import StoppableThread

import json

class Peer(Thread):
    def __init__(self, peerAddress):
        Thread.__init__(self)

        self.peerAddress = peerAddress

        self.oneDirNeighbours = []
        self.neighboursAddress = []
        self.requested = []
        self.tempNeighbour = None

        self.lastSentTime = dict()
        self.lastRecievedTime = dict()

        self.peerIsOnline = False

        self.sock = None

        self.recievedPacketsNum = dict()
        self.sentPacketsNum = dict()
        self.allTimeNeighbours = set()
        self.neighboursAvailabilty = dict()
        self.topology = dict()

    def creatSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.peerAddress)

    def findNewNeighbour(self):
        notNeighbours = list(set(configs.allNodes).difference(self.neighboursAddress).difference([self.peerAddress]).difference(self.requested))
        if len(notNeighbours) < 1:
            return []

        index = generateRandomIndex(0, len(notNeighbours)-1)

        self.tempNeighbour = notNeighbours[index]
        self.requested.append(self.tempNeighbour)

        self.lastSentTime[self.tempNeighbour] = time.time()
        print(f"{self.peerAddress} has New Requested {self.tempNeighbour} Time: {time.time() % 60}")
        return [self.tempNeighbour]

    def sendOthers(self):
        if configs.NEIGHBOURS_NUM <= len(self.neighboursAddress):
            return

        a = self.findNewNeighbour()

        for tempNeighbour in self.oneDirNeighbours + a:
            self.lastSentTime[tempNeighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(tempNeighbour) , tempNeighbour)
            if tempNeighbour in self.sentPacketsNum:
                self.sentPacketsNum[tempNeighbour] += 1
            else:
                self.sentPacketsNum[tempNeighbour] = 1
        self.tempNeighbour = None

    def removeOldNeighbours(self):
        self.removeNeighbourThread = Timer(1, self.removeOldNeighbours)
        self.removeNeighbourThread.setName("RemoveNeighbourThread")
        self.removeNeighbourThread.start()

        neighboursList = list()
        for neighbour in self.neighboursAddress:
            t = time.time()
            if t - self.lastRecievedTime[neighbour] > 8:
                self.neighboursAvailabilty[neighbour][-1][1] = t
            else:
                neighboursList.append(neighbour)

        self.neighboursAddress = neighboursList

        self.requested = [neighbour for neighbour in self.requested if (time.time()-self.lastSentTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]
        self.oneDirNeighbours = [neighbour for neighbour in self.oneDirNeighbours if (time.time()-self.lastRecievedTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]

    def sendData(self):
        self.sendThread = Timer(configs.SEND_PACKET_PERIOD, self.sendData)
        self.sendThread.setName("SendThread")
        self.sendThread.start()

        for neighbour in self.neighboursAddress:
            self.lastSentTime[neighbour] = time.time()
            self.sock.sendto(self.createHelloPacket(neighbour) , neighbour)
            if neighbour in self.sentPacketsNum:
                self.sentPacketsNum[neighbour] += 1
            else:
                self.sentPacketsNum[neighbour] = 1
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
                if addr in self.recievedPacketsNum:
                    self.recievedPacketsNum[addr] += 1
                else:
                    self.recievedPacketsNum[addr] = 1
            except socket.timeout:
                continue
            except OSError:
                print(self.sock._closed)
                time.sleep(0.1)
                continue

            msg += "\tNEIGHBOURSLIST:   " + str(self.neighboursAddress) + "\n"
            msg += "\tLASTRECIEVEDTIME:   " + str(self.lastRecievedTime) + "\n"
            self.topology[addr] = packet['neighbours']

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
                self.allTimeNeighbours.add(addr)
                self.neighboursAddress.append(addr)

                try:
                    self.neighboursAvailabilty[addr].append([time.time(), -1])
                except:
                    self.neighboursAvailabilty[addr] = [[time.time(), -1]]

                msg += f"\tNewNighbour Hoooora: {addr}\n"
            elif self.peerAddress in packet['neighbours']:
                self.neighboursAddress.append(addr)

                try:
                    self.neighboursAvailabilty[addr].append([time.time(), -1])
                except:
                    self.neighboursAvailabilty[addr] = [[time.time(), -1]]

                self.allTimeNeighbours.add(addr)

                try:
                    self.oneDirNeighbours.remove(addr)
                except ValueError:
                    pass

                msg += f"\tNewNighbour Hoooora: {addr}\n"
            elif self.peerAddress not in packet['neighbours']:
                if configs.NEIGHBOURS_NUM > len(self.requested):
                    if addr not in self.oneDirNeighbours:
                        # self.allTimeNeighbours.add(addr)
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
        for neighbour in self.neighboursAddress:
            self.neighboursAvailabilty[neighbour][-1][1] = time.time()
        self.close()

    def restartPeer(self):
        self.run()

    def writeJSON(self):
        filename = "./json/" + str(self.peerAddress[1]) + ".json"
        allTimeNeighboursData = [{"peerIP": k[0], "peerPort": k[1], "sentPackets": self.sentPacketsNum[k], "receivedPackets": self.recievedPacketsNum[k]} for k in self.allTimeNeighbours]
        currentNeighboursData = [{"peerIP": k[0], "peerPort": k[1]} for k in self.neighboursAddress]
        topologyData = [{"peerIP": k[0], "peerPort": k[1], "neighbours": [{"peerIP": n[0], "peerPort": n[1]} for n in self.topology[k]]} for k in self.neighboursAddress]
        data = {"allTimeNeighbours": allTimeNeighboursData, "currentNeighbours": currentNeighboursData, "topology": topologyData}
        print(f"{self.peerAddress} ::: ")
        print(self.neighboursAvailabilty)
        with open(filename, 'w+') as outfile:
            json.dump(data, outfile, indent=2)

    def close(self):
        self.writeJSON()
        self.neighboursAddress.clear()
        self.oneDirNeighbours.clear()
        self.requested.clear()

        self.sendThread.cancel()
        self.rcvThread.stop()
        self.removeNeighbourThread.cancel()

        # self.sendThread.join()
        # self.rcvThread.join()

        while self.rcvThread.is_alive() or self.sendThread.is_alive() or self.removeNeighbourThread.is_alive():
            time.sleep(0.5)
            print(f"\nClosing {self.peerAddress} {(self.rcvThread.is_alive(), self.sendThread.is_alive(), self.removeNeighbourThread.is_alive())}\n")
        self.sock.close()
