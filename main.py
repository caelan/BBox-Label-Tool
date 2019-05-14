#!/usr/bin/env python2.7

from __future__ import division, print_function

try:
    from Tkinter import *
    #import tkMessageBox
except ImportError:
    from tkinter import *
from PIL import Image, ImageTk

import os
import glob
import random
import ttk

# colors for the bboxes
#COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
COLORS = ['red', 'blue', 'olive', 'teal', 'cyan', 'green', 'black']

CLASSES_PATH = 'classes.txt'

def load_classes(path):
    classes = []
    if not os.path.exists(path):
        return classes
    with open(path) as cf:
        for line in cf.readlines():
            classes.append(line.strip('\n'))
    return classes

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("ROS Image Labeler")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageList= []
        self.tkimg = None
        self.currentLabelclass = ''
        self.cla_can_temp = []

        # initialize mouse state
        self.STATE = {
            'click': 0,
            'x': 0,
            'y': 0,
        }

        # TODO: button to submit
        # TODO: continuously update the underlying image (with same boxes)

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI ---------------------
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, columnspan = 1, sticky = W+N)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame,state='readonly',textvariable=self.classname)
        self.classcandidate.grid(row=1,column=2)

        self.cla_can_temp = load_classes(CLASSES_PATH)
        print('Classes:', self.cla_can_temp)
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get() #init
        self.btnclass = Button(self.frame, text = 'ComfirmClass', command = self.setClass)
        self.btnclass.grid(row=2,column=2,sticky = W+E)

        # TODO: highlight selected box

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Boxes:')
        self.lb1.grid(row=3, column=2, sticky=W + N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row=4, column=2, sticky=N + S)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'Clear', command = self.clearBBox)
        self.btnClear.grid(row = 5, column = 3, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=6, column=1, columnspan=2, sticky=W + E)
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def loadDir(self):
        self.parent.focus()
        #if not os.path.isdir(s):
        #   tkMessageBox.showerror("Error!", message="The specified dir doesn't exist!")
        #   return
        category = 1
        # get image list
        imageDir = os.path.join(r'./Images', '%03d' %category)
        self.imageList = glob.glob(os.path.join(imageDir, '*.JPEG'))
        if len(self.imageList) == 0:
            print('No .JPEG images found in the specified dir!')
            return
        self.loadImage()

    def loadImage(self):
        # load image
        cur = 0
        imagepath = self.imageList[cur]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = self.tkimg.width(),
                              height = self.tkimg.height())
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.clearBBox()

    def mouseClick(self, event):
        if not self.tkimg:
            return
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((x1, y1, x2, y2, self.currentLabelclass))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % (self.currentLabelclass, x1, y1, x2, y2))
            color = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)]
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=color)
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        if not self.tkimg:
            return
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.hl:
            self.mainPanel.delete(self.hl)
        self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
        if self.vl:
            self.mainPanel.delete(self.vl)
        self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)

        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            color = COLORS[len(self.bboxList) % len(COLORS)]
            self.bboxId = self.mainPanel.create_rectangle(
                self.STATE['x'], self.STATE['y'], event.x, event.y, width=2, outline=color)

    def cancelBBox(self, event):
        if 1 != self.STATE['click']:
            return
        if self.bboxId:
            self.mainPanel.delete(self.bboxId)
            self.bboxId = None
            self.STATE['click'] = 0

    def getIndex(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return None
        idx = int(sel[0])
        return idx

    def delBBox(self):
        idx = self.getIndex()
        if idx is None:
            return
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def setClass(self):
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to :', self.currentLabelclass)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=False, height=False)
    root.mainloop()
