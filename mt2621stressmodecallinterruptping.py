#-------------------------------------------------------------------------------
# Name:        MT2621 MAIN
# Purpose:
#
# Author:      mtbf
#
# Created:    21/09/2018
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



def daulstandbyvoicecallinterruptPING(serinstance,loop):

    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        logger.debug(" AT*MUSO=0 is ok!")
    serinstance.settimeout(6)
    serinstance.Send_Command("at+PING=180.169.77.254 -n 20 -d 1 -w 20000\r")
    logger.debug("at+PING=180.169.77.254 -n 20 -d 1 -w 20000")
    time.sleep(2)
    serinstance.settimeout(2)
    serinstance.Send_Command("ATD112;\r")
    logger.debug("ATD112;")
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        logger.debug(" call was triggered!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Pass','call success triggered'])
    time.sleep(3)
    logger.debug("wait for 3 seconds")

    serinstance.Send_Command("ATH\r")
    logger.debug("ATH")
    serinstance.settimeout(2)
    logger.info("serial time out:%s" % serinstance.timeout)
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        logger.debug(" call was terminated!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Pass','call success ternimated'])
    #time.sleep(15)
    serinstance.settimeout(95)
    logger.info("serial time out:%s" % serinstance.timeout)
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    PING_check_string=r'\+PING:.*?Lost=(\d.*?).*'
    parten=re.compile(PING_check_string)
    pingresult = parten.findall(RSP)
    if pingresult == None:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','PING fail!'])
        return False
    result=int(pingresult[0])
    logger.debug(result)
    if result > 10:
        #write_record(run_record_file,at_exe_time,'AT+PING=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','PING fail!'])
        return False
    else:
        if result  < 3 :
            #write_record(run_record_file,at_exe_time,'AT+PING=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'voicecallinterruptPING','Pass','PING pass'])

    serinstance.settimeout(20)
    serinstance.Send_Command("at+PING=180.169.77.254  -d 1 -w 20000\r")
    logger.debug("at+PING=180.169.77.254  -d 1 -w 20000")
    time.sleep(6)
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    PING_check_string=r'\+PING:.*?Lost=(\d.*?).*'
    parten=re.compile(PING_check_string)
    pingresult = parten.findall(RSP)
    if pingresult == None:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','PING fail!'])
        return False
    result=int(pingresult[0])
    logger.debug(result)
    if result == 1:
        #write_record(run_record_file,at_exe_time,'AT+PING=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','PING fail!'])
        return False
    else:
        if result  < 1 :
            #write_record(run_record_file,at_exe_time,'AT+PING=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'voicecallinterruptPING','Pass','PING pass'])
            return True
def setting(serinstance,loop):

    serinstance.settimeout(1)
    serinstance.Send_Command("AT\r")
    logger.debug("send at command")
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','at channel is ok'])
        logger.debug(" at response is ok!")
    elif "ERROR" in RSP:
        logger.debug(" at response is error!")
    elif None == RSP:
        logger.debug("at channel is not activation")

    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        logger.debug(" AT*MUSO=1 is ok!")
    for i in range(60):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CGATT?\r")
        logger.debug("send AT+CGATT? command")
        RSP = serinstance.Reciveve_Command()
        if "+CGATT: 1" in RSP:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'voicecallinterruptPING','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break

        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','evb can\'t register nb nw!'])
        return False
    serinstance.Send_Command("AT*EUSO=0\r")
    logger.debug("send AT*EUSO=0 command")
    RSP = serinstance.Reciveve_Command()
    logger.info(RSP)
    if "OK" in RSP:
        logger.debug(" AT*EUSO=0 is ok!")
    for i in range(60):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CREG?\r")
        logger.debug("send AT+CREG? command")
        RSP = serinstance.Reciveve_Command()
        logger.info(RSP)
        if "+CREG: 0,1" in RSP:
            logger.debug(" evb register gsm nw!")
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'voicecallinterruptPING','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Fail','evb can\'t gsm nw!'])
        return False
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
    try:
		logger.debug("started myWatch")
		setting(ser,1)
		for i in range(1000):
			daulstandbyvoicecallinterruptPING(ser,i)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()