import base64
import socket
import struct
import itertools
import selectors
import random
import time
import string
import pickle

class zerg:
    # Get it get it it's a zerg rush
    # StarCraft ref - they're played by bruteforce :D
    # like here :D
    # until we can bamboozle the server that is

    def __init__(self, name: str = ""):
        print("alifhusidfh")
        self.sel = selectors.DefaultSelector()
        self.name = name



        self.mCastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mCastSock.settimeout(2)
        self.MCAST_TTL = struct.pack('b', 1)
        self.MCAST_GRP = '224.3.29.71' # what we put here
        self.MCAST_PORT = 10000
        self.HOST = "172.17.0.2" # "host.docker.internal"
        self.PORT = 8000
        self.server_address = ('', 10000)
        self.mCastSock.bind(self.server_address)

        group = socket.inet_aton(self.MCAST_GRP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


        self.sel.register(self.mCastSock, selectors.EVENT_READ, self.recvMCAST)                   # Listen for socket activity


    def fds(self):
        print("oh look a message")

    def sayHello(self):
        '''Get a hello message''' #Hello there
        msg={
            'command':'hello'
        }
        encodedMSG = pickle.dumps(msg)        

        print("Slave",self.name+":","sending HELLO message:",msg)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        while True:
            print("Slave",self.name+":","waiting to recieve. sayhellow")
            try:
                data, server = self.mCastSock.recvfrom(1024)
            except socket.timeout:
                print("Slave",self.name+":","timed out, no more responses.")
                break
            else:
                print("Slave",self.name+":","recieved:",data,"from",server)
                
                recvMSG = pickle.loads(data) # I'm here message
                print("received:",recvMSG)
        return 


    def sendMCAST(self, msg):
        print("Slave",self.name+":","sending message:",msg)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(msg, (self.MCAST_GRP, self.MCAST_PORT))
        while True:
            print("Slave",self.name+":","waiting to recieve sendmcast.")
            try:
                data, server = mCastSock.recvfrom(1024)
            except socket.timeout:
                print("Slave",self.name+":","timed out, no more responses.")
                break
            else:
                print("Slave",self.name+":","recieved:",data,"from",server)
                if server not in self.peers:
                    self.peers.append(server)

    def recvMCAST(self):
        while True:
            print("Slave",self.name+":","waiting to recieve. recvmcast")
            try:
                data, server = self.mCastSock.recvfrom(1024)
            except socket.timeout:
                print("Slave",self.name+":","timed out, no more responses.")
                break
            else:
                print("Slave",self.name+":","recieved:",data,"from",server)
                
                recvMSG = pickle.loads(data) # I'm here message
                print("received message:",recvMSG)
                break


    def loop(self):
        # send HELLO message
        print("Initialized")

        self.sayHello()
        while True:
            toDo = self.sel.select()                                               # The usual method for event treatment
            for event, data in toDo:
                callback = event.data
                print("sds",event.fileobj)
                msg = callback()
                
slave = zerg("Brood1")
slave.loop()
            


