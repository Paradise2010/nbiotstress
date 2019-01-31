#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      mtbf
#
# Created:     24/01/2019
# Copyright:   (c) mtbf 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from pyser import pySer
import tkMessageBox
import time
import datetime
from threading import Thread, Event

class RandomAt:
    def __init__(self):
        self.ser=None
        self.window = tk.Tk()
        self.window.title("random to send at command")
        self.atlist={}
        self.btnlist={}
        self.execlist=[]
        leftFrame = tk.Frame(self.window)
        leftFrame.grid(column = 0 ,row = 0)
        self.textvar = tk.StringVar()
        # 滚动文本框
        self.scrolW = 60 # 设置文本框的长度
        self.scrolH = 55 # 设置文本框的高度
        self.scr = scrolledtext.ScrolledText(leftFrame, width=self.scrolW, height=self.scrolH, wrap=tk.WORD)
        self.scr.pack(side = "top")

        rightFrame = tk.Frame(self.window)
        rightFrame.grid(column = 1 ,row = 0)
        self.createAtCommand(rightFrame)

        bottomFrame = tk.Frame(self.window)
        bottomFrame.grid(column =0, row = 1,columnspan =2)
        comlabel = tk.Label(bottomFrame,text="AT comport:")
        comlabel.pack(side = "left",padx=1)
        self.comvar = tk.StringVar()
        comport = tk.Entry(bottomFrame,width=10,textvariable=self.comvar)
        comport.pack(side = "left",padx=4)
        startbtn = tk.Button(bottomFrame,text = "Start",command=self.start)
        startbtn.pack(side = "left",padx=4)
        stopbtn = tk.Button(bottomFrame,text = "Stop",command=self.stop)
        stopbtn.pack(side = "left",padx=4)
        selectbtn = tk.Button(bottomFrame,text = "SelectAll",command=self.selectall)
        selectbtn.pack(side = "left",padx=4)

        self.refresh_data()
        self.window.mainloop()

    def refresh_data(self):
        self.window.after(10000, self.refresh_data)
    def selectall(self):
        for k , v  in self.atlist.items():
				v.set(1)
    def start(self):
        if self.comvar.get() != None and self.ser == None:
            self.ser = pySer(self.comvar.get(),115200,10)
            self.ser.start()
        elif self.comvar.get() == None:
            tkMessageBox.showerror("Error","No com port! please fill it with \"COM1\" format.")
            return

        t = Thread(target=self.recdata)

        t.daemon = True
        t.start()
        for k , v  in self.atlist.items():
				if v.get() == 1:
					#print(type(v))
					#self.scr.insert("insert",self.btnlist[k]["text"])
					self.execlist.append(self.btnlist[k]["text"])
        if len(self.execlist) > 0:
            for at in self.execlist:
                print at
                self.ser.Send_Command(str(at)+"\r")
                time.sleep(1)



    def recdata(self):
        '''
        Receive an incoming message
        '''

        '''
        while True :
                self.scr.insert("end","start record...............\r")
                if not self.ser._mailbox.empty():
                    popmessage=self.ser._mailbox.get()
                    print(popmessage)
                    if popmessage != "":
                        self.scr.insert("end",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": "+popmessage+"\n")
        '''
        if not self.ser._mailbox.empty():
            popmessage=self.ser._mailbox.get()
            print(popmessage)
            if popmessage != "":
                self.scr.insert("end",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": "+popmessage+"\n")
        self.window.after(1000,self.recdata)


    def stop(self):
        if self.ser != None:
            self.ser.close()

    def createAtCommand(self,frame):
        with open("atcomand.txt","r") as f:
            i=0
            for line in f.readlines():

                strvar = tk.IntVar()
                self.atlist[i] = strvar
                strcheck = "check"+str(i)
                strcheck = tk.Checkbutton(frame, text=line.strip(), variable=strvar)
                self.btnlist[i] = strcheck
                strcheck.grid(column=0, row=i, sticky=tk.W)
                i = i + 1
def main():
    demo = RandomAt()

if __name__ == '__main__':
    main()
