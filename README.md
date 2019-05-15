ROS-Labeler
===============

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.

Environment
----------
- python 2.7
- python PIL (Pillow)

Run
-------
$ python main.py

Usage
-----
To create a new bounding box, left-click to select the first vertex. Moving the mouse to draw a rectangle, and left-click again to select the second vertex.
  - To cancel the bounding box while drawing, just press `<Esc>`.
  - To delete a existing bounding box, select it from the listbox, and press the `Backspace` key.
  - To delete all existing bounding boxes in the image, simply click `Clear`.
