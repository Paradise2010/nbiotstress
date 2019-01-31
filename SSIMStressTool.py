#-------------------------------------------------------------------------------
# Name:        SSIM stress tool
# Purpose:     convinence to use stress
#
# Author:     Jackey.jiang
#
# Created:     18/01/2019
# Copyright:   (c) mediatek 2019
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
from tkinter import *
from tkinter import scrolledtext

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



formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)



logger.addHandler(fh)


test_report_folder = os.path.join(os.getcwd(), "TestReport")
if os.path.exists(test_report_folder) is False:
	os.mkdir(test_report_folder)


Realtime=time.strftime("%Y%m%d_%H%M%S",time.localtime(time.time()))
reportName="TestReport_%s"%Realtime+".csv"

def writercsv(datalist):
    with open(os.path.join(test_report_folder,reportName),'a+b') as fwriter:
        writer=csv.writer(fwriter,dialect='excel')
        writer.writerow(datalist)

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

def main():
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    assertfilepath = config.get("mtbf","assertfile")
    comport = config.get("mtbf","port")
    powerrelayport = config.get("mtbf","powerrelayport")
    catchertool = config.get("mtbf","catchertool")
    tclcommand = config.get("mtbf","tclcommand")

    window = Tk()
    window.title("MSCH SSIM SI1 STRESS TOOL")
    window.geometry('600x600')

    assertLabel = Label(window,text="Assert File Path")
    assertLabel.grid(column=0,row=0)
    assertvar=StringVar()
    assertvar.set(assertfilepath)
    assertText = Entry(window,width=50,textvariable=assertvar)
    assertText.grid(column=1,row=0,columnspan=3,sticky=W)
    #assertText.configure(text=assertfilepath)

    comportLabel = Label(window,text="AT channel Port")
    comportLabel.grid(column=0,row=1)
    comportvar=StringVar()
    comportvar.set(comport)
    comportText = Entry(window,width=10,textvariable=comportvar)
    comportText.grid(column=1,row=1,columnspan=3,sticky=W,pady=5)

    powerrelayportLabel = Label(window,text="Power Relay Port")
    powerrelayportLabel.grid(column=0,row=2)
    powerrelayportvar=StringVar()
    powerrelayportvar.set(powerrelayport)
    powerrelayportText = Entry(window,width=10,textvariable=powerrelayportvar)
    powerrelayportText.grid(column=1,row=2,columnspan=3,sticky=W,pady=5)

    catchertoolLabel = Label(window,text="Catch Tool path")
    catchertoolLabel.grid(column=0,row=3)
    catchertoolvar=StringVar()
    catchertoolvar.set(catchertool)
    catchertoolText = Entry(window,width=50,textvariable=catchertoolvar)
    catchertoolText.grid(column=1,row=3,columnspan=3,sticky=W,pady=5)

    tclcommandLabel = Label(window,text="Tcl Command Script")
    tclcommandLabel.grid(column=0,row=4)
    tclcommandvar=StringVar()
    tclcommandvar.set(tclcommand)
    tclcommandText = Entry(window,width=50,textvariable= tclcommandvar)
    tclcommandText.grid(column=1,row=4,columnspan=3,sticky=W,pady=5)
    chk_state = BooleanVar()

    chk = Checkbutton(window, text='ShortPingwithoutPSM', var=chk_state)
    chk1_state = BooleanVar()

    chk1 = Checkbutton(window, text='InitialAttach', var=chk1_state)
    chk2_state = BooleanVar()

    chk2 = Checkbutton(window, text='LongtimePing', var=chk2_state)
    chk3_state = BooleanVar()

    chk3 = Checkbutton(window, text='CTShortPingwithPSM', var=chk3_state)
    chk4_state = BooleanVar()

    chk4 = Checkbutton(window, text='voicecallinteruptshortpingwithoutPSM', var=chk4_state)
    chk5_state = BooleanVar()

    chk5 = Checkbutton(window, text='ModeChange', var=chk5_state)
    chk.grid(column=0,row=5,sticky=W)
    chk1.grid(column=1,row=5,sticky=W)
    chk2.grid(column=2,row=5,sticky=W)
    chk3.grid(column=0,row=6,sticky=W)
    chk4.grid(column=1,row=6,sticky=W)
    chk5.grid(column=2,row=6,sticky=W)
    txt = scrolledtext.ScrolledText(window,width=80,height=20)
    txt.grid(column=0,row=7,columnspan=4,sticky=W,pady=5)

    congbtn = Button(window, text="Save config", command=saveconfig)
    congbtn.grid(column=0,row=8,sticky=W,pady=5)
    execbtn = Button(window, text="Start Test", command=starttest)
    execbtn.grid(column=2,row=8,sticky=W,pady=5)
    # Create textLogger

    text_handler = TextHandler(txt)
    text_handler.setFormatter(formatter)
    text_handler.setLevel(logging.DEBUG)
    logger.addHandler(text_handler)

    window.mainloop()

def saveconfig():
    pass

def starttest():
    pass

if __name__ == '__main__':
    main()
