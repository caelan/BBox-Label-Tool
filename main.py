#!/usr/bin/env python2.7

from __future__ import division, print_function
from collections import namedtuple

LabeledBox = namedtuple('LabeledBox', ['label', 'x1', 'y1', 'x2', 'y2'])

try:
    from Tkinter import *
    import ttk
    #import tkMessageBox
except ImportError:
    from tkinter import *
from PIL import Image, ImageTk

import time
import os

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

    def __init__(self, root):
        # set up the main frame
        self.root = root
        self.root.title("ROS Image Labeler")
        #self.root.configure(background='grey')
        frame = Frame(self.root, background='tan')
        frame.pack(fill=BOTH, expand=True)
        self.root.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.image_path = os.path.join(r'./Images', '%03d' % 1, 'test.jpeg')
        self.tkimg = None

        # initialize mouse state
        self.click = False
        self.x = 0
        self.y = 0
        # TODO: continuously update the underlying image (with same boxes)

        # reference to bbox
        self.start_time = time.time()
        self.box_list = []
        self.box_id_list = []
        self.current_box_id = None
        self.publishing = False
        self.hl = None
        self.vl = None

        # ----------------- GUI ---------------------
        # main panel for labeling
        self.disp_lb = Label(frame, text='')
        self.disp_lb.grid(row=0, column=0, sticky=W + N)
        self.main_panel = Canvas(frame, cursor='tcross')
        self.main_panel.bind("<Button-1>", self.mouse_click_cb)
        self.main_panel.bind("<Motion>", self.mouse_move_cb)
        self.root.bind("<Return>", self.start_publishing)
        self.root.bind("<BackSpace>", self.delete_box)
        self.root.bind("d", self.delete_box)
        self.root.bind("<Escape>", self.cancel_box)
        # TODO: additional hotkeys for toggling classes

        self.main_panel.grid(row=1, column=0,  # rowspan=1, columnspan=1,
                            sticky=W + N)
        self.publish_lb = Label(frame, text='')
        self.publish_lb.grid(row=2, column=0, sticky=W + N)

        # choose class
        class_frame = Frame(frame)
        class_frame.grid(row=0, column=1, sticky=W + E)
        class_lb = Label(class_frame, text='Class:')
        class_lb.pack(side=LEFT)
        self.class_name = StringVar()
        self.class_selector = ttk.Combobox(
            class_frame, state='readonly', textvariable=self.class_name)
        self.class_selector.pack(side=RIGHT)
        self.class_selector['values'] = load_classes(CLASSES_PATH)
        self.class_selector.current(0)
        print('Classes:', self.classes)

        # showing bbox info & delete bbox
        self.listbox = Listbox(frame, #selectmode='multiple', exportselection=True,
                               width=22, height=12)
        self.listbox.grid(row=1, column=1, columnspan=1, sticky=N + S)

        btn_frame = Frame(frame)
        btn_frame.grid(row=2, column=1, sticky=W + E)
        self.pub_btn = Button(btn_frame, text='Publish',
                              command=self.start_publishing)
        self.pub_btn.pack(side=LEFT, expand=True, fill='both')
        self.clear_btn = Button(btn_frame, text='Reset',
                                command=self.clear_boxes)
        self.clear_btn.pack(side=RIGHT, expand=True, fill='both')

        #frame.columnconfigure(1, weight=1)
        #frame.rowconfigure(4, weight=1)
        # tkMessageBox.showerror("Error!", message="The specified dir doesn't exist!")

        self.root.focus()
        self.load_image()

    @property
    def classes(self):
        return self.class_selector['values']

    @property
    def current_class(self):
        return self.class_selector.get()

    @property
    def current_color(self):
        index = self.classes.index(self.current_class)
        return COLORS[index % len(COLORS)]

    @property
    def selected_indices(self):
        return self.listbox.curselection()

    def start_publishing(self, *args):
        self.publishing = True
        self.publish_lb.config(text='Publishing {} boxes [t={:.1f}]'.format(
            len(self.box_list), time.time() - self.start_time))

    def stop_publishing(self):
        self.publishing = False
        self.publish_lb.config(text='')

    def load_image(self):
        self.img = Image.open(self.image_path)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.main_panel.config(width=self.tkimg.width(),
                               height=self.tkimg.height())
        self.main_panel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.clear_boxes()

    def mouse_click_cb(self, event):
        if not self.tkimg:
            return
        if not self.click:
            self.x, self.y = event.x, event.y
        else:
            x1, x2 = min(self.x, event.x), max(self.x, event.x)
            y1, y2 = min(self.y, event.y), max(self.y, event.y)
            self.box_list.append(LabeledBox(self.current_class, x1, y1, x2, y2))
            self.box_id_list.append(self.current_box_id)
            self.current_box_id = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' % self.box_list[-1])
            self.listbox.itemconfig(len(self.box_id_list) - 1, fg=self.current_color)
        self.click = not self.click

    def draw_box(self, x1, y1, x2, y2):
        # TODO: take in the current color
        return self.main_panel.create_rectangle(
            x1, y1, x2, y2, width=2, outline=self.current_color)

    def mouse_move_cb(self, event):
        if not self.tkimg:
            return
        # TODO: highlight the selected box
        self.disp_lb.config(text='Cursor: x=%d, y=%d' % (event.x, event.y))
        if self.hl:
            self.main_panel.delete(self.hl)
        self.hl = self.main_panel.create_line(
            0, event.y, self.tkimg.width(), event.y, width=2)

        if self.vl:
            self.main_panel.delete(self.vl)
        self.vl = self.main_panel.create_line(
            event.x, 0, event.x, self.tkimg.height(), width=2)

        if self.click:
            if self.current_box_id:
                self.main_panel.delete(self.current_box_id)
            self.current_box_id = self.draw_box(self.x, self.y, event.x, event.y)

    def cancel_box(self, *args):
        if not self.click:
            return
        if self.current_box_id:
            self.main_panel.delete(self.current_box_id)
            self.current_box_id = None
            self.click = False

    def delete_box(self, *args):
        for idx in self.selected_indices:
            self.stop_publishing()
            self.main_panel.delete(self.box_id_list[idx])
            self.box_id_list.pop(idx)
            self.box_list.pop(idx)
            self.listbox.delete(idx)

    def clear_boxes(self):
        self.stop_publishing()
        for idx in range(len(self.box_id_list)):
            self.main_panel.delete(self.box_id_list[idx])
        self.listbox.delete(0, len(self.box_list))
        self.box_id_list = []
        self.box_list = []

if __name__ == '__main__':
    root = Tk()
    tool = ImageLabeler(root)
    root.mainloop()

# autopep8 main.py -i
