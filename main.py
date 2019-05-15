#!/usr/bin/env python2.7

from __future__ import division, print_function

try:
    from Tkinter import *
    import ttk
    #import tkMessageBox
except ImportError:
    from tkinter import *
from PIL import Image, ImageTk

import os
import glob

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

# http://tcl.tk/man/tcl8.5/TkCmd/options.htm#M-exportselection

class ImageLabeler(object):

    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("ROS Image Labeler")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.image_path = os.path.join(r'./Images', '%03d' % 1, 'test.jpeg')
        self.tkimg = None
        self.cla_can_temp = []

        # initialize mouse state
        self.click = False
        self.x = 0
        self.y = 0
        # TODO: button to submit
        # TODO: continuously update the underlying image (with same boxes)

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI ---------------------
        # main panel for labeling
        self.disp_lb = Label(self.frame, text='')
        self.disp_lb.grid(row=0, column=0, sticky=W + N)
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouse_click_cb)
        self.mainPanel.bind("<Motion>", self.mouse_move_cb)
        self.parent.bind("<Return>", self.delete_box)
        self.parent.bind("<BackSpace>", self.delete_box)
        self.parent.bind("d", self.delete_box)
        self.parent.bind("<Escape>", self.cancel_box)
        # TODO: additional hotkeys for toggling classes

        self.mainPanel.grid(row=1, column=0, rowspan=1,
                            columnspan=1, sticky=W + N)

        # choose class
        self.class_frame = Frame(self.frame)
        self.class_frame.grid(row=0, column=1, sticky=W + E)
        self.class_lb = Label(self.class_frame, text='Class:')
        #self.class_lb.grid(row=0, column=1, sticky=W + N)
        self.class_lb.pack(side=LEFT)
        self.class_name = StringVar()
        self.classcandidate = ttk.Combobox(
            self.class_frame, state='readonly', textvariable=self.class_name)
        self.classcandidate.pack(side=RIGHT)
        #self.classcandidate.grid(row=0, column=2)
        self.classcandidate['values'] = load_classes(CLASSES_PATH)
        self.classcandidate.current(0)
        print('Classes:', self.classes)

        # showing bbox info & delete bbox
        self.listbox = Listbox(self.frame, #selectmode='multiple', exportselection=True,
                               width=22, height=12)
        self.listbox.grid(row=1, column=1, columnspan=1, sticky=N + S)

        ctrPanel = Frame(self.frame)
        ctrPanel.grid(row=2, column=1, sticky=W + E)
        self.btnDel = Button(ctrPanel, text='Publish',
                             command=self.delete_box)
        #self.btnDel.grid(row=2, column=1, sticky=W + E + N)
        self.btnDel.pack(side=LEFT, expand=True, fill='both')
        self.btnClear = Button(ctrPanel, text='Reset',
                               command=self.clear_boxes)
        self.btnClear.pack(side=RIGHT, expand=True, fill='both')
        #self.btnClear.grid(row=2, column=2, sticky=W + E + N)

        #self.frame.columnconfigure(1, weight=1)
        #self.frame.rowconfigure(4, weight=1)
        # tkMessageBox.showerror("Error!", message="The specified dir doesn't exist!")

        self.parent.focus()
        self.load_image()

    @property
    def classes(self):
        return self.classcandidate['values']

    @property
    def current_class(self):
        return self.classcandidate.get()

    @property
    def current_color(self):
        index = self.classes.index(self.current_class)
        return COLORS[index % len(COLORS)]

    @property
    def selected_indices(self):
        return self.listbox.curselection()

    def load_image(self):
        self.img = Image.open(self.image_path)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width=self.tkimg.width(),
                              height=self.tkimg.height())
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.clear_boxes()

    def mouse_click_cb(self, event):
        if not self.tkimg:
            return
        if not self.click:
            self.x, self.y = event.x, event.y
        else:
            x1, x2 = min(self.x, event.x), max(self.x, event.x)
            y1, y2 = min(self.y, event.y), max(self.y, event.y)
            self.bboxList.append((x1, y1, x2, y2, self.current_class))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %
                                (self.current_class, x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=self.current_color)
        self.click = not self.click

    def draw_box(self, x1, y1, x2, y2):
        # TODO: take in the current color
        return self.mainPanel.create_rectangle(
            x1, y1, x2, y2, width=2, outline=self.current_color)

    def mouse_move_cb(self, event):
        if not self.tkimg:
            return
        # TODO: highlight the selected box
        self.disp_lb.config(text='Cursor: x=%d, y=%d' % (event.x, event.y))
        if self.hl:
            self.mainPanel.delete(self.hl)
        self.hl = self.mainPanel.create_line(
            0, event.y, self.tkimg.width(), event.y, width=2)

        if self.vl:
            self.mainPanel.delete(self.vl)
        self.vl = self.mainPanel.create_line(
            event.x, 0, event.x, self.tkimg.height(), width=2)

        if self.click:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.draw_box(self.x, self.y, event.x, event.y)

    def cancel_box(self, *args):
        if not self.click:
            return
        if self.bboxId:
            self.mainPanel.delete(self.bboxId)
            self.bboxId = None
            self.click = False

    def delete_box(self, *args):
        for idx in self.selected_indices:
            self.mainPanel.delete(self.bboxIdList[idx])
            self.bboxIdList.pop(idx)
            self.bboxList.pop(idx)
            self.listbox.delete(idx)

    def clear_boxes(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

if __name__ == '__main__':
    root = Tk()
    tool = ImageLabeler(root)
    root.resizable(width=False, height=False)
    root.mainloop()

# autopep8 main.py -i
