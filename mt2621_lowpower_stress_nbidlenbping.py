#-------------------------------------------------------------------------------
# Name:        MT2621 MAIN
# Purpose:
#
# Author:      mtbf
#
# Created:     15/08/2018
# updated:     12/24/2018, add summit assert number to remote server
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

import urllib,urllib2
import json
import socket
import parser

#========================================= Common Function  ===================================================
# 第一步，创建一个logger
logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)    # Log等级总开关

# 第二步，创建一个handler，用于写入日志文件
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
        time.sleep(420)
        if os.path.exists(os.path.join(temppath,"MemoryDump.bin")):
            logger.info("memorydump.bin file was created!")
            os.rename("MemoryDump.bin",currentTime+"memorydump.bin")
            self.resetboard()
            logger.info("board was reset!!!")
            self.closecatcherdump()
            logger.info("send command to catcher for closing dump window")
            time.sleep(15)
            self.summitdata()
            time.sleep(5)

    def summitdata(self):
        data={}
        data["hostname"]=socket.gethostbyname(socket.gethostname())
        data["date"]=datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        data["assertNumber"]=1
        data["project"]="MT2621"
        params=json.dumps(data).encode('utf8')
        req = urllib2.Request("http://172.28.231.19:8888", data=params,
                             headers={'content-type': 'application/json'})
        response = urllib2.urlopen(req)

        print(response)
        response.close()
    def resetboard(self):
        board = pySer(self.comport,9600,3)

        #board.Send_Command('O(00,02,1)E')
        #time.sleep(2)
        board.Send_Command('O(00,01,1)E')
        self.logger.info('O(00,01,1)E')
        time.sleep(2)
        board.Send_Command('O(00,01,0)E')
        self.logger.info('O(00,01,0)E')
        time.sleep(3)

        board.Send_Command('O(00,03,1)E')
        self.logger.info('O(00,03,1)E')
        time.sleep(2)

        board.Send_Command('O(00,03,0)E')
        self.logger.info('O(00,03,0)E')
        time.sleep(7)

        #board.Send_Command('O(00,02,0)E')
        #time.sleep(2)
        board.close()

    def closecatcherdump(self):
        #subprocess.Popen([r"D:\scripts\tcl\SendTCLToCatcherELT.exe ",r"source {D:\scripts\tcl\conn.tcl}"])
        subprocess.Popen([self.tool,self.tclcommand])


#   nblostgsmservice updated by jackey at 1/3/2019
#  update pyserial util

def ping(serinstance,loop):
    logger.info("--------ping test was executed--------")
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.settimeout(200)
    logger.debug("send AT+PING=182.150.27.42 -n 20 -d 1 ")
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 20 -d 1\r')
    RSP =  serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result == 20:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'ping','Fail','ping success!'])
        return False
    else:
        if result  < 15 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'ping','Fail','ping failed'])
            return True
    time.sleep(1)


#   nblostgsmservice updated by jackey at 1/3/2019
#  update pyserial util

def gsmcall(serinstance,loop):
    logger.info("--------gsmcall--------")
    serinstance.settimeout(2)
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.settimeout(20)
    serinstance.Send_Command('ATD 112;\r')
    RSP =  serinstance.checkResponse("NO CARRIER")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'gsmcall','Fail','gsm call failed'])


#   gsm short message function updated by jackey at 1/3/2019
#  update pyserial util


def gsmsms(serinstance,loop):
    logger.info("--------gsmsms %d--------" % loop)
    serinstance.settimeout(4)
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.settimeout(30)
    serinstance.Send_Command('AT+CMGF=1\r')
    #serdemo.settimeout(i*2)
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.Send_Command('AT+CMGS=\"1064899990000\"\r')
    #serdemo.settimeout(i*2)
    #RSP = serdemo.checkResponse()
		#print RSP
    #if '>' in RSP:
        #print "ok is response!!!"
    time.sleep(1)
    serinstance.Send_Command('testing')
    #serdemo.settimeout(i*2)
    time.sleep(1)
    serinstance.Send_Command(chr(26))
    logger.debug("send test message")
    RSP =  serinstance.checkResponse("CMGS:")
    if RSP != "timeout":
        logger.debug(RSP)
    time.sleep(5)
    #RSP = serinstance.checkResponse()



#   basic function updated by jackey at 1/3/2019
#  update pyserial util

def basictest(serinstance,loop):

    logger.info("--------basictest--------")
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
            writercsv([loop,Realtime,'basictest','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'basictest','Fail','evb can\'t register nb nw!'])
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
            writercsv([loop,Realtime,'basictest','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'basictest','Fail','evb can\'t gsm nw!'])
        return False
    return True


#   gsm sms interupt nb ping process updated by jackey at 1/3/2019
#  update pyserial util

def gsminterruptnbping(serinstance,loop):
    logger.info("--------gsminterruptnbping--------")
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)

    serinstance.settimeout(1000)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 100 -d 1\r')
    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'gsminterruptnbping','Pass','gsm call failed'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'gsminterruptnbping','Fail','gsm call failed'])
    time.sleep(5)
    for i in  range(3):
        gsmsms(serinstance,loop)
    serinstance.settimeout(100)
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 20:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'gsminterruptnbping','Fail','ping success!'])
        return False
    else:
        if result  < 15 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'gsminterruptnbping','Fail','ping failed'])
            return True
    time.sleep(1)


#   nblostgsmservice updated by jackey at 1/3/2019
#  update pyserial util

def nblostgsmservice(serinstance,loop):
    logger.info("--------nblostgsmservice--------")
    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.Send_Command("at*mfrcllck=1,2506,2,99\r")
    logger.debug("send at*mfrcllck=1,2506,2,99 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else :
        logger.debug("at*mfrcllck=1,2506,2,99 fail!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'nblostgsmservice','Fail','lock freq  failed'])
        return False

    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        logger.debug(" fail to set muso")
    for i in range(60):
        serinstance.settimeout(1)
        serinstance.Send_Command("AT+CREG?\r")
        logger.debug("send AT+CREG? command")
        RSP =  serinstance.checkResponse("+CREG: 0,1")
        if RSP != "timeout":
            logger.debug(" evb register gsm nw!")
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'basictest','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'basictest','Fail','evb can\'t gsm nw!'])
        return False
    time.sleep(3)
    serinstance.settimeout(200)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 20 -d 1\r')
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 20:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'nblostgsmservice','Fail','ping success!'])

    elif result  < 15 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'nblostgsmservice','Fail','ping failed'])

    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'nblostgsmservice','Pass','gsm call failed'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'nblostgsmservice','Fail','gsm call failed'])
    for i in range(3):
        gsmsms(serinstance,loop)
    time.sleep(3)
    serinstance.settimeout(3)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)

    serinstance.Send_Command("at*mfrcllck=0\r")
    logger.debug("send at*mfrcllck=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    else :
        logger.debug("at*mfrcllck=0 fail!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'nblostgsmservice','Fail','unlock freq  failed'])
        return False
    time.sleep(5)

def setmfrcllckzero(serinstance,loop):
    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)

    serinstance.Send_Command("at*mfrcllck?\r")
    logger.debug("send at*mfrcllck=0 command")
    RSP =  serinstance.checkResponse("MFRCLLCK: 0")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        serinstance.Send_Command("at*mfrcllck=0\r")
        RSP =  serinstance.checkResponse("OK")
        if RSP != "timeout":
            logger.debug(RSP)

def mtbfcase1(ser,loop):
    logger.info("--------mtbfcase1--------")
    if not basictest(ser,loop):
        return False
	ping(ser,loop)
	gsmcall(ser,loop)
	gsmsms(ser,loop)
def mtbfcase2(ser,loop):
    logger.info("--------mtbfcase2--------")
    if not basictest(ser,loop):
        return False
    gsminterruptnbping(ser,loop)
def mtbfcase3(ser,loop):
    logger.info("--------mtbfcase3--------")
    if not basictest(ser,loop):
        return False
    nblostgsmservice(ser,loop)
def mtbfDMDSSwitch(serinstance,loop):
    logger.info("--------mtbfDMDSSwitch--------")
    logger.debug("start dmds switch test!")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    time.sleep(2)
    serinstance.settimeout(20)
    executeAtCommand(serinstance,"AT+MSSTANDBY=1","CPIN:")
    serinstance.settimeout(3)
    #executeAtCommand(serinstance,"AT*MUSO=1","OK")
    #executeAtCommand(serinstance,"AT*MNVMQ=\"1.0.0\"","OK")
    #executeAtCommand(serinstance,"AT*MNVMW=1,\"NVDM_MODEM_CFG\",\"CELL_QUALITY_RSRP_THRESHOLD\",0,1,\"3D\"","OK")
    subprocess.Popen([catchertool,"send_pcommand MOD_RRM 0 -40"])
    subprocess.Popen([catchertool,"send_pcommand MOD_MODEM_SWITCH 1 -40"])
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(20)
    executeAtCommand(serinstance,"AT+MSMODE=0","CPIN:")
    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','evb can\'t register gsm!'])
        return False
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','evb can\'t register NB!'])
        return False
    subprocess.Popen([catchertool,"send_pcommand MOD_RRM 0 -100"])
    subprocess.Popen([catchertool,"send_pcommand MOD_MODEM_SWITCH 1 -100"])
    time.sleep(30)
    if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','EVB didn\'t switch to gsm'])
        return False
    #ping(serinstance,loop)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MNVMQ=\"1.0.0\"","OK")
    executeAtCommand(serinstance,"AT*MNVMW=1,\"NVDM_MODEM_CFG\",\"CELL_QUALITY_RSRP_THRESHOLD\",0,1,\"78\"","OK")

    time.sleep(10)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    time.sleep(2)
    subprocess.Popen([catchertool,"send_pcommand MOD_RRM 0 -60"])
    subprocess.Popen([catchertool,"send_pcommand MOD_MODEM_SWITCH 1 -60"])
    serinstance.settimeout(10)
    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    time.sleep(2)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','evb can\'t register NB!'])
        return False
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MFRCLLCK=1,2506,2,99","OK")
    time.sleep(30)
    if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','EVB didn\'t switch to gsm'])
        return False
    #ping(serinstance,loop)
    executeAtCommand(serinstance,"AT*MFRCLLCK=0","OK")
    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'DMDS','Fail','evb can\'t register NB!'])
        return False
    #ping(serinstance,loop)


#   nblostgsmservice updated by jackey at 1/3/2019
#  update pyserial util

def executeAtCommand(serinstance,atcommand,response):
    serinstance.Send_Command(atcommand+"\r")
    logger.debug("send %s command" % atcommand)
    RSP =  serinstance.checkResponse(response)
    if RSP != "timeout":
        logger.debug(RSP)
        return True
def mtbfDMSSSwitch(ser,loop):
    pass

# case 4: nb preferred ping 20, gsm perferred 3 calls
# created by jackey 1/3/2019
def mtbf4(serinstance,loop):
    logger.info("--------mtbf case 4--------")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MBSC=1,8","MBSC: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=1","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")

    serinstance.settimeout(3)

    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','evb can\'t register NB!'])
        return False
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(200)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 20 -d 1\r')
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 10:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','ping success!'])

    elif result  < 10 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','ping failed'])
    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=2","OK")
    for i in range(350):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 350:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','evb can\'t register gsm!'])
        return False
    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf4','Pass','gsm call successed!'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf4','Fail','gsm call failed!'])



# case 5:  gsm perferred 3 calls ,nb preferred ping 20
# created by jackey 1/3/2019
def mtbf5(serinstance,loop):

    logger.info("--------mtbf case 5--------")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MBSC=1,8","MBSC: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=2","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")

    serinstance.settimeout(3)

    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")

    for i in range(60):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf5','Fail','evb can\'t register gsm!'])
        return False
    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf5','Pass','gsm call successed!'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf5','Fail','gsm call failed'])

    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=1","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(350):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 350:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','evb can\'t register NB!'])
        return False
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(200)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 20 -d 1\r')
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 10:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf5','Pass','ping success!'])

    elif result  < 10 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf5','Fail','ping failed'])
    serinstance.settimeout(2)



# case 6:  nb preferred ,manual select a network, wait for switching ,dial 3 calls.auto select nb, check NBIOT attach
# created by jackey 1/3/2019
# updated cops timer expired, when setting cops=1,2,31001, the deep sleep expier timer is 90s
def mtbf6(serinstance,loop):
    logger.info("--------mtbf case 6--------")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MBSC=1,8","MBSC: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=1","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    time.sleep(10)
    executeAtCommand(serinstance,"AT+COPS=1,2,\"31001\"","OK")

    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    for i in range(210):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 120:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf6','Fail','evb can\'t register gsm!'])
        return False
    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf6','Pass','gsm call successed!'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf6','Fail','gsm call failed!'])
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT+COPS=0","OK")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    for i in range(350):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 350:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf4','Fail','evb can\'t register NB!'])
        return False
    time.sleep(3)




# case 7:  gsm preferred ,manual select a network, wait for switching ,ping 20 packets.auto select nb, check gsm attach
# created by jackey 1/3/2019
#update cops timer, no reason ,just keep safe
def mtbf7(serinstance,loop):

    logger.info("--------mtbf case 7--------")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT*MBSC=1,8","MBSC: 0")
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSNWPRI=2","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")

    serinstance.settimeout(3)

    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    time.sleep(10)
    executeAtCommand(serinstance,"AT+COPS=1,2,\"31001\"","OK")
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    for i in range(210):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CGATT?","+CGATT: 1"):
            break
        i =i +1
        logger.debug(i)
    if i == 120:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf7','Fail','evb can\'t register NB!'])
        return False
    time.sleep(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(200)
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 20 -d 1\r')
    RSP = serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result >= 10:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf7','Pass','ping success!'])

    elif result  < 10 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf7','Fail','ping failed'])
    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=1","OK")
    executeAtCommand(serinstance,"AT+COPS=0","OK")
    executeAtCommand(serinstance,"AT+MSMODE=0","OK")
    time.sleep(5)
    for i in range(350):
        serinstance.settimeout(1)
        if executeAtCommand(serinstance,"AT+CREG?","+CREG: 0,1"):
            break
        i =i +1
        logger.debug(i)
    if i == 350:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'mtbf7','Fail','evb can\'t register gsm!'])
        return False
    time.sleep(5)
    for i in range(3):
        serinstance.settimeout(80)
        serinstance.Send_Command('ATD 112;\r')
        RSP =  serinstance.checkResponse("NO CARRIER")
        if RSP != "timeout":
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf7','Pass','gsm call successed!'])
        else:
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'mtbf7','Fail','gsm call failed!'])

#  DMSS/DMDS switch
# created by jackey 1/3/2019
def DMDSDMSSSWITCH(serinstance,switchmode):

    logger.info("--------mtbf DMSS DMDS Switch--------")
    logger.debug("start dmds switch test!")
    serinstance.settimeout(3)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    time.sleep(3)
    serinstance.Send_Command("AT+MSSTANDBY?\r")
    logger.info("AT+MSSTANDBY?")
    RSP = serinstance.checkResponse("MSSTANDBY:")
    DMDSDMSS_check_string=r'MSSTANDBY: (\d)'
    parten=re.compile(DMDSDMSS_check_string)
    result=parten.findall(RSP)
    logger.debug(RSP)

    if result  and result[0] != str(switchmode) :
        serinstance.Send_Command("AT+MSSTANDBY="+str(switchmode)+"\r")
        serinstance.settimeout(60)
        RSP = serinstance.checkResponse("CPIN: READY")
        if RSP is not "timeout":
            return True


    logger.info("--------end DMSS DMDS Switch--------")

#set cops back
#created by jackey 1/4/2019
def setcops(serinstance):
    logger.info("--------set cops 0--------")
    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    executeAtCommand(serinstance,"AT+COPS=0","OK")
    time.sleep(5)
    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")
    executeAtCommand(serinstance,"AT+COPS=0","OK")
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
    ser = pySer(comport,115200,10)
    ser.start()
    logger.debug(" start com port!")
    if 1 == int(dmdsenable):
        dmdsflag = 1
    else:
        dmdsflag = 0
    try:
		logger.debug("started myWatch")

		for i in range(1000):
			if 1 == dmdsflag:
				DMDSDMSSSWITCH(ser,1)
				mtbfcase1(ser,i)
				mtbfcase2(ser,i)
				setmfrcllckzero(ser,i)
				mtbfcase3(ser,i)
				setmfrcllckzero(ser,i)
	  			#mtbfDMDSSwitch(ser,1)
            #start dmss case
			if 0 == dmdsflag:
				setcops(ser)
				DMDSDMSSSWITCH(ser,0)
				mtbf4(ser,i)
				mtbf5(ser,i)
				mtbf6(ser,i)
				setcops(ser)
				mtbf7(ser,i)
				setcops(ser)
    except KeyboardInterrupt:
		observer.stop()
    observer.join()