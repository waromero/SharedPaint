#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : Controller.py
# Purpose: Controller for SharedPaint (MVC pattern)
# Author : Henry Caballero 	<hh.caballero921@uniandes.edu.co>
#          William A. Romero R.	<wil-rome@uniandes.edu.co>
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
__revision__ = "$Id: Controller.py,v 1.1 2009/05/06 05:31:44 agmoxdev Exp$"

import wx

from Model import Annotation
from Model import SharedPaintParticipant
from Messaging import MessagingException
from View import ItemPicker
from View import WelcomeDialog
from View import AboutDialog
from Exceptions import SharedPaintException
from threading import Timer
from time import strftime

class SharedPaintController:
    """
    SharedPaint controller (MVC).
    """

    def __init__(self, messagingInstance, modelInstance, viewInstance):
        """The constructor."""
        self.__drawing = False
        self.__warnOffline = True
        self.__synchronizing = False
        self.__messaging = messagingInstance
        self.__model = modelInstance
        self.__frame = viewInstance
        self.__returning = (-1, -1)

        # UI callbacks
        wx.EVT_LEFT_DOWN(self.__frame.doodle, self.__OnMouseDown)
        wx.EVT_MOTION(self.__frame.doodle, self.__OnMouseMove)
        wx.EVT_LEFT_UP(self.__frame.doodle, self.__OnMouseUp)
        self.__frame.Bind(wx.EVT_CLOSE, self.__OnCloseCommand)
        self.__frame.Bind(wx.EVT_MENU, self.__OnJoinCommand, id=101)
        self.__frame.Bind(wx.EVT_MENU, self.__OnSessionSnapshotCommand, id=102)
        self.__frame.Bind(wx.EVT_MENU, self.__OnSessionLoadCommand, id=103)
        self.__frame.Bind(wx.EVT_MENU, self.__OnCloseCommand, id=104)        
        self.__frame.Bind(wx.EVT_MENU, self.__OnImageLoadCommand, id=201)
        self.__frame.Bind(wx.EVT_MENU, self.__OnImageClearCommand, id=202)
        self.__frame.Bind(wx.EVT_MENU, self.__OnClearCommand, id=301)
        self.__frame.Bind(wx.EVT_MENU, self.__OnUndoCommand, id=302)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnSessionSnapshotCommand, id=102)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnSessionLoadCommand, id=103)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnImageLoadCommand, id=201)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnImageClearCommand, id=202)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnClearCommand, id=301)
        self.__frame.Bind(wx.EVT_TOOL, self.__OnAboutCommand, id=402)
        self.__frame.ctrlPanel.EVT_PEN_UPDATE(self.__OnPenUpdate)

        # Event channel callbacks
        self.__messaging.EVT_STATUS_REQUEST(self.__HandleStatusRequest)
        self.__messaging.EVT_STATUS_RESPONSE(self.__HandleStatusResponse)
        self.__messaging.EVT_JOINED(self.__HandleJoined)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_ANNOTATION", self.__HandleEVTAnnotation)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_DRAWING", self.__HandleEVTDrawing)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_IMAGE_LOAD", self.__HandleEVTImageLoad)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_IMAGE_CLEAR", self.__HandleEVTImageClear)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_CLEAR", self.__HandleEVTClear)        
        self.__messaging.EVT_EVENT_RECEIVED("EVT_PARTICIPANT_JOIN", self.__HandleEVTParticipantJoin)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_PARTICIPANT_LEAVE", self.__HandleEVTParticipantLeave)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_PARTICIPANT_UPDATE", self.__HandleEVTParticipantUpdate)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_SNAPSHOT_LOADED", self.__HandleEVTSnapshotLoaded)
        self.__messaging.EVT_EVENT_RECEIVED("EVT_UNDO", self.__HandleEVTUndo)

    def Run(self):
        """Shows the splash screen."""
        self.__messaging.Join()
        self.__splashScreen = WelcomeDialog(self.__frame)
        # On close, show the main form
        self.__splashScreen.Bind(wx.EVT_CLOSE, self.__ShowGUI)

    def __ShowGUI(self, evt):
        """Shows the main form."""
        self.__frame.Centre()
        self.__frame.Show(1)
        evt.Skip()

    def __AppendAnnotation(self, (x, y)):
        """Appends a new annotation to the model."""
        penColor = self.__model.PenColor
        penThickness = self.__model.PenThickness
        clientId = self.__messaging.GetClientId()        

        if self.__messaging.HasJoined():
            try:
                eventData = { "participantName" : self.__messaging.GetClientName(),
                       "participantID" : clientId,
                       "penColor" : penColor,
                       "penThickness" : penThickness }
                self.__messaging.SendEvent("EVT_ANNOTATION", eventData)
            except Exception, e:
                print e
                self.__frame.HandleNetworkProblems()
                return
        else:
            if self.__warnOffline:
                self.__frame.HandleDrawingOffline()
                self.__warnOffline = False

        ann = Annotation(self.__messaging.GetClientName(), clientId, (penColor, penThickness))
        self.__model.AppendAnnotation(ann)

    def __AppendDrawing(self, (x, y)):
        """Appends a new drawing to the current annotation."""
        clientId = self.__messaging.GetClientId()

        if self.__messaging.HasJoined():
            try:
                eventData = { "participantID" : clientId,
                       "x" : x,
                       "y" : y }
                self.__messaging.SendEvent("EVT_DRAWING", eventData)
            except Exception, e:
                print e
                self.__frame.HandleNetworkProblems()
                return
        else:
            if self.__warnOffline:
                self.__frame.HandleDrawingOffline()
                self.__warnOffline = False

        self.__model.AppendDrawing((x, y), clientId)

    def __ToWorkspaceCoordinates(self, (x, y)):
        """Transforms the given client coordinates into workspace coordinates."""
        return self.__frame.doodle.CalcUnscrolledPosition((x, y))

    def __ModelToString(self):
        """Transforms the model into its string representation."""
        strModel = self.__model.ImageFile + ";;;"
        for ann in self.__model.GetAnnotations():
            strAnn =  str(ann.ParticipantName) + ";;" + \
                str(ann.ParticipantId) + ";;" + \
                str(ann.PenSettings[0]) + "," + str(ann.PenSettings[1]) + ";;"
            for point in ann.Drawing:
                strAnn = strAnn + str(point[0]) + "." + str(point[1]) + ","
            strAnn = strAnn + ";;" + str(ann.Description)
            strModel = strModel + strAnn + ";;;"
        return strModel

    def __ModelFromString(self, strModel):
        """Transforms a given string into a list of annotations. This
        list is then used to populate the model (replacing the data)."""
        annotations = strModel.split(";;;")
        imageFile = annotations[0]

        if imageFile != "":
            try:
                tmpfile = self.__messaging.DownloadFile(imageFile)
            except MessagingException, e:
                wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
                return

            tmp = self.__model.ImageFile
            try:
                self.__model.ImageFile = imageFile
                self.__frame.doodle.SetBackground(tmpfile)
            except SharedPaintException, e:
                self.__model.ImageFile = tmp
                wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
                return
        else:
            self.__model.ImageFile = ""
            self.__frame.doodle.ClearBackground()

        self.__model.ClearAll()
        del annotations[0]
        for ann in annotations:
            if ann == "":
                break
            info = ann.split(";;")
            pen = info[2].split(",")
            new = Annotation(info[0], info[1], (pen[0], int(pen[1])))
            self.__model.AppendAnnotation(new)
            drawing = info[3].split(",")
            for point in drawing:
                if point == "":
                    break
                coord = point.split(".")
                self.__model.AppendDrawing((int(coord[0]), int(coord[1])), info[1])    

    def __OnMouseDown(self, evt):
        """Called when the left button has been pressed within the doodle window."""
        (x, y) = self.__ToWorkspaceCoordinates(evt.GetPositionTuple())
        (width, heigth) = self.__frame.doodle.GetVirtualSize()

        if x in range(width) and y in range(heigth):
            self.__drawing = True
            self.__frame.doodle.CaptureMouse()
            self.__AppendAnnotation((x, y))
            self.__AppendDrawing((x, y))

    def __OnMouseMove(self, evt):
        """Called when the mouse has been moved within the doodle window."""
        if not (evt.Dragging() and evt.LeftIsDown()):
            return

        (x, y) = self.__ToWorkspaceCoordinates(evt.GetPositionTuple())
        (width, heigth) = self.__frame.doodle.GetVirtualSize()

        if x in range(width) and y in range(heigth):
            if self.__drawing:
                self.__AppendDrawing((x, y))
            # Drawing went back to canvas
            elif self.__returning != (-1, -1):
                self.__drawing = True
                self.__AppendDrawing((-1, -1))
                self.__AppendDrawing(self.__returning)
                self.__AppendDrawing((x, y))
        else:
            # Drawing went out the canvas
            if self.__drawing:
                self.__drawing = False
                self.__AppendDrawing((x, y))
                self.__returning = (x, y)
            if self.__returning != (-1, -1):
                self.__returning = (x, y)

    def __OnMouseUp(self, evt):
        """Called when the left button has been released within the doodle window."""
        if self.__frame.doodle.HasCapture():
            self.__frame.doodle.ReleaseMouse()
        else:
            return

        (x, y) = self.__ToWorkspaceCoordinates(evt.GetPositionTuple())

        if self.__drawing:
            self.__AppendDrawing((x, y))
            self.__drawing = False

        self.__returning = (-1, -1)

    def __OnCloseCommand(self, evt):
        """Called when the main frame has been closed."""
        if self.__messaging.HasJoined():
            self.__messaging.Leave()
        self.__frame.Show(0)
        self.__frame.Destroy()
        evt.Skip()

    def __OnJoinCommand(self, evt):
        """Called when the 'Session->Join' menu item (or the equivalent
        toolbar icon) has been picked. The messaging service is started."""
        #TODO: Asynchronous exception can't be handled
        try:
            self.__messaging.Join()
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)

    def __OnClearCommand(self, evt):
        """Called when the 'Session->Clear' menu item (or the equivalent
        toolbar icon) has been picked. The model's data is cleared; this
        event is broadcasted through the messaging service."""
        if self.__messaging.HasJoined():
            self.__messaging.SendEvent("EVT_CLEAR", {})
        self.__model.ClearAll()

    def __OnUndoCommand(self, evt):
        """Called when the 'Session->Undo' menu item (or the equivalent
        toolbar icon) has been picked. The last annotation made by the user
        is undone; this event is broadcasted through the messaging service."""
        if self.__messaging.HasJoined():
            eventData = { "participantId" : self.__messaging.GetClientId() }
            self.__messaging.SendEvent("EVT_UNDO", eventData )
        self.__model.Undo(self.__messaging.GetClientId())

    def __OnImageLoadCommand(self, evt):
        """Called when the 'Image->Load new...' menu item (or the equivalent
        toolbar icon) has been picked. A dialog listing the available images
        in the AG server is shown.
        A dialog is shown listing the available images in the AG server."""
        wildcard = ["*.jpg", "*.JPG", "*.png", "*.PNG",
                    "*.gif", "*.GIF", "*.tif", "*.TIF"]
        try:
            files = self.__messaging.ListFiles(wildcard)
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
            return

        x = ItemPicker(self.__frame, "Available images", files)
        x.ShowDialog(True, self.__OnFileSelected)

    def __OnFileSelected(self, filename):
        """Called when the user has chosen a new background image.
        The image is retrieved from the AG server (given its filename)
        and the doodle window is refreshed with it. This event is
        broadcasted through the messaging service."""
        try:
            tmpfile = self.__messaging.DownloadFile(filename)
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
            return

        tmp = self.__model.ImageFile
        try:
            self.__model.ImageFile = filename
            self.__frame.doodle.SetBackground(tmpfile)
            self.__model.ClearAll()
        except SharedPaintException, e:
            self.__model.ImageFile = tmp
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
            return

        eventData = { "imageFile" : filename }
        self.__messaging.SendEvent("EVT_IMAGE_LOAD", eventData)

    def __OnImageClearCommand(self, evt):
        """Called when the 'Image->Clear' menu item (or the equivalent
        toolbar icon) has been picked. The current background image
        is removed; this event is broadcasted through the messaging service."""
        if not self.__messaging.HasJoined():
            return

        self.__model.ImageFile = ""
        self.__frame.doodle.ClearBackground()
        self.__model.ClearAll()
        self.__messaging.SendEvent("EVT_IMAGE_CLEAR", {})

    def __OnSessionSnapshotCommand(self, evt):
        """Called when the 'Take snapshot' toolbar icon has been picked.
        A snapshot of the current session status is taken and uploaded
        to the AG server. This event is broadcasted through the
        messaging service."""
        try:
            key = strftime("%Y-%m-%d %H:%M:%S")
            data = self.__ModelToString()
            self.__messaging.Save(key, data, "description")
            wx.MessageBox("Snapshot saved!", "Information", wx.ICON_INFORMATION)
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)

    def __OnSessionLoadCommand(self, evt):
        """Called when the 'Load snapshot' toolbar icon has been picked.
        A dialog listing all previously saved snapshots (available in the
        AG server) is shown."""
        try:
            snapshots = self.__messaging.GetAll()
            x = ItemPicker(self.__frame, "Saved snapshots", snapshots)
            x.ShowDialog(True, self.__OnSnapshotSelected)
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)

    def __OnSnapshotSelected(self, key):
        """Called when the user has chosen a snapshot to load.
        The snapshot is retrieved from the AG server (given its key) and
        the model is populated with it."""
        self.__ModelFromString(self.__messaging.Get(key))
        eventData = { "snapshotId" : key }
        self.__messaging.SendEvent("EVT_SNAPSHOT_LOADED", eventData)

    def __OnPenUpdate(self, **settings):
        """Called when a new pen setting has been picked."""
        if settings.has_key("color"):
            self.__model.PenColor = settings["color"]
            if self.__messaging.HasJoined():
                self.__messaging.SendClientStatus({ "penColor" : self.__model.PenColor })
        if settings.has_key("thickness"):
            self.__model.PenThickness = settings["thickness"]

    def __OnAboutCommand(self, evt):
        """Shows the about dialog."""
        AboutDialog(self.__frame)

    def __HandleJoined(self):
        """Called when the user has joined the SharedPaint session."""
        self.__frame.HandleJoined()

    def __HandleEVTAnnotation(self, eventData):
        """Called when a participant has created a new annotation.
        The annotation is added to the model."""
        ann = Annotation(eventData["participantName"],
                         eventData["participantID"],
                         (eventData["penColor"], eventData["penThickness"]))
        self.__model.AppendAnnotation(ann)

    def __HandleEVTDrawing(self, eventData):
        """Called when a participant has drawn a segment of an annotation.
        The segment is added to the model. (This event is generated at
        every mouse move)."""
        drawing = (eventData["x"], eventData["y"])
        self.__model.AppendDrawing(drawing, eventData["participantID"])

    def __HandleEVTClear(self, eventData):
        """Called when a participant has cleared his session.
        The model is cleared."""
        self.__model.ClearAll()

    def __HandleEVTUndo(self, eventData):
        """Called when a participant has undone his last annotation.
        This annotation is removed from the model as well."""
        self.__model.Undo(eventData["participantId"])

    def __HandleEVTImageLoad(self, eventData):
        """Called when a participant has loaded a new background image.
        The image is retrieved from the AG server (given its filename)
        and the doodle window is refreshed with it"""
        imageFile = eventData["imageFile"]
        try:
            tmpfile = self.__messaging.DownloadFile(imageFile)
        except MessagingException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)
            return

        self.__model.ClearAll()
        self.__model.ImageFile = imageFile
        try:
            self.__frame.doodle.SetBackground(tmpfile)
        except SharedPaintException, e:
            wx.MessageBox(str(e), "Error", wx.ICON_ERROR)

    def __HandleEVTImageClear(self, eventData):
        """Called when a participant has removed his background image.
        The local background image is removed as well."""
        self.__model.ImageFile = ""
        self.__frame.doodle.ClearBackground()
        self.__model.ClearAll()

    def __HandleEVTSnapshotLoaded(self, eventData):
        """Called when a participant has loaded a snapshot.
        This snapshot is retrieved from the AG server (given its key)
        and the model is populated with it."""
        key = eventData["snapshotId"]
        self.__ModelFromString(self.__messaging.Get(key))

    def __HandleEVTParticipantJoin(self, eventData):
        """Called when a participant has joined the session.
        This list of participants is updated."""
        self.__messaging.SendClientStatus({ "penColor" : self.__model.PenColor })
        p = SharedPaintParticipant()
        p.Name = eventData.Name
        p.Id = eventData.Id
        try:
            p.PenColor = eventData.Status["penColor"]
        except:
            p.PenColor = "#000000"

        self.__model.AddParticipant(p)
        self.__frame.AddParticipant(p)

    def __HandleEVTParticipantUpdate(self, eventData):
        """Called when a participant has updated his status (due to
        a change to his pen settings, for example). The participant's
        avatar is updated."""
        p = SharedPaintParticipant()
        p.Name = eventData.Name
        p.Id = eventData.Id
        p.PenColor = eventData.Status["penColor"]
        self.__model.UpdateParticipant(p)
        self.__frame.UpdateParticipant(p)

    def __HandleEVTParticipantLeave(self, eventData):
        """Called when a participant has left the session.
        This list of participants is updated."""
        self.__model.RemoveParticipant(eventData)
        self.__frame.RemoveParticipant(eventData)

    def __HandleStatusRequest(self):
        """Called when a participant has requested the user to provide
        the updated data from his model. A string representation of the
        model is returned (then broadcasted through the messaging service)."""
        return self.__ModelToString()

    def __HandleStatusResponse(self, appStatus):
        """Called when updated data from a participant's model has been
        received. The model is populated with it."""
        self.__ModelFromString(appStatus)