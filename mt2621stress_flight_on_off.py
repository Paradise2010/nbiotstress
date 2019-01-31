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
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)    # Log等级总开关

# 第二步，创建一个handler，用于写入日志文件
GKI_Trace_folder=""
ISOTIMEFORMAT='%Y-%m-%d %H_%I_%M_%S'
currentTime = time.strftime( ISOTIMEFORMAT, time.localtime() )
test_trace_folder = os.path.join(os.getcwd(), "log")
if os.path.exists(test_trace_folder) is False:
	os.mkdir(test_trace_folder)
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
        self.logger=logging.getLogger(__name__)
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
        time.sleep(6)

        board.Send_Command('O(00,03,0)E')
        time.sleep(1)
        board.close()

    def closecatcherdump(self):
        #subprocess.Popen([r"D:\scripts\tcl\SendTCLToCatcherELT.exe ",r"source {D:\scripts\tcl\conn.tcl}"])
        subprocess.Popen([self.tool,self.tclcommand])



def FligtModeTest(serinstance,loop):
    logger.info("--------FligtModeTest--------")
    serinstance.settimeout(2)
    serinstance.Send_Command("AT\r")
    logger.debug("send at command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        logger.debug(" at response is error!")
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        logger.debug(" at response is error!")
    # choose gsm side to enter at command
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        logger.debug(" at response is error!")

    serinstance.settimeout(10)
    serinstance.Send_Command("AT+MSMODE=1\r")
    logger.debug("send AT+MSMODE=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        return None
    time.sleep(3)
    serinstance.settimeout(3)
    serinstance.Send_Command("AT+MSMODE=0\r")
    logger.debug("send AT+MSMODE=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        return None
    time.sleep(3)
    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        return None
    for i in range(60):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CGATT?\r")
        logger.debug("send AT+CGATT? command")
        RSP =  serinstance.checkResponse("+CGATT: 1")
        if RSP != "timeout":
            logger.debug(RSP)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'FligtModeTest','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'FligtModeTest','Fail','evb can\'t register nb nw!'])
        return False
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        return None
    for i in range(60):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CREG?\r")
        logger.debug("send AT+CREG? command")
        RSP =  serinstance.checkResponse("+CREG: 0,1")
        if RSP != "timeout":
            logger.debug(" evb register gsm nw!")
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'FligtModeTest','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'FligtModeTest','Fail','evb can\'t gsm nw!'])
        return False
    return True

def DMDSDMSSSWITCH(serinstance,switchmode):
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT","OK")
    executeAtCommand(serinstance,"AT","OK")
    logger.info("--------mtbf DMSS DMDS Switch--------")
    logger.debug("start dmds switch test!")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    time.sleep(3)
    serinstance.Send_Command("AT+MSSTANDBY?\r")
    RSP = serinstance.checkResponse("MSSTANDBY:")
    DMDSDMSS_check_string=r'MSSTANDBY: (\d)'
    parten=re.compile(DMDSDMSS_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result != None and result[0] != str(switchmode) :
        serinstance.Send_Command("AT+MSSTANDBY="+str(switchmode)+"\r")
        serinstance.settimeout(60)
        RSP = serinstance.checkResponse("CPIN: READY")
        if RSP is not "timeout":
            return True


    logger.info("--------end DMSS DMDS Switch--------")

#   nblostgsmservice updated by jackey at 1/3/2019
#  update pyserial util

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
		if 1 == dmdsflag:
			DMDSDMSSSWITCH(sercom,1)
		else:
			DMDSDMSSSWITCH(sercom,0)

		for i in range(1000):
			FligtModeTest(sercom,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()