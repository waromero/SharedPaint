#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : Model.py
# Purpose: Business model for SharedPaint.
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
__revision__ = "$Id: Model.py,v 1.1 2009/05/06 12:18:55 agmoxdev Exp$"

class Annotation:
    """An annotation is a drawing from a participant."""

    def __init__(self, participantName, participantId, penSettings):
        """The constructor."""
        ## Name of the participant who made the annotation
        self.ParticipantName = participantName
        ## Participant identifier
        self.ParticipantId = participantId
        ## The pen settings data: color & thickness
        self.PenSettings = penSettings
        ## List of points of the drawing
        self.Drawing = []
        ## Description associated with the annotation
        self.Description = "(Description)"

#-----------------------------------------------------------------------------

class SharedPaintSession:
    """Represents a collaborative drawing session."""  

    def __init__(self):
        """The constructor."""
        # The current pen color
        self.PenColor = "#000000"
        # The current pen thickness
        self.PenThickness = 1
        # Background image
        self.ImageFile = ""
        # List of participants
        self.__participants = []
        # The annotations made throughout the session
        self.__annotations = []
        # Annotations being drawn (not yet finished)
        self.__openAnnotations = {}
        # Observers callbacks
        self.__eventsCallbacks = {}
        self.__eventsCallbacks["EVT_LINE"] = []
        self.__eventsCallbacks["EVT_CLEAR"] = []
        self.__eventsCallbacks["EVT_ANNOTATION"] = []

    def EVT_LINE(self, eventCallback):
        """Registers a callback for handling a LINE event."""
        self.__eventsCallbacks["EVT_LINE"].append(eventCallback)

    def EVT_CLEAR(self, eventCallback):
        """Registers a callback for handling a CLEAR event"""
        self.__eventsCallbacks["EVT_CLEAR"].append(eventCallback)

    def EVT_ANNOTATION(self, eventCallback):
        """Registers a callback for handling an ANNOTATION event."""
        self.__eventsCallbacks["EVT_ANNOTATION"].append(eventCallback)    

    def GetAnnotations(self):
        """Returns the list of annotations."""
        return self.__annotations    

    def AppendAnnotation(self, annotation):
        """Appends a new annotation to the list."""
        self.__annotations.append(annotation)
        self.__openAnnotations[annotation.ParticipantId] = annotation
        for callback in self.__eventsCallbacks["EVT_ANNOTATION"]:
            callback(annotation)

    def AppendDrawing(self, drawing, participantId):
        """Appends a new drawing to an annotation."""
        ann = self.__openAnnotations[participantId]
        ann.Drawing.append(drawing)

        p2 = ann.Drawing[-1]
        if len(ann.Drawing) > 1:
            p1 = ann.Drawing[-2]
        else:
            p1 = ann.Drawing[0]

        for callback in self.__eventsCallbacks["EVT_LINE"]:
            callback((ann.PenSettings[0], ann.PenSettings[1]), p1, p2)

    def Clear(self, participantId):
        """Removes the annotations made by a given participant."""
        while True:
            done = True
            for i in range(len(self.__annotations)):
                if cmp(self.__annotations[i].ParticipantId, participantId) == 0:
                    del self.__annotations[i]
                    done = False
                    break
            if done:
                break

        # Notify observers
        for callback in self.__eventsCallbacks["EVT_CLEAR"]:
            callback()

    def ClearAll(self):
        """Removes all the annotations from the session."""
        self.__annotations = []
        self.__currentAnnotations = {}

        # Notify observers
        for callback in self.__eventsCallbacks["EVT_CLEAR"]:
            callback()

    def Undo(self, participantId):
        """Removes the last annotation made by a given participant."""
        last = -1
        for i in range(len(self.__annotations)):
            a = self.__annotations[i]
            if a.ParticipantId == participantId:
                last = i

        try:
            del self.__annotations[last]
            # Force refresh
            for callback in self.__eventsCallbacks["EVT_CLEAR"]:
                callback()
        except IndexError:
            # Nothing to undo
            pass

    def GetParticipants(self):
        """Returns the participant's list."""
        return self.__participants

    def AddParticipant(self, participant):
        """Adds a new participant to the list."""
        self.__participants.append(participant)

    def UpdateParticipant(self, participant):
        """Updates a participant's information."""
        for p in self.__participants:
            if p.Id == participant.Id:
                p.Name = participant.Name
                p.PenColor = participant.PenColor
                break

    def RemoveParticipant(self, participantID):
        """Removes a participant from the list (given its ID)."""
        for i in range(len(self.__participants)):
            p = self.__participants[i]
            if p.Id == participantID:
                del self.__participants[i]
                break

#-----------------------------------------------------------------------------

class SharedPaintParticipant:
    """Represents a participant of a SharedPaint session."""

    def __init__(self):
        """The constructor."""
        self.Name = ""
        self.Id = ""
        self.PenColor = ""

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    """Test."""
    sp = SharedPaintSession("participantName", "participantID")
    annotation = Annotation(sp.ParticipantName, sp.ParticipantId, (1,2))
    sp.AppendAnnotation(annotation)
    sp.AppendDrawing((1,2))
    print len(sp.GetAnnotations())
    print sp.GetAnnotations()