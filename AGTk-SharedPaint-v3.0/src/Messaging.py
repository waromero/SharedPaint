#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : Messaging.py
# Purpose: Abstraction of the messaging tasks in an AGTk Shared Application
# Author : Henry Caballero 	<hh.caballero921@uniandes.edu.co>
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

__author__  = "Henry Caballero <hh.caballero921@uniandes.edu.co>"
__license__ = "GNU GPL"
__version__ = "3.0"
__revision__ = "$Id: Messaging.py,v 1.1 2009/05/06 06:42:09 agmoxdev Exp$"

import sys
import os
import tempfile
import string

from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile
from AccessGrid.DataStoreClient import GetVenueDataStore
from AccessGrid.DataStoreClient import FileNotFound

from threading import Timer
from AccessGrid.GUID import GUID

class MessagingException(Exception):
    """Thrown when an error occurs while communicating with the AG server."""
    pass

# Time in seconds between heartbeats
heartbeatInterval = 10

class SharedAppMessaging:
    """ Provides an abstraction of the messaging tasks in an AGTk Shared Application."""

    def __init__(self, appName, appURL, connectionID):
        """The constructor."""
        self.__appName = appName
        self.__appURL = appURL
        self.__venueURL = ""
        self.__connectionID = connectionID
        self.__statusRequestHandler = None
        self.__statusResponseHandler = None
        self.__heartbeatCount = 0
        self.__heartbeatTimer = None
        self.__purgueTimer = None
        # Status: 0=Offline, 1=Attempting to connect, 2=Connected
        self.__status = 0
        # List containing known participants' IDs
        self.__participants = []
        # Temporary list containing incoming hellos' IDs
        self.__participantsTmp = []
        # Observers callbacks
        self.__eventsCallbacks = {}
        self.__eventsCallbacks["EVT_JOINED"] = []
        self.__eventsCallbacks["EVT_PARTICIPANT_JOIN"] = []
        self.__eventsCallbacks["EVT_PARTICIPANT_LEAVE"] = []
        self.__eventsCallbacks["EVT_PARTICIPANT_UPDATE"] = []
        # Used for holding the registration of callbacks
        # (until the messaging service has been successfully started)
        self.__callbacksQueue = []

        self.__statusRequests = {}

        self.EVT_EVENT_RECEIVED("EVT_PARTICIPANT_HELLO", self.__HandleHeartbeat)
        self.EVT_EVENT_RECEIVED("EVT_PARTICIPANT_BYE", self.__HandleBye)
        self.EVT_EVENT_RECEIVED("EVT_APPSTATUS_REQUEST", self.__HandleStatusRequest)
        self.EVT_EVENT_RECEIVED("EVT_APPSTATUS_RESPONSE", self.__HandleStatusResponse)

        self.__tmpdir = UserConfig.instance().GetTempDir()
        self.__sharedAppClient = SharedAppClient(self.__appName)
        self.__log = self.__sharedAppClient.InitLogging(1)
        self.__clientProfile = None

        # Get client profile
        try:
            clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(), "profile")
            self.__clientProfile = ClientProfile(clientProfileFile)

            # For testing purposes:
            #self.__clientProfile = ClientProfile()
            #self.__randomName = str(GUID())
        except:
            raise MessagingException, "Could not load client profile."

    def EVT_JOINED(self, eventCallback):
        """Registers a callback for handling the EVT_JOINED event."""
        if self.__status != 0:
            raise Exception, "Callback must be registered before joining."
        self.__eventsCallbacks["EVT_JOINED"].append(eventCallback)

    def EVT_EVENT_RECEIVED(self, eventName, eventCallback):
        """Registers a callback for handling incoming messages from the
        event channel."""
        try:
            self.__eventsCallbacks[eventName].append(eventCallback)
        except KeyError:
            self.__eventsCallbacks[eventName] = [eventCallback]

        if self.HasJoined():
            self.__sharedAppClient.RegisterEventCallback(eventName, self.__HandleEventChannelMessage)
        else:
            self.__callbacksQueue.append(eventName)

    def EVT_PARTICIPANT_JOIN(self, eventCallback):
        """Registers a callback for handling the arrival of new
        participants to the shared application session."""
        self.__eventsCallbacks["EVT_PARTICIPANT_JOIN"].append(eventCallback)

    def EVT_PARTICIPANT_LEAVE(self, eventCallback):
        """Registers a callback for handling leaving participants
        from the shared application session."""
        self.__eventsCallbacks["EVT_PARTICIPANT_LEAVE"].append(eventCallback)

    def EVT_PARTICIPANT_UPDATE(self, eventCallback):
        """Registers a callback for handling status updates from
        a participant."""
        self.__eventsCallbacks["EVT_PARTICIPANT_UPDATE"].append(eventCallback)

    def EVT_STATUS_REQUEST(self, eventCallback):
        """Registers a (unique) callback for handling status requests.
        The provided callback must return a string representation of
        the shared application's model."""
        self.__statusRequestHandler = eventCallback

    def EVT_STATUS_RESPONSE(self, eventCallback):
        """Registers a (unique) callback for handling status responses.
        The received status is passed to the callback so it can
        synchronize the shared application's model wit it."""
        self.__statusResponseHandler = eventCallback

    def GetClientName(self):
        """Returns the client's profile name."""
        # For testing purposes:
        #return self.__randomName

        return self.__clientProfile.GetName()

    def GetClientId(self):
        """Returns the client's profile ID."""
        return self.__clientProfile.GetPublicId()

    def GetSessionId(self):
        """Returns the public ID used during the event channel
        session."""
        return self.__sharedAppClient.GetPublicId()

    def HasJoined(self):
        """Indicates whether the client has joined the shared application
        session."""
        return self.__status == 2;

    def Join(self):
        """Joins the client to the AG event service."""
        # It's called asynchronously to avoid UI blocking
        Timer(0, self.__Join).start()

    def __Join(self):
        """The actual Join procedure. It's run in a separate thread."""
        #TODO: Asynchronous exception can't be handled
        if self.__status == 1:
            raise MessagingException, "An attempt to join the session is currently active."

        if self.__status == 2:
            raise MessagingException, "Client has already joined the session."

        self.__log.info("Attempting to connect to event service. " +
                        "(appURL = " + str(self.__appURL) + ", connectionID = " + str(self.__connectionID))

        try:
            self.__sharedAppClient.Join(self.__appURL, self.__clientProfile)
        except Exception, e:
            self.__log.error(str(e))
            self.__status = 0
            return

        self.__status = 1
        self.__sharedAppClient.eventClient.RegisterMadeConnectionCallback(self.__HandleJoined)
        self.__venueURL = self.__sharedAppClient.GetVenueURL()
        self.__dataStoreClient = GetVenueDataStore(self.__venueURL, self.__connectionID)

    def Leave(self):
        """Shuts down the messaging service."""
        if self.__status != 2:
            return
        self.__Bye()
        self.__status = 0
        self.__log.info("Shutting down event service client.")
        self.__heartbeatTimer.cancel()
        self.__sharedAppClient.Shutdown()

    def SendEvent(self, eventName, eventData):
        """Sends the given data to the event channel."""
        if not isinstance(eventData, dict):
            raise Exception, "Invalid data type: dictionary expected."

        self.__AssertClientHasJoined()

        self.__sharedAppClient.SendEvent(eventName, repr(eventData))

    def SendClientStatus(self, clientStatus):
        """Sends a message containing updated client/model status."""
        if not isinstance(clientStatus, dict):
            raise Exception, "Invalid event data type: dictionary expected."

        eventData = { "participantName" : self.GetClientName(),
                     "participantID" : self.GetClientId(),
                     "clientStatus" : clientStatus }

        self.SendEvent("EVT_PARTICIPANT_HELLO", eventData)

    def GetVenueURL(self):
        """Returns the URL of the venue where the client currently belongs to."""
        return self.__venueURL;

    def GetConnectionId(self):
        """Returns the connectionID (supplied by the AG server)."""
        return self.__connectionID

    def ListFiles(self, wildcard):
    	"""Returns a list containing the names of the files that match the given
    	wildcard."""
        self.__AssertClientHasJoined()

        dsc = GetVenueDataStore(self.__venueURL, self.__connectionID)
        try:
            return dsc.QueryMatchingFilesMultiple(wildcard)
        except:
            raise MessagingException, "Couldn't list files from AG server"

    def DownloadFile(self, filename):
    	"""Retrieves a file from the AG server, given its name. 
    	Returns the file's full path (according to the local file system)."""
        self.__AssertClientHasJoined()

        t = string.split(filename, ".") 
        ext = ""
        if len(t) > 1:
            ext = "." + t[len(t)-1]
        (fd, tname) = tempfile.mkstemp(suffix = ext) 
        os.close(fd)
        dsc = GetVenueDataStore(self.__venueURL, self.__connectionID)
        try:
            dsc.Download(filename, tname)
        except:
            raise MessagingException, "Couldn't obtain file from AG server"
        return tname

    def Save(self, key, data, description):
        """Saves the given data into the session's data service."""
        self.__AssertClientHasJoined()

        self.__sharedAppClient.SetData(key, data)

    def Get(self, key):
    	"""Returns the data identified by the given key from the session's
    	data service."""
        self.__AssertClientHasJoined()

        return self.__sharedAppClient.GetData(key)

    def GetAll(self):
        """Returns the whole session's data service."""
        self.__AssertClientHasJoined()

        return self.__sharedAppClient.GetDataKeys()

    def Delete(self, key):
        """Removes the data identified by the given key from the 
        session's data service."""
        self.__AssertClientHasJoined()

    def __AssertClientHasJoined(self):
        """Checks whether the client has already joined the session."""
        if self.__status != 2:
            raise MessagingException, "Client has not joined the session."

    def __HandleJoined(self):
        """Called when the connection to the event service succeeds."""
        self.__status = 2
        self.__venueURL = self.__sharedAppClient.GetVenueURL() 

        self.__log.info("Connection to event service succeeded.")

        # Notify observers
        for callback in self.__eventsCallbacks["EVT_JOINED"]:
            callback()

        # Register held callbacks
        for c in self.__callbacksQueue:
            self.__sharedAppClient.RegisterEventCallback(c, self.__HandleEventChannelMessage)

        # Announce the client has just joined
        self.__Heartbeat()

        participants = self.__sharedAppClient.GetParticipants()
        ids = []
        for p in participants:
            id = p.clientProfile.GetPublicId()
            if id not in ids and id != self.GetClientId():
                ids.append(id)

        if len(ids) > 0:
            ids = ";".join(ids)
            eventData = { "participantID" : self.GetClientId(),
                         "suggestedOrder" : ids }
            self.SendEvent("EVT_APPSTATUS_REQUEST", eventData)
            self.__log.info("Status request sent.")

    def __Heartbeat(self):
        """Sends a message indicating that the client has joined
        the session."""
        if self.__heartbeatTimer is not None:
            self.__heartbeatTimer.cancel()

        self.__heartbeatCount += 1;

        eventData = { "participantName" : self.GetClientName(),
                     "participantID" : self.GetClientId() }

        self.SendEvent("EVT_PARTICIPANT_HELLO", eventData)

        self.__heartbeatTimer = Timer(heartbeatInterval, self.__Heartbeat)
        if self.__heartbeatCount == 2:
            self.__heartbeatCount = 0
            self.__PurgueParticipants()

    def __Bye(self):
        """Sends a message indicating that the client has left
        the session."""
        eventData = { "participantID" : self.GetClientId() }
        self.SendEvent("EVT_PARTICIPANT_BYE", eventData)

    def __HandleHeartbeat(self, eventData):
        """Called when an incoming 'heartbeat' message has been received."""
        p = SharedAppParticipant()
        p.Name = eventData["participantName"]
        p.Id = eventData["participantID"]
        try:
            p.Status = eventData["clientStatus"]
        except:
            pass

        # Already in list?
        if p.Id in self.__participants:
            if p.Status is not None:
                self.__NotifyParticipantUpdate(p)
        else:
            self.__participants.append(p.Id)
            self.__NotifyParticipantJoin(p)

        self.__participantsTmp.append(p.Id)

    def __HandleBye(self, eventData):
        """Called when a 'bye' message has been received."""
        id = eventData["participantID"]
        self.__participants.remove(id)
        self.__NotifyParticipantLeave(id)
 
    def __HandleStatusRequest(self, eventData):
        """Called when a participant has requested the client to
        provide the updated data from his model. Used primarily
        for synchronization."""
        if self.__statusRequestHandler is None:
            return

        destination = eventData["participantID"]
        try:
            ids = eventData["suggestedOrder"].split(";")
            order = 0
            for i in range(len(ids)):
                if ids[i] == self.GetClientId():
                    break
                if ids[i] in self.__participants:
                    order = order + 1

            if order == 0:
                self.__SendAppStatus(destination, None)
                self.__log.info("Status response sent")
            else:
                predecessor = ids[order - 1]
                t = Timer(2 * order, self.__SendAppStatus, [destination, predecessor])
                self.__statusRequests[destination] = t
                self.__statusRequests[predecessor] = t
                t.start()
        except Exception, e:
            self.__log.warn("Error while sending status response. " + str(e))

    def __HandleStatusResponse(self, eventData):
        """Called when updated data from a participant's model has
        been received."""
        if self.__statusResponseHandler is None:
            return

        destination = eventData["destination"]
        if (destination == self.GetClientId()):
            self.__statusResponseHandler(eventData["appStatus"])
            self.__log.info("Local model has been updated.")
        else:
            try:
                t = self.__statusRequests[destination]
                predecessor = t.args[1]
                t.cancel()
                del self.__statusRequests[destination]
                del self.__statusRequests[predecessor]
            except:
                pass

    def __PurgueParticipants(self):
        """Detects which participants have left the session."""
        if self.__purgueTimer is not None:
            self.__purgueTimer.cancel()

        gone = []
        for p in self.__participants:
            if p not in self.__participantsTmp:
                gone.append(p)

        for id in gone:
            self.__participants.remove(id)
            self.__NotifyParticipantLeave(id)

        # Clear temporary list
        self.__participantsTmp = []

    def __SendAppStatus(self, destination, predecessor):
        """Sends a message containing the application current status."""
        eventData = { "participantID" : self.GetClientId(),
                     "destination" : destination,
                     "appStatus" : self.__statusRequestHandler() }
        self.SendEvent("EVT_APPSTATUS_RESPONSE", eventData)

        try:
            del self.__statusRequests[destination]
            del self.__statusRequests[predecessor]
        except:
            pass

    def __NotifyParticipantJoin(self, participant):
        """Called when a new participant has joined the session.
        Observers are notified about it."""
        for callback in self.__eventsCallbacks["EVT_PARTICIPANT_JOIN"]:
            callback(participant)

    def __NotifyParticipantUpdate(self, participant):
        """Called when a participant update message has been received.
        Observers are notified about it."""
        for callback in self.__eventsCallbacks["EVT_PARTICIPANT_UPDATE"]:
            callback(participant)

    def __NotifyParticipantLeave(self, id):
        """Called when a participant has left the session.
        Observers are notified about it."""
        for callback in self.__eventsCallbacks["EVT_PARTICIPANT_LEAVE"]:
            callback(id)

        # Check whether the client must respond a pending status request
        try:
            t = self.__statusRequests[id]
            t.cancel()
            destination = t.args[0]
            predecessor = t.args[1]
            if (destination != id):
                t.function(t.args)
            else:
                del self.__statusRequests[destination]
                del self.__statusRequests[predecessor]
        except:
            pass

    def __HandleEventChannelMessage(self, event):
        """Called when an event channel message is received."""
        eventName = event.GetEventType()

        if cmp(self.GetSessionId(), event.GetSenderId()) == 0:
            if not eventName in ["EVT_PARTICIPANT_HELLO", "EVT_PARTICIPANT_BYE"]:
                return

        try:
            eventData = eval(event.data)
            if not isinstance(eventData, dict):
                self.__log.warn("Malformed event data. Ignoring.")
                return
            for callback in self.__eventsCallbacks[eventName]:
                callback(eventData)
        except KeyError:
            self.__log.warn("No handler registered for event: " + eventName + ".")

#-----------------------------------------------------------------------------

class SharedAppParticipant:
    """Represents a participant in a shared application."""

    def __init__(self):
        """The constructor."""
        self.Name = ""
        self.Id = ""
        self.Status = None