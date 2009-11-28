#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name   : SharedPaint.py
# Purpose: Main application file.
# Author : William A. Romero R.	<wil-rome@uniandes.edu.co>
#          Henry Caballero	<hh.caballero921@uniandes.edu.co>
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

__author__  = "William A. Romero R. <wil-rome@uniandes.edu.co>, Henry Caballero <hh.caballero921@uniandes.edu.co>"
__license__ = "GNU GPL"
__version__ = "3.0"
__revision__ = "$Id: SharedPaint.py,v 1.5 2009/05/06 13:26:33 agmoxdev Exp$"

import wx
import os
import sys
import agversion
agversion.select(3)

from Messaging import SharedAppMessaging
from Model import SharedPaintSession
from View import SharedPaintGUI
from Controller import SharedPaintController
from AccessGrid.Toolkit import WXGUIApplication
from optparse import Option
from twisted.internet import reactor # it should be already installed

try:
    pass
    #from twisted.internet import _threadedselect as threadedselectreactor
except:
    pass
    #from twisted.internet import threadedselectreactor
#threadedselectreactor.install()

class SharedPaintApp(wx.App):
    """Main class."""    

    def __init__(self, appURL, connectionID):
        """The constructor."""
        wx.App.__init__(self, False)
        reactor.interleave(wx.CallAfter)

        messaging = SharedAppMessaging("SharedPaint-3", appURL, connectionID)
        model = SharedPaintSession()
        frame = SharedPaintGUI(model)

        self.SetTopWindow(frame)

        controller = SharedPaintController(messaging, model, frame)
        controller.Run()

    def OnInit(self):
        """Called when the application is initialized."""
        return True

    def OnExit(self):
        """Called when the main loop stops."""
        print "Application was shutdown cleanly"
        os._exit(0)

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    """Method for running SharedPaint."""
    if len(sys.argv) < 2:
       print "Usage: SharedPaint.py --appURL=<url> --connectionID=<id>"
       os._exit(0)

    appURLOption = Option("-a", "--appURL", dest="appURL", type="string", default=None, help="Please provide an application URL in the command line") 
    connectionIDOption = Option("-i", "--connectionID", dest="connectionID", type="string", default=None, help="Please provide a connection ID in the command line")

    wx.InitAllImageHandlers()
    # Create the AG application
    app = WXGUIApplication()
    name = "SharedPaint 3.0"

    # Add command line options
    app.AddCmdLineOption(appURLOption)
    app.AddCmdLineOption(connectionIDOption)

    # Initialize the AG application
    app.Initialize(name)

    appURL = app.GetOption("appURL")
    connectionID = app.GetOption("connectionID")

    spApp = SharedPaintApp(appURL, connectionID)

    # Start the window application processing
    spApp.MainLoop()

    # Exit gracefully
    os._exit(0)
