#-------------------------------------------------------------------------------
# Name:        MT2621 MAIN
# Purpose:
#
# Author:      mtbf
#
# Created:     15/08/2018
# Copyright:   (c) mtbf 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#--encoding:utf-8--
import time
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pyser import pySer
import os
import shutil
import csv
import logging
import re
import subprocess
import ConfigParser


#========================================= Common Function  ===================================================

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


ISOTIMEFORMAT='%Y-%m-%d %H_%I_%M_%S'
currentTime = time.strftime( ISOTIMEFORMAT, time.localtime() )
test_trace_folder = os.path.join(os.getcwd(), "log")
if os.path.exists(test_trace_folder) is False:
	os.mkdir(test_trace_folder)
logfile = os.path.join(test_trace_folder,"test_trace_"+currentTime+'.log')
fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(logging.DEBUG)


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)


formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)


logger.addHandler(fh)
logger.addHandler(ch)

test_report_folder = os.path.join(os.getcwd(), "TestReport")
if os.path.exists(test_report_folder) is False:
	os.mkdir(test_report_folder)


Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
reportName="TestReport_%s"%Realtime+".csv"

def writercsv(datalist):
    with open(os.path.join(test_report_folder,reportName),'a+b') as fwriter:
        writer=csv.writer(fwriter,dialect='excel')
        writer.writerow(datalist)

#in order to improve code ,keep it
def Send_cmd(cmd, timeout):
    serial_port=serial.Serial(port=Port,baudrate=Port_baudrate,bytesize=8,timeout=timeout)
    serial_port.write(cmd.encode())
    command_response=serial_port.read(512)
    serial_port.close()
    return command_response

class MyHandler(FileSystemEventHandler):
    def __init__(self,comport,tool,tclcommand):
        super(MyHandler, self).__init__()
        self.comport = comport
        self.tool = tool
        self.tclcommand = tclcommand

    def on_created(self,event):
        pass
    def on_modified(self,event):

        temppath = os.path.split(event.src_path)[0]
        os.chdir(temppath)
        logger.debug("the directory was modified!!!")
        logger.debug(event.src_path)
        ISOTIMEFORMAT='%Y-%m-%d %H_%I_%M_%S'
        currentTime = time.strftime( ISOTIMEFORMAT, time.localtime() )
        time.sleep(120)
        if os.path.exists(os.path.join(temppath,"MemoryDump.bin")):
            logger.info("memorydump.bin file was created!")
            os.rename("MemoryDump.bin",currentTime+"memorydump.bin")
            self.resetboard()
            logger.info("board was reset!!!")
            self.closecatcherdump()
            logger.info("send command to catcher for closing dump window")
            time.sleep(15)

            time.sleep(5)

    def resetboard(self):
        board = pySer(self.comport,9600,3)

        board.Send_Command('O(00,01,1)E')
        time.sleep(2)
        board.Send_Command('O(00,01,0)E')
        time.sleep(1)

        board.Send_Command('O(00,03,1)E')
        time.sleep(2)

        board.Send_Command('O(00,03,0)E')
        time.sleep(7)
        board.close()

    def closecatcherdump(self):
        #subprocess.Popen([r"D:\scripts\tcl\SendTCLToCatcherELT.exe ",r"source {D:\scripts\tcl\conn.tcl}"])
        subprocess.Popen([self.tool,self.tclcommand])



def singlestandbymodechange(serinstance,loop):
    serinstance.settimeout(1)
    executeAtCommand(ser,"AT","OK")
    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=1","OK")

    for i in range(80):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CGATT?\r")
        logger.debug("send AT+CGATT? command")
        RSP =  serinstance.checkResponse("+CGATT: 1")
        if RSP != "timeout":
            logger.debug(RSP)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'singlestandbymodechange','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 80:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'singlestandbymodechange','Fail','evb can\'t register nb nw!'])
        return False
    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")

    serinstance.settimeout(2)
    executeAtCommand(ser,"AT+MSMODE=4","OK")


    for i in range(80):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CREG?\r")
        logger.debug("send AT+CREG? command")
        RSP =  serinstance.checkResponse("+CREG: 0,1")
        if RSP != "timeout":
            logger.debug(" evb register gsm nw!")
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'singlestandbymodechange','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 80:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'singlestandbymodechange','Fail','evb can\'t gsm nw!'])
        return False
    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=2","OK")
    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=1","OK")
    for i in range(80):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CGATT?\r")
        logger.debug("send AT+CGATT? command")
        RSP =  serinstance.checkResponse("+CGATT: 1")
        if RSP != "timeout":
            logger.debug(RSP)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'singlestandbymodechange','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 80:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'singlestandbymodechange','Fail','evb can\'t register nb nw!'])
        return False

    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=0","OK")
    executeAtCommand(ser,"AT*MUSO=1","OK")
    for i in range(80):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CGATT?\r")
        logger.debug("send AT+CGATT? command")
        RSP =  serinstance.checkResponse("+CGATT: 1")
        if RSP != "timeout":
            logger.debug(RSP)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'singlestandbymodechange','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 80:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'singlestandbymodechange','Fail','evb can\'t register nb nw!'])
        return False
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=0","OK")
    return True
def setsinglestandby(serinstance,loop):
    logger.debug("start  single standby mode change setting!")
    ser.settimeout(20)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    serinstance.Send_Command("AT+MSSTANDBY?\r")
    logger.debug("AT+MSSTANDBY?")
    RSP =  serinstance.checkResponse("MSSTANDBY: 0")
    logger.debug(RSP)
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        serinstance.Send_Command("AT+MSSTANDBY=0\r")
    time.sleep(3)
    serinstance.settimeout(10)

    executeAtCommand(ser,"AT+MSMODE=1","OK")

    serinstance.settimeout(3)
    executeAtCommand(ser,"AT+MSMODE=0","OK")
    time.sleep(5)
def executeAtCommand(serinstance,atcommand,response):
    serinstance.Send_Command(atcommand+"\r")
    logger.debug("send %s command" % atcommand)
    RSP =  serinstance.checkResponse(response)
    logger.debug(RSP)
    if RSP != "timeout":
        logger.debug(RSP)
        return True

if __name__ == "__main__":


    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    assertfilepath = config.get("mtbf","assertfile")
    comport = config.get("mtbf","port")
    powerrelayport = config.get("mtbf","powerrelayport")
    catchertool = config.get("mtbf","catchertool")
    tclcommand = config.get("mtbf","tclcommand")
    #casepath = "D:\\scripts\\python\\testcase"
    event_handler = MyHandler(powerrelayport,catchertool,tclcommand)
    observer = Observer()
    observer.schedule(event_handler, path=assertfilepath, recursive=True)
    observer.start()
    ser = pySer(comport,115200,10)
    logger.debug(" start com port!")
    ser.start()
    try:
		logger.debug("started myWatch")
		setsinglestandby(ser,1)
		for i in range(1000):
			singlestandbymodechange(ser,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()