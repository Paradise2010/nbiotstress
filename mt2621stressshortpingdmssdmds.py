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



logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


ISOTIMEFORMAT='%Y-%m-%d %H_%I_%M_%S'
currentTime = time.strftime( ISOTIMEFORMAT, time.localtime() )
test_trace_folder = os.path.join(os.getcwd(), "log")
if os.path.exists(test_trace_folder) is False:
	os.mkdir(GKI_Trace_folder)
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



def basictest(serinstance,loop):
    logger.info("--------shortpingwithoutpsm--------")
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
            writercsv([loop,Realtime,'shortpingwithoutpsm','Pass','evb  register nb nw!'])
            logger.debug(" evb register nb nw!")
            break
        i =i +1
        logger.debug(i)
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'shortpingwithoutpsm','Fail','evb can\'t register nb nw!'])
        return False

    return True

def checkGSM(serinstance,loop):
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
            writercsv([loop,Realtime,'shortpingwithoutpsm','Pass','evb  register gsm nw!'])
            break

        i =i +1
    if i == 60:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'shortpingwithoutpsm','Fail','evb can\'t gsm nw!'])
        return False

def setidleflag(serinstance):
    executeAtCommand(ser,"AT*MUSO=1","OK")
    executeAtCommand(ser,"AT+CSCON=1","OK")

def shortpingwithout(serinstance,i,standbymode):
    executeAtCommand(ser,"AT*MUSO=0","OK")
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
        writercsv([loop,Realtime,'%s' % standbymode,'Fail','ping success!'] )
        return False
    else:
        if result  < 15 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'%s'% standbymode,'Fail','ping success!'] )
            return True
    time.sleep(1)

    serinstance.settimeout(2)
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.settimeout(20)
    RSP =  serinstance.checkResponse("CSCON: 0")
    if RSP != "timeout":
        logger.debug(RSP)
    else:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([i,Realtime,'%s'% standbymode,'Fail','evb cannot enter idle mode in 30s'] )


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
    logger.debug(RSP)
    if result  and result[0] != str(switchmode) :
        serinstance.Send_Command("AT+MSSTANDBY="+str(switchmode)+"\r")
        serinstance.settimeout(60)
        RSP = serinstance.checkResponse("CPIN: READY")
        if RSP is not "timeout":
            return True


    logger.info("--------end DMSS DMDS Switch--------")

#   longtime ping test updated by jackey at 1/16/2019
#  update pyserial util

def ping(serinstance,standbymode):
    logger.info("--------ping test was executed--------")
    serinstance.Send_Command("AT*MUSO=0\r")
    logger.debug("send AT*MUSO=0 command")
    RSP =  serinstance.checkResponse("OK")
    if RSP != "timeout":
        logger.debug(RSP)
    serinstance.settimeout(60000)
    logger.debug("send AT+PING=182.150.27.42 -n 6000 -d 1 ")
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 6000 -d 1\r')
    RSP =  serinstance.checkResponse("Lost=")
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result == 3000:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv(["%s" % standbymode,Realtime,'ping','Fail','ping success!'])
        return False
    else:
        if result  < 3000 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv(["%s" % standbymode,Realtime,'ping','Fail','ping failed'])
            return True
    time.sleep(1)


def daulstandbyvoicecallinterruptPING(serinstance,loop):

    serinstance.settimeout(2)
    executeAtCommand(ser,"AT*MUSO=0","OK")
    serinstance.settimeout(6)
    serinstance.Send_Command("at+PING=180.169.77.254 -n 20 -d 1 -w 20000\r")
    logger.debug("at+PING=180.169.77.254 -n 20 -d 1 -w 20000")
    time.sleep(6)
    serinstance.settimeout(2)
    serinstance.Send_Command("ATD112;\r")
    logger.debug("ATD112;")
    RSP =  serinstance.checkResponse("OK")
    logger.info(RSP)
    if RSP is not "timeout":
        logger.debug(" call was triggered!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Pass','call success triggered'])
    time.sleep(3)
    logger.debug("wait for 3 seconds")

    serinstance.Send_Command("ATH\r")
    logger.debug("ATH")
    serinstance.settimeout(2)
    logger.info("serial time out:%s" % serinstance.timeout)
    RSP =  serinstance.checkResponse("OK")
    logger.info(RSP)
    if RSP is not "timeout":
        logger.debug(" call was terminated!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'voicecallinterruptPING','Pass','call success ternimated'])
    #time.sleep(15)
    serinstance.settimeout(120)
    logger.info("serial time out:%s" % serinstance.timeout)
    RSP =  serinstance.checkResponse("Lost=")
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

    RSP =  serinstance.checkResponse("Lost=")
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


#created by jackey.jiang
#set psm mode under china mode
def setdualstandbypsm(serinstance,loop):

    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=1","OK")

    executeAtCommand(serinstance,"AT*MNBIOTEVENT=1,1","OK")

    executeAtCommand(serinstance,"at+cpsms=1,,,\"00100011\",\"00000001\"","OK")

    basictest(serinstance,loop)

    serinstance.settimeout(2)

    executeAtCommand(serinstance,"at+cpsms=0","OK")

    time.sleep(1)

    executeAtCommand(serinstance,"at+cpsms=1","OK")

 #created by jackey.jiang
 #

def dualstandbyctpsm(serinstance,loop):
    time.sleep(40)
    serinstance.settimeout(10)
    serinstance.Send_Command("AT\r")
    serinstance.Send_Command("AT*MUSO=1\r")
    logger.debug("send AT*MUSO=1 command")
    RSP =  serinstance.checkResponse("ENTER PSM")
    logger.info(RSP)
    if RSP != "timeout":
        logger.debug(" enter psm mode!")
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'dualstandbyctpsm','PASS','evb enter psm mode'])
    else:
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'dualstandbyctpsm','Fail','evb can\'t enter psm mode'])
        return False



    serinstance.settimeout(2)
    executeAtCommand(serinstance,"AT*MUSO=0","OK")
    serinstance.settimeout(20)
    logger.debug("send AT+PING=182.150.27.42 -n 1 -d 1 -w 20000 ")
    serinstance.Send_Command('AT+PING=182.150.27.42 -n 1 -d 1\r')

    RSP =  serinstance.checkResponse("Lost=")
    logger.info(RSP)
    ping_check_string=r'\+ping:.*?Lost = (\d.*?).*'
    parten=re.compile(ping_check_string)
    result=parten.findall(RSP)
    logger.debug(result)
    if result == 1:
        #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Fail",command_response)
        Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
        writercsv([loop,Realtime,'dualstandbyctpsm','fail','ping fail!'])
        return False
    else:
        if result  < 1 :
            #write_record(run_record_file,at_exe_time,'AT+Ping=182.150.27.42',"Pass",command_response)
            Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
            writercsv([loop,Realtime,'dualstandbyctpsm','Pass','ping pass'])
            return True


    return True

if __name__ == "__main__":

    print "start stress test"
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

    print("###############MT2621 STRESS Test################\r\n")
    print("1.DMDS/DMSS short ping test\r")
    print("2.DMDS/DMSS long time ping test\r")
    print("3.DMDS GSM VOICE CALL INTERUPT NB PING\r")
    print("4.DMDS China Telecomm psm stress test\r")
    input = raw_input("Please choose test:")
    print(input)
    choose = int(input.encode("utf-8"))
    print(type(choose))
    try:
		if 1 == choose:
			DMDSDMSSSWITCH(ser,1)
			if basictest(ser,1):
				checkGSM(ser,1)
				setidleflag(ser)
	 			for i in range(1000):
					shortpingwithout(ser,i,"dualstandbymode")
					DMDSDMSSSWITCH(ser,1)
			DMDSDMSSSWITCH(ser,0)
			if basictest(ser,1):
				setidleflag(ser)
				for i in range(1000):
					shortpingwithout(ser,i,"singlestandbymode")
		elif 2 == choose:
			DMDSDMSSSWITCH(ser,0)
			if basictest(ser,1):
				ping(ser,"DMSS")
			DMDSDMSSSWITCH(ser,1)
			if basictest(ser,1):
				checkGSM(ser,1)
				ping(ser,"DMDS")
		elif 3 == choose:
			DMDSDMSSSWITCH(ser,1)
			if basictest(ser,1):
				checkGSM(ser,1)
				for i in range(1000):
				    daulstandbyvoicecallinterruptPING(ser,"DMSS")
		elif 4 == choose:
			setdualstandbypsm(ser,1)
			for i in range(1000):
				dualstandbyctpsm(ser,i)



    except KeyboardInterrupt:
		observer.stop()

    observer.join()