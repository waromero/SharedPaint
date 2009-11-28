#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : View.py
# Purpose: GUI classes.
# Author : Henry Caballero 	<hh.caballero921@uniandes.edu.co>
#          William A. Romero R.	<wil-rome@uniandes.edu.co>
#          
#
# This product includes software derived from the Access Grid project
# <http://www.accessgrid.org>.
# 
#
#    Copyright (C) 2009
#    IMAGINE research group	<http://imagine.uniandes.edu.co>
#    Universidad de los Andes	<http://www.uniandes.edu.co>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

__author__  = "Henry Caballero <hh.caballero921@uniandes.edu.co>, William A. Romero R. <wil-rome@uniandes.edu.co>"
__license__ = "GNU GPL"
__version__ = "3.0"
__revision__ = "$Id: View.py,v 1.2 2009/05/06 14:47:11 agmoxdev Exp$"

import sys
import os
import wx
import wx.html
import datetime

from Model import SharedPaintSession
from Model import Annotation
from Exceptions import SharedPaintException
from AccessGrid import icons
from wx.lib import buttons # for generic button classes

menuColors = [ "#000000", # Black
               "#800000", # Dark red
               "#FF0000", # Red
               "#008000", # Dark green
               "#808000", # Dark yellow
               "#00FF00", # Green
               "#FFFF00", # Yellow
               "#000080", # Dark blue
               "#800080", # Dark purple
               "#008080", # Dark teal
               "#808080", # Dark grey
               "#C0C0C0", # Light gray
               "#0000FF", # Blue
               "#FF00FF", # Purple
               "#00FFFF", # Teal
               "#FFFFFF", # White
               ]

maxThickness = 7

defaultImageSize = (520, 390)

class SharedPaintGUI(wx.Frame):
    """Main GUI class of SharedPaint application."""

    def __init__(self, model):
        """The constructor."""
        wx.Frame.__init__(self, None, -1, "SharedPaint", wx.DefaultPosition, wx.Size(800, 600))

        # Model instance
        self.__model = model

        # List containing the participants' IDs
        self.__participants = []

        # Main sizer
        workspaceSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(workspaceSizer)

        # Center panel
        centerPanel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
        centerPanel.SetBackgroundColour("#BBBBBB")
        sizer = wx.BoxSizer(wx.VERTICAL)
        centerPanel.SetSizer(sizer)
        self.doodle = DoodleWindow(centerPanel, self.__model)
        sizer.Add(self.doodle, 1, wx.EXPAND | wx.ALL, 1) 
        workspaceSizer.Add(centerPanel, 1, wx.EXPAND | wx.ALL, 1)

        # Imagelist containing penColor images
        il = wx.ImageList(24, 24, True)
        pen = wx.Bitmap("pen.png", wx.BITMAP_TYPE_PNG).ConvertToImage()
        for color in menuColors:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            penImage = pen.Copy()
            penImage.Replace(204, 0, 204, r, g, b)
            il.Add(penImage.ConvertToBitmap())

        # Right panel
        rightPanel = wx.Panel(self, -1, size=(200, 0))
        rightPanelSizer = wx.BoxSizer(wx.VERTICAL)
        rightPanel.SetSizer(rightPanelSizer)
        # List of participants
        staticBox = wx.StaticBox(rightPanel, -1, "Participants")
        sizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        self.__list = wx.ListView(rightPanel, -1, size=(200, 0), style=wx.LC_SMALL_ICON)
        self.__list.SetBackgroundColour(wx.WHITE)
        self.__list.AssignImageList(il, wx.IMAGE_LIST_SMALL)
        sizer.Add(self.__list, 1, wx.EXPAND | wx.ALL, 1)
        rightPanelSizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 1)
        # Control panel
        staticBox = wx.StaticBox(rightPanel, -1, "Pen settings")
        sizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        self.ctrlPanel = ControlPanel(rightPanel, self.__model.PenColor, self.__model.PenThickness)
        sizer.Add(self.ctrlPanel, 1, wx.EXPAND | wx.ALL, 1)
        rightPanelSizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 1)
        workspaceSizer.Add(rightPanel, 0, wx.EXPAND | wx.ALL, 1)

        # Application icon
        self.SetIcon(icons.getAGIconIcon())

        # Menu
        menuBar = wx.MenuBar()

        session = wx.Menu()
        #session.Append(101, "&Join", "Join to the SharedPaint drawing session")
        session.Append(102, "&Take snapshot", "Save the current session status: snapshot")
        session.Append(103, "&Load snapshot...", "Load a saved snapshot")
        session.Append(104, "&Quit", "Quit the application")
        menuBar.Append(session, "&Session")

        imageMenu = wx.Menu()
        imageMenu.Append(201, "&Load from server", "Load an image from the Venue Server as background")
        imageMenu.Append(202, "Clear", "Quit the current background image")
        menuBar.Append(imageMenu, "&Image")

        drawing = wx.Menu()
        drawing.Append(301, "&Clear", "Remove all the annotations")
        drawing.Append(302, "&Undo", "Remove the last annotation made by the participant")
        menuBar.Append(drawing, "&Annotations")

        help = wx.Menu()
        #help.Append(401, "User Manual", "Open the SharedPaint user manual")
        help.Append(402, "About", "About SharedPaint")
        menuBar.Append(help, "&Help")

        self.SetMenuBar(menuBar)

        # Status bar
        self.__statusbar = self.CreateStatusBar()

        toolbar = self.CreateToolBar()
        toolbar.SetToolBitmapSize((24, 24))
        toolbar.AddLabelTool(102, "", wx.Bitmap("session_snapshot.gif"),
                             longHelp="Save the current session status: snapshot")
        toolbar.AddLabelTool(103, "", wx.Bitmap("session_load.gif"),
                             longHelp="Load a saved snapshot")
        toolbar.AddLabelTool(201, "", wx.Bitmap("image_load.gif"),
                             longHelp="Load an image from the Venue Server as background")
        toolbar.AddLabelTool(202, "", wx.Bitmap("image_clear.gif"),
                             longHelp="Quit the current background image")
        toolbar.AddLabelTool(301, "", wx.Bitmap("annotations_clear.gif"),
                            longHelp="Remove all the annotations")
        toolbar.Realize()

    def AddParticipant(self, participant):
        """Shows a new participant into the participant's widget."""
        itemIndex = self.__list.GetItemCount()
        imageIndex = menuColors.index(participant.PenColor)
        self.__participants.append(participant.Id)
        self.__list.InsertImageStringItem(itemIndex, participant.Name, imageIndex)

    def UpdateParticipant(self, participant):
        """Updates a participant status into the participant's widget."""
        itemIndex = self.__participants.index(participant.Id)
        imageIndex = menuColors.index(participant.PenColor)
        self.__list.SetItemText(itemIndex, participant.Name)
        self.__list.SetItemImage(itemIndex, imageIndex)

    def RemoveParticipant(self, participantId):
        """Removes a given participant from the participant's widget."""
        itemIndex = self.__participants.index(participantId)
        del self.__participants[itemIndex]
        self.__list.DeleteItem(itemIndex)

    def HandleJoined(self):
        """Updates the UI for showing the client current status (called by the controller)."""
        print "User has joined the session"

    def HandleNetworkProblems(self):
        """(Called by the controller)."""
        print "Network problems"

    def HandleDrawingOffline(self):
        """(Called by the controller)."""
        print "Drawing offline"

#-----------------------------------------------------------------------------

class DoodleWindow(wx.ScrolledWindow):
    """Canvas for drawing."""

    def __init__(self, parent, model):
        """The constructor."""
        wx.ScrolledWindow.__init__(self, parent, -1)

        # Model instance
        self.__model = model

        # Bitmap used for buffering the display
        self.__workspaceBuffer = None
        # Bitmap used for storing the background image
        self.__imageBuffer = None

        self.SetScrollRate(1, 1)

        # Cursor icon
        self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

        # Model callbacks (observer pattern)
        self.__model.EVT_LINE(self.__HandleLine)
        self.__model.EVT_CLEAR(self.__HandleClear)

        # UI callbacks
        wx.EVT_PAINT(self, self.__OnPaint)

    def __OnPaint(self, event):
        """Called when the window must be redrawn."""
        if self.__workspaceBuffer is None:
            self.__InitWorkspaceBuffer()

        xOffset = self.GetScrollPos(wx.HORIZONTAL)
        yOffset = self.GetScrollPos(wx.VERTICAL)

        # Create bitmap containing the visualized area
        bitmap = wx.EmptyBitmap(self.__workspaceBuffer.GetWidth(), self.__workspaceBuffer.GetHeight())
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        dc.DrawBitmap(self.__workspaceBuffer, -xOffset, -yOffset)
        del dc

        # Update screen using a buffered DC        
        wx.BufferedPaintDC(self, bitmap)

    def __DrawLines(self, dc):
        """Redraws all the lines contained in the SharedPaint session"""
        dc.BeginDrawing()
        for ann in self.__model.GetAnnotations():
            pen = wx.Pen(ann.PenSettings[0], ann.PenSettings[1], wx.SOLID)
            dc.SetPen(pen)
            points = len(ann.Drawing)
            if points == 0:
                continue
            elif points == 1:
                (x1 , y1) = ann.Drawing[0]
                (x2 , y2) = ann.Drawing[0]
                dc.DrawLine(x1, y1, x2, y2)
            else:
                for i in range(len(ann.Drawing) - 1):
                    (x1 , y1) = ann.Drawing[i]
                    (x2 , y2) = ann.Drawing[i + 1]
                    if (x1, y1) == (-1, -1) or (x2, y2) == (-1, -1):
                        continue
                    dc.DrawLine(x1, y1, x2, y2)
        dc.EndDrawing()

    def __InitWorkspaceBuffer(self):
        """Initializes the bitmap containing the entire workspace."""
        if self.__imageBuffer is None:
            self.__InitImageBuffer()

        size = self.__imageBuffer.GetSize()
        self.__workspaceBuffer = wx.EmptyBitmap(size[0], size[1])
        dc = wx.MemoryDC()
        dc.SelectObject(self.__workspaceBuffer)
        dc.DrawBitmap(self.__imageBuffer, 0, 0)
        self.__DrawLines(dc)
        del dc

    def __InitImageBuffer(self):
        """Initializes the bitmap used as background."""
        self.__imageBuffer = wx.EmptyBitmap(defaultImageSize[0], defaultImageSize[1])
        dc = wx.MemoryDC()
        dc.SelectObject(self.__imageBuffer)
        dc.SetBrush(wx.Brush("WHITE"))
        dc.Clear()
        del dc
        self.SetVirtualSize(self.__imageBuffer.GetSize())

    def __HandleLine(self, penSettings, p1, p2):
        """Called when a new line is added to the SharedPaint session."""
        if p1 == (-1, -1) or p2 == (-1, -1):
            return 

        xOffset = self.GetScrollPos(wx.HORIZONTAL)
        yOffset = self.GetScrollPos(wx.VERTICAL)

        # Draw line onto buffer
        dc = wx.MemoryDC()
        dc.SelectObject(self.__workspaceBuffer)
        dc.SetPen(wx.Pen(penSettings[0], penSettings[1], wx.SOLID))
        dc.BeginDrawing()
        dc.DrawLine(p1[0], p1[1], p2[0], p2[1])
        dc.EndDrawing()
        del dc

        # Update window using its Device context (DC)
        wx.ClientDC(self).DrawBitmap(self.__workspaceBuffer, -xOffset, -yOffset)

    def __HandleClear(self):
        """Called when the SharedPaint session is cleared."""
        self.__InitWorkspaceBuffer()
        self.Refresh()

    def SetBackground(self, imageFile):
        """Sets a new background image, given its filename."""
        try:
            image = wx.Bitmap(imageFile, wx.BITMAP_TYPE_ANY)
            dc = wx.MemoryDC()
            dc.SelectObject(image)
            dc.DrawBitmap(image, 0, 0)
            del dc

            self.__imageBuffer = image
            self.SetVirtualSize(self.__imageBuffer.GetSize())
            self.__InitWorkspaceBuffer()
            self.Refresh()
        except Exception, e:
            raise SharedPaintException("The image could not be processed")

    def ClearBackground(self):
        """Clears the background image."""
        self.__workspaceBuffer = None
        self.__imageBuffer = None
        self.Refresh()

#-----------------------------------------------------------------------------

class ControlPanel(wx.Panel):
    """This class implements a very simple control panel for the DoodleWindow.
    It creates buttons for each of the colors and thickneses supported by
    the DoodleWindow, and event handlers to set the selected values.  There is
    also a little window that shows an example doodleLine in the selected
    values.  Nested sizers are used for layout."""

    BMP_SIZE = 16
    BMP_BORDER = 3

    def __init__(self, parent, color, thickness):
        """The constructor."""
        wx.Panel.__init__(self, parent, -1, size=(20,20))

        (self.color, self.thickness) = (color, thickness)      

        self.__eventsCallbacks = {}
        self.__eventsCallbacks["EVT_PEN_UPDATE"] = []

        numCols = 8
        spacing = 4

        btnSize = wx.Size(self.BMP_SIZE + 2 * self.BMP_BORDER,
                          self.BMP_SIZE + 2 * self.BMP_BORDER)

        # Make a grid of buttons for each color.  Attach each button
        # event to self.OnSetColor.  The button ID is the same as the
        # key in the color dictionary.
        self.clrBtns = {}

        colorID = 0
        cGrid = wx.GridSizer(cols=numCols, hgap=2, vgap=2)
        for color in menuColors:
            bmp = self.__MakeBitmap(color)
            b = buttons.GenBitmapToggleButton(self, colorID, bmp, size=btnSize)
            b.SetBezelWidth(1)
            b.SetUseFocusIndicator(False)
            self.Bind(wx.EVT_BUTTON, self.__OnSetColor, b)
            cGrid.Add(b, 0)
            self.clrBtns[colorID] = b
            colorID = colorID + 1
        self.clrBtns[0].SetToggle(True)

        # color indicator
        self.__ci = ColorIndicator(self, self.color, self.thickness)

        self.__thicknessSlider = wx.Slider(self, style=wx.SL_AUTOTICKS)
        self.__thicknessSlider.SetRange(1, maxThickness)
        self.Bind(wx.EVT_SLIDER, self.__OnSetThickness, self.__thicknessSlider)

        # Make a box sizer and put the two grids and the indicator
        # window in it.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(cGrid, 0, wx.ALL, spacing)
        box.Add(self.__thicknessSlider, 0, wx.EXPAND | wx.ALL, spacing)
        box.Add(self.__ci, 0, wx.EXPAND | wx.ALL, spacing)
        self.SetSizer(box)

        # Resize this window so it is just large enough for the
        # minimum requirements of the sizer.
        box.Fit(self)

    def EVT_PEN_UPDATE(self, callback):
        """Registers a new callback for EVT_UPDATE event."""
        self.__eventsCallbacks["EVT_PEN_UPDATE"].append(callback)

    def __MakeBitmap(self, color):
        """Creates a bitmap used for representing a given pen color."""
        bmp = wx.EmptyBitmap(self.BMP_SIZE, self.BMP_SIZE)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetBackground(wx.Brush(color))
        dc.Clear()
        dc.SelectObject(wx.NullBitmap)
        return bmp

    def __OnSetColor(self, event):
        """Called when a color button is clicked."""
        c = menuColors[event.GetId()]

        if c != self.color:
            # untoggle the old color button
            self.clrBtns[menuColors.index(self.color)].SetToggle(False)
        else:
            self.clrBtns[event.GetId()].SetToggle(True)

        self.color = c
        for callback in self.__eventsCallbacks["EVT_PEN_UPDATE"]:
            callback(color=self.color)
        self.__ci.Update(self.color, self.thickness)

    def __OnSetThickness(self, eventt):
        """Called when the value of thickness' slider changes."""
        self.thickness = self.__thicknessSlider.GetValue()

        for callback in self.__eventsCallbacks["EVT_PEN_UPDATE"]:
            callback(thickness=self.thickness)
        self.__ci.Update(self.color, self.thickness)

#-----------------------------------------------------------------------------

class ColorIndicator(wx.Window):
    """Window for drawing a line using the current pen color and thickness."""

    def __init__(self, parent, color, thickness):
        """The constructor."""
        wx.Window.__init__(self, parent, -1, style=wx.SUNKEN_BORDER)
        self.SetBackgroundColour(wx.WHITE)
        self.SetSize((45, 45))
        (self.color, self.thickness) = (color, thickness)
        self.Bind(wx.EVT_PAINT, self.__OnPaint)

    def __OnPaint(self, event):
        """Draws the window."""
        dc = wx.PaintDC(self)
        if self.color:
            sz = self.GetClientSize()
            pen = wx.Pen(self.color, self.thickness)
            dc.SetPen(pen)
            dc.DrawLine(10, sz.height/2, sz.width-10, sz.height/2)    

    def Update(self, color, thickness):
        """Updates the color and thickness."""
        (self.color, self.thickness) = (color, thickness)
        self.Refresh()  # fire a paint event

#-----------------------------------------------------------------------------

class ItemPicker(wx.Dialog):
    """Dialog for displaying a list of items."""    

    def __init__(self, parent, title, items):
        """The constructor.""" 
        wx.Dialog.__init__(self, parent, -1, title)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.items = wx.ListBox(self,-1)
        self.items.InsertItems(items, 0)        

        bpanel = wx.Panel(self, -1) 
        bsizer = wx.BoxSizer(wx.HORIZONTAL) 

        okbutton = wx.Button(bpanel, wx.NewId(), "Ok") 
        cancelbutton = wx.Button(bpanel, wx.NewId(), "Cancel") 

        bsizer.Add(okbutton, 1, wx.EXPAND | wx.ALL, 5) 
        bsizer.Add(cancelbutton, 1, wx.EXPAND | wx.ALL, 5) 

        bpanel.SetSizer(bsizer)
        bsizer.SetSizeHints(bpanel) 

        sizer.Add(self.items, 1, wx.EXPAND | wx.ALL, 5) 
        sizer.Add(bpanel, 0, wx.EXPAND | wx.ALL, 5) 

        self.SetSizer(sizer)
        sizer.SetSizeHints(self) 

        self.selected_item = None 

        wx.EVT_BUTTON(self, okbutton.GetId(), self.__OnOk) 
        wx.EVT_BUTTON(self, cancelbutton.GetId(), self.__OnCancel)

        self.__OnOkCallback = None 

    def __OnOk(self, event): 
        """Called when the Ok button is clicked."""
        self.selected_item = self.items.GetStringSelection()
        self.Close(True)
        if self.__OnOkCallback is not None:
            self.__OnOkCallback(self.selected_item)

    def __OnCancel(self, event):
        """Called when the Cancel button is clicked."""
        self.Close(True)

    def ShowDialog(self, visible, callback = None):
        """Shows/hides the dialog."""
        self.__OnOkCallback = callback
        self.Show(visible)

#-----------------------------------------------------------------------------

class AboutDialog(wx.SplashScreen):
    """SharedPaint about dialog."""

    def __init__(self, parent=None):
        """The constructor.""" 
        aBitmap = wx.Image(name = "sharedpaint_about.png").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, -1, parent)
        wx.Yield()

        wx.EVT_LEFT_DOWN(self, self.__OnMouseDown)

    def __OnMouseDown(self):
        """Click on splash image."""
        pass

#-----------------------------------------------------------------------------

class WelcomeDialog(wx.SplashScreen):
    """SharedPaint splash screen."""

    def __init__(self, parent=None):
        """The constructor."""
        aBitmap = wx.Image(name = "sharedpaint_start.png").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 3000 # milliseconds
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, splashDuration, parent)
        wx.Yield()

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    """Test."""
    app = wx.PySimpleApp()
    frame = SharedPaintGUI(SharedPaintSession())
    frame.Show()
    frame.Centre()
    app.SetTopWindow(frame)
    app.MainLoop()
