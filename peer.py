from threading import Thread, Timer
import socket, pickle
import random
import time

import utils
import configs

import json

class Peer(Thread):
    def __init__(self, peerAddress, id):
        Thread.__init__(self)

        self.peerAddress = peerAddress
        self.id = id

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

        index = utils.generateRandomIndex(0, len(notNeighbours)-1)

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
        while utils.run:
            neighboursList = list()
            for neighbour in self.neighboursAddress:
                t = time.time()
                if t - self.lastRecievedTime[neighbour] > configs.REMOVE_NEIGHBOUR_PERIOD:
                    self.neighboursAvailabilty[neighbour][-1][1] = t
                else:
                    neighboursList.append(neighbour)

            self.neighboursAddress = neighboursList

            self.requested = [neighbour for neighbour in self.requested if (time.time()-self.lastSentTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]
            self.oneDirNeighbours = [neighbour for neighbour in self.oneDirNeighbours if (time.time()-self.lastRecievedTime[neighbour] < configs.REMOVE_NEIGHBOUR_PERIOD)]
            time.sleep(1)

    def sendData(self):
        while utils.run:
            if self.peerIsOnline:
                for neighbour in self.neighboursAddress:
                    self.lastSentTime[neighbour] = time.time()
                    self.sock.sendto(self.createHelloPacket(neighbour) , neighbour)
                    if neighbour in self.sentPacketsNum:
                        self.sentPacketsNum[neighbour] += 1
                    else:
                        self.sentPacketsNum[neighbour] = 1
                self.sendOthers()
                time.sleep(configs.SEND_PACKET_PERIOD)

    def recieveData(self):
        while utils.run:
            if self.peerIsOnline:
                msg = f"\nPeer {self.peerAddress}: {time.time()} \n"
                try:
                    data, addr = self.sock.recvfrom(1024)

                    if random.randint(1, 100) <= configs.DROP_PERCENT:
                        continue

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

                except ConnectionResetError as e:
                    print(self.peerAddress, e)
                    continue

                msg += "\tNEIGHBOURSLIST:   " + str(self.neighboursAddress) + "\n"
                msg += "\tLASTRECIEVEDTIME:   " + str(self.lastRecievedTime) + "\n"
                self.topology[addr] = packet['neighbours']
        self.close()

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
                        self.oneDirNeighbours.append(addr)
        return msg

    def run(self):
        self.creatSocket()
        self.peerIsOnline = True

        self.sendThread = Thread(target=self.sendData, name="SendThread")
        time.sleep(0.05)
        self.sendThread.start()

        self.sock.settimeout(0.1)

        self.rcvThread = Thread(target=self.recieveData, name="RcvThread")
        time.sleep(0.05)
        self.rcvThread.start()

        self.removeNeighbourThread = Thread(target=self.removeOldNeighbours, name="removeNeighbourThread")
        self.removeNeighbourThread.start()


    def decodeHelloPacket(self, packet):
        packetData = pickle.loads(packet)
        return packetData

    def createHelloPacket(self, neighbour):
        packetData = {
            "senderId": self.id,
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

        self.updateNeighboursAvailability()

        self.clearNeighbours()

    def updateNeighboursAvailability(self):
        for neighbour in self.neighboursAddress:
            self.neighboursAvailabilty[neighbour][-1][1] = time.time()

    def clearNeighbours(self):
        self.neighboursAddress.clear()
        self.oneDirNeighbours.clear()
        self.requested.clear()

    def restartPeer(self):
        self.peerIsOnline = True

    def makeTopologyMatrix(self):
        matrix = [[0 for _ in range(configs.PEERS_NUM)] for _ in range(configs.PEERS_NUM)]
        for n in self.oneDirNeighbours:
            matrix[configs.allNodes.index(n)][configs.allNodes.index(self.peerAddress)] = 1
        for n1 in self.neighboursAddress:
            for n2 in self.topology[n1]:
                matrix[configs.allNodes.index(n1)][configs.allNodes.index(n2)] = 1
                matrix[configs.allNodes.index(n2)][configs.allNodes.index(n1)] = 1
        return matrix

    def calculateAvailability(self):
        finalAvailablity = dict()
        for neighbour in self.neighboursAvailabilty:
            sum = 0
            for t in self.neighboursAvailabilty[neighbour]:
                sum += t[1] - t[0]
            finalAvailablity[neighbour] = sum / configs.RUNNING_DURATION
        return finalAvailablity

    def writeJSON(self):
        filename = "./json/" + self.peerAddress[0] + "_" + str(self.peerAddress[1]) + ".json"
        allTimeNeighboursData = [{"peerAddress": k[0] + ":" + str(k[1]), "sentPackets": self.sentPacketsNum[k], "receivedPackets": self.recievedPacketsNum[k]} for k in self.allTimeNeighbours]
        currentNeighboursData = [{"peerAddress": k[0] + ":" + str(k[1])} for k in self.neighboursAddress]
        matrix = self.makeTopologyMatrix()
        topologyData = [{k[0] + ":" + str(k[1]): [{n[0] + ":" + str(n[1]): matrix[configs.allNodes.index(k)][configs.allNodes.index(n)]} for n in configs.allNodes]} for k in configs.allNodes]
        availability = self.calculateAvailability()
        availabilityData = [{n[0] + ":" + str(n[1]): availability[n]} for n in availability]
        data = {"peerAddress": self.peerAddress[0] + ":" + str(self.peerAddress[1]),
        "allTimeNeighbours": allTimeNeighboursData,
        "currentNeighbours": currentNeighboursData,
        "availability": availabilityData,
        "topology": topologyData,
        }
        with open(filename, 'w+') as outfile:
            json.dump(data, outfile, indent=2)


    def close(self):
        self.updateNeighboursAvailability()

        self.writeJSON()
        self.clearNeighbours()

        self.sock.close()
