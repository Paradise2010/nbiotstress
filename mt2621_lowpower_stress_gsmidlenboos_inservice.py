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
def gsmidlenboos_inservice_setting(ser):


    logger.debug("start dmds gsm idle nb iot idle ping setting!")
    ser.settimeout(2)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT*MUSO=0","OK")

    ser.settimeout(20)
    executeAtCommand(ser,"AT+MSSTANDBY=1","CPIN:")
    ser.settimeout(2)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT+MSMODE=1","OK")
    time.sleep(2)
    executeAtCommand(ser,"AT+MSMODE=0","CPIN:")
    for i in range(60):
        ser.settimeout(1)
        if executeAtCommand(ser,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        time.sleep(1)
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv(["start",Realtime,'DMDS','Fail','evb can\'t register gsm!'])
        return False
    ser.settimeout(3)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT*MUSO=1",'OK')
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
        writercsv(["1",Realtime,'DMDS','Fail','evb can\'t register NB!'])
        return False
def gsmidlenboos_inservice(ser,loop):
    global lightsleepCount
    # add change
    ser.settimeout(3)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)

    executeAtCommand(ser,"AT*MUSO=1","OK")
    time.sleep(1)
    executeAtCommand(ser,"at*mfrcllck=1,3738,2,99","OK")
    # WAIT FOR EVE ENTERING sleepling mode
    time.sleep(21)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command('at+sm=status\r')
    RSP =  ser.checkResponse("times")
    logger.debug(RSP)
    if RSP != "timeout":
        logger.debug(RSP)
        #return True
    else:
        return False
    lightsleep_check_string=r'(\d+)'
    parten=re.compile(lightsleep_check_string)
    result=int(parten.findall(RSP)[0])
    logger.debug(result)
    if lightsleepCount < result :
        logger.info(" the MT2621 NB enter light sleep")
    else:
        logger.info("the evb didn\'t enter evb from idle")
    lightsleepCount = result

    executeAtCommand(ser,"at*mfrcllck=0","OK")
    for i in range(60):
        if executeAtCommand(ser,"at+cgatt?","+CGATT: 1"):
            logger.info("nb live nw recover!")
            break
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([i,Realtime,'gsmidlenboos_inservice','Fail','fail to recover NW!'])
            #return False
        time.sleep(1)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv(["1",Realtime,'gsmidlenboos_inservice','Fail','evb can\'t register NB!'])
        return False
    #WAKE UP EVB ,THNE SEND AT+PING COMMAND
    ser.Send_Command("AT\r")
    time.sleep(1)
    ser.Send_Command("AT\r")
    time.sleep(1)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    executeAtCommand(ser,"AT","OK")
    ser.settimeout(40)
    ser.Send_Command('AT+PING=180.169.77.254 -n 4 -w 10000\r')
    RSP =  ser.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result == 4:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'gsmidlenboos_inservice','pass','ping success!'])
        #return False
    else:
        if result  < 2 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'gsmidlenboos_inservice','Fail','ping failed'])
            #return True

    time.sleep(11)


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
		gsmidlenboos_inservice_setting(ser)
		for i in range(1000):
			gsmidlenboos_inservice(ser,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()