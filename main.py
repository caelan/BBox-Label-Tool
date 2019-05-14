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

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageList= []
        self.tkimg = None

        # initialize mouse state
        self.STATE = {
            'click': 0,
            'x': 0,
            'y': 0,
        }

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, columnspan = 1, sticky = W+N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Boxes:')
        self.lb1.grid(row = 1, column = 2, columnspan = 2, sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 2, column = 2, columnspan = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 3, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'Clear', command = self.clearBBox)
        self.btnClear.grid(row = 3, column = 3, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 5, column = 0, columnspan = 2, sticky = W+E)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

    def loadDir(self):
        s = self.entry.get()
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
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
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

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
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

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width=False, height=False)
    root.mainloop()
