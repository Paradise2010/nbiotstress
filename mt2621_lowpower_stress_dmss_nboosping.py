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
# 第一步，创建一个logger
logger = logging.getLogger("main")
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

def executeAtCommand(serinstance,atcommand,response):
    serinstance.Send_Command(atcommand+"\r")
    logger.debug("send %s command" % atcommand)
    RSP =  serinstance.checkResponse(response)
    logger.debug(RSP)
    if RSP != "timeout":
        logger.debug(RSP)
        return True
def DMSSNBOOSPING_setting(ser):

    ser.settimeout(2)
    executeAtCommand(ser,"AT","OK")
    executeAtCommand(ser,"AT","OK")
    logger.debug("start dmds gsm idle nb iot idle ping setting!")
    ser.settimeout(20)
    executeAtCommand(ser,"AT*MUSO=0","OK")

    time.sleep(2)

    executeAtCommand(ser,"AT+MSSTANDBY=0","CPIN: READY")
    ser.settimeout(2)
    executeAtCommand(ser,"AT","OK")
    executeAtCommand(ser,"AT","OK")
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT+MSMODE=1","OK")
    time.sleep(2)
    executeAtCommand(ser,"AT+MSMODE=0","CPIN:")

    # CHANGE TO NB SIDE
    ser.settimeout(2)
    executeAtCommand(ser,"AT","OK")
    executeAtCommand(ser,"AT","OK")
    executeAtCommand(ser,"AT*MUSO=1",'OK')
    # ENABLE NB REPORT REGISTER STATUS
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
        writercsv(["start",Realtime,'DMSS','Fail','evb can\'t register NB!'])
        return False
def DMSSNBOOSPING(serinstance,loop):
    logger.info("--------DMSSNBOOSPING--------")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MBSC=1,8","MBSC: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=1","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    serinstance.settimeout(10)
    #executeAtCommand(serinstance,"AT+COPS=1,2,\"31001\"","OK")
    executeAtCommand(serinstance,"AT*MFRCLLCK=1,2525,2,99","CEREG: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    for i in range(210):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 120:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMSSNBOOSPING','Fail','evb can\'t register gsm!'])
        return False
    time.sleep(5)

    serinstance.settimeout(3)
    serinstance.Send_Command("AT\r")
    time.sleep(1)
    serinstance.Send_Command("AT\r")
    time.sleep(1)
    #UPDATE
    #executeAtCommand(serinstance,"AT*MUSO=0","OK")
    #executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    serinstance.settimeout(10)
    executeAtCommand(serinstance,"AT*MFRCLLCK=0","OK")
    #executeAtCommand(serinstance,"AT*MUSO=0","OK")
    #executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    #executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(350):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 350:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMSSNBOOSPING','Fail','evb can\'t register NB!'])
        return False
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(200)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 4 -d 1\r')
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 2:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMSSNBOOSPING','Pass','ping success!'])

    elif result  < 2 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMSSNBOOSPING','Fail','ping failed'])




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
    ser.start()
    logger.debug(" start com port!")
    try:
		logger.debug("started myWatch")
		DMSSNBOOSPING_setting(ser)
		for i in range(1000):
			DMSSNBOOSPING(ser,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()