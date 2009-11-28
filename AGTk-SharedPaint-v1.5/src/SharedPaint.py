#--------------------------------------------------------------------
# Name   : SharedPaint.py
# Purpose: Main application file 
# Author : William A. Romero R.
# ID     : $Id: SharedPaint.py,v 1.1 2007/05/22 16:52:16 accessgrid Exp $
#--------------------------------------------------------------------

try:
    import wxversion
    wxversion.select("2.6")
except:
    pass

import agversion
agversion.select(3)

import sys
import wx

from optparse import Option
from AccessGrid import icons
from AccessGrid.Toolkit import WXGUIApplication

from gui import FrameExtended

try:
    from twisted.internet import threadedselectreactor
    threadedselectreactor.install()
except:
    pass
## 
#
# \brief Access Grid Toolkit Application
# \author William A. Romero R.
# \version 1.1
# \date March 2007
# 
class AGTkApp(wx.App):
    def __init__(self, appurlOption, venueUrlOption, idOption):
        self.appurlOption = appurlOption
        self.venueUrlOption = venueUrlOption
        self.idOption = idOption
        wx.App.__init__(self, redirect=False)
           
    def OnInit(self):
        
        wx.InitAllImageHandlers()
        # Create the AG application
        app = WXGUIApplication()
        name = "SharedPaint"
        
        # Add command line options
        app.AddCmdLineOption(self.appurlOption)
        app.AddCmdLineOption(self.venueUrlOption)
        app.AddCmdLineOption(self.idOption)
        
        # Initialize the AG application
        app.Initialize(name)
        
         # Create the group panel
        appUrl = app.GetOption("appUrl")
        venueUrl = app.GetOption("venueUrl")
        connectionId = app.GetOption('id')
        
        frame = FrameExtended(None, -1, 'SharedPaint', appUrl, venueUrl, connectionId)
        frame.SetIcon(icons.getAGIconIcon())
        frame.MakeMenu()
        frame.LoadConsole()
        frame.Show()
        frame.Centre()
        self.frame = frame
        return True
        
    def OnExitApp(self, evt):
        self.frame.Close(True)

if __name__ == '__main__':
    
    if len(sys.argv) < 2:
       print "Please provide the application URL on the command line --appUrl=<url>"
       sys.exit()
       
    appurlOption = Option("-a", "--appUrl", dest="appUrl", default=None, help="Specify an application url on the command line") 
    venueUrlOption = Option("-v", "--venueURL", dest='venueUrl', default=None, help='Specify a Venue URL') 
    idOption = Option("-i", "--id", type='string', dest='id')
                          
    agktApp = AGTkApp(appurlOption, venueUrlOption, idOption)
    agktApp.MainLoop()
