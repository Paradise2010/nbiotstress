#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mtbf
#
# Created:     12/11/2018
# Copyright:   (c) mtbf 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from queue import Queue
from threading import Thread, Event
import time
import serial
import logging

# Sentinel used for shutdown
class ActorExit(Exception):
    def __repr__(self):
        return "close"

class pySer:
    def __init__(self,port,baudrate,xwait):
        self._mailbox = Queue()
        self.port=port
        self.baudrate = baudrate
        self.timeout = xwait
        self.waittimeout= None
        self.logger = logging.getLogger("main.pySer")
        try:
            self.ser = serial.Serial(port, baudrate, timeout =xwait)
            self.logger.debug("%s is connected" % self.port )
        except serial.SerialException:
            self.logger.debug("Port is closed")

    def Send_Command(self, msg):
        '''
        Send a message to the actor
        '''
        #self._mailbox.put(msg)
        try:
            print(msg)
            #self.logger.debug(msg)
        except Exception:
            print(msg)
        try:
            cmd= msg
            self.ser.write(cmd.encode())
        #print(cmd.encode())
        except serial.SerialException:
            self.reConnect()
            self.logger.debug("fail to write at command to evb")

    def recv(self):
        '''
        Receive an incoming message
        '''
        while True:
            try:
                out = self.ser.readline()
                msg =''.join(out).strip()
                if msg !='' or msg != None or msg != '\r\n':
                    self._mailbox.put(msg)
            except serial.SerialException:
                self.reConnect()
                self.logger.debug("fail to write at command to evb")

    def close(self):
        '''
        Close the actor, thus shutting it down
        '''
        #self.send(ActorExit)
        self.ser.close()
    def open(self):
        self.ser.open()

    def isopen(self):
        return self.ser.is_open
    def start(self):
        '''
        Start concurrent execution
        '''
        self._terminated = Event()
        t = Thread(target=self.recv)

        t.daemon = True
        t.start()

    def _bootstrap(self):
        try:
            self.run()
        except ActorExit:
            pass
        finally:
            self._terminated.set()

    def join(self):
        self._terminated.wait()

    def run(self):
        '''
        Run method to be implemented by the user
        '''
        while True:


            msg = self._mailbox.get()
            if msg != "":
                print('Got:', msg)
    def settimeout(self,timeout=2):
        self.waittimeout=timeout
    def checkResponse(self,response):
        starttime=time.time()
        runtime=time.time()
        while(runtime < starttime+self.waittimeout):
            runtime=time.time()
            time.sleep(0.1)
            while not self._mailbox.empty():
                try:
                    popmessage=self._mailbox.get()
                    print popmessage
                    if popmessage !="" or None:
                        self.logger.debug(popmessage)
                except Exception:
                    raise Exception( "get popmessage error")
                #print popmessage
                if response in popmessage:
                    return popmessage
        return "timeout"
    def reConnect(self):
        try:

            self.ser = serial.Serial(self.port,self.baudrate,timeout = self.timeout)
        except serial.SerialException:
            time.sleep(60)
            self.ser.close()
            self.ser = serial.Serial(self.port,self.baudrate,timeout = self.timeout)
            self.logger.debug("Port is closed")












