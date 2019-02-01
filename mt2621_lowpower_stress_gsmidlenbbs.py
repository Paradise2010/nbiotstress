#-------------------------------------------------------------------------------
# Name:        MT2621 MAIN
# Purpose:
#
# Author:     low power stress test
#
# Created:     10/19/2018
# Copyright:   (c) stress 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
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
# 第一步，创建一个logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)    # Log等级总开关

# 第二步，创建一个handler，用于写入日志文件
ISOTIMEFORMAT='%Y-%m-%d %H_%I_%M_%S'
currentTime = time.strftime( ISOTIMEFORMAT, time.localtime() )
test_trace_folder = os.path.join(os.getcwd(), "log")
if os.path.exists(test_trace_folder) is False:
	os.mkdir(GKI_Trace_folder)
logfile = os.path.join(test_trace_folder,"test_trace_"+currentTime+'.log')
fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(logging.DEBUG)   # 输出到file的log等级的开关

# 第三步，再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)   # 输出到console的log等级的开关

# 第四步，定义handler的输出格式
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 第五步，将logger添加到handler里面
logger.addHandler(fh)
logger.addHandler(ch)
#
lightsleepCount = -1
test_report_folder = os.path.join(os.getcwd(), "TestReport")
if os.path.exists(test_report_folder) is False:
	os.mkdir(test_report_folder)


Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
reportName="TestReport_%s"%Realtime+".csv"

def writercsv(datalist):
    with open(os.path.join(test_report_folder,reportName),'a+') as fwriter:
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
            time.sleep(5)

    def resetboard(self):
        board = pySer(self.comport,9600,3)

        board.Send_Command('O(00,01,1)E')
        time.sleep(1)
        board.Send_Command('O(00,01,0)E')
        time.sleep(1)

        board.Send_Command('O(00,03,1)E')
        time.sleep(4)

        board.Send_Command('O(00,03,0)E')
        time.sleep(1)
        board.close()

    def closecatcherdump(self):
        #subprocess.Popen([r"D:\scripts\tcl\SendTCLToCatcherELT.exe ",r"source {D:\scripts\tcl\conn.tcl}"])
        subprocess.Popen([self.tool,self.tclcommand])

def executeAtCommand(ser,atcommand,response):
    ser.Send_Command(atcommand+"\r")
    logger.debug("send %s command" % atcommand)
    RSP =  ser.checkResponse(response)
    logger.debug(RSP)
    if RSP != "timeout":
        logger.debug(RSP)
        return True

def gsmidlenbbs_setting(ser):


    logger.debug("start dmds gsm idle nb background search setting!")
    ser.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=1","OK")
    time.sleep(2)
    ser.settimeout(20)
    executeAtCommand(ser,"AT+MSSTANDBY=0","OK")
    ser.settimeout(2)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=1","OK")
    time.sleep(1)
    print("1")
    executeAtCommand(ser,"AT+MSMODE=0","OK")
    '''
    for i in range(60):
        ser.settimeout(1)
        if executeAtCommand(ser,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        time.sleep(1)
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv(["start",Realtime,'gsmidlenbbs','Fail','evb can\'t register gsm!'])
        return False

    '''
    ser.settimeout(3)
    executeAtCommand(ser,"AT*MUSO=1",'OK')
    time.sleep(1)
    executeAtCommand(ser,"at*mfrcllck=0","OK")
    time.sleep(1)
    executeAtCommand(ser,"AT+CEREG=1","OK")
    for i in range(60):
        ser.settimeout(1)
        if executeAtCommand(ser,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        time.sleep(1)
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([i,Realtime,'gsmidlenbbs','Fail','evb can\'t register NB!'])
        return False

def gsmidlenbbs(ser,loop):
    global lightsleepCount

    ser.settimeout(3)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT*MUSO=1","OK")
    time.sleep(1)
    executeAtCommand(ser,"at*mfrcllck=1,3738,2,99","OK")
    # WAIT FOR EVE ENTERING sleepling mode
    time.sleep(1)
    ser.settimeout(30)
    RSP =  ser.checkResponse("+CEREG: 0")
    if RSP != "timeout":
        logger.debug(RSP)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mt2621lowpowerstressgsmidlenbbs','PASS','evb deattacg NB!'])
    time.sleep(1)
    ser.settimeout(3)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    for i in range(60):
        ser.settimeout(1)
        if executeAtCommand(ser,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        time.sleep(1)
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mt2621lowpowerstressgsmidlenbbs','Fail','evb can\'t register gsm!'])
        return False
    ser.settimeout(3)
    executeAtCommand(ser,"AT*MUSO=1","OK")
    ser.settimeout(2)
    for i in range(200):
        if i > 180 :
            pass
        ser.Send_Command("AT\r")
        RSP =  ser.checkResponse("CEREG: 2")
        if RSP != "timeout":
            logger.debug(RSP)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mt2621lowpowerstressgsmidlenbbs','PASS','evb  NB backgroud search!'])
            logger.debug(Realtime)
            break
        logger.debug(str(i))
        time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.settimeout(3)
    executeAtCommand(ser,"at*mfrcllck=0","OK")
    time.sleep(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    time.sleep(1)
    executeAtCommand(ser,"AT+MSNWSEL=1","OK")
    time.sleep(1)
if __name__ == "__main__":


    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    assertfilepath = config.get("mtbf","assertfile")
    comport = config.get("mtbf","port")
    powerrelayport = config.get("mtbf","powerrelayport")
    catchertool = config.get("mtbf","catchertool")
    tclcommand = config.get("mtbf","tclcommand")
    dmdsenable = config.get("mtbf","dmdsenable")
    dmdsdmssswitch = config.get("mtbf","dmdsdmssswitch")
    #casepath = "D:\\scripts\\python\\testcase"
    event_handler = MyHandler(powerrelayport,catchertool,tclcommand)
    observer = Observer()
    observer.schedule(event_handler, path=assertfilepath, recursive=True)
    observer.start()
    sercom = pySer(comport,115200,10)
    sercom.start()
    logger.debug(" start com port!")
    if 1 == int(dmdsenable):
        dmdsflag = 1
    else:
        dmdsflag = 0
    try:
		logger.debug("started myWatch")

		gsmidlenbbs_setting(sercom)
		for i in range(1000):
			gsmidlenbbs(sercom,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()
