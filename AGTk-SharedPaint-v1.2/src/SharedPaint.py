#--------------------------------------------------------------------
# Name   : SharedPaint.py
# Purpose: Main application file 
# Author : William A. Romero R.
# ID     : $Id: SharedPaint.py,v 1.1 2007/03/27 16:03:07 accessgrid Exp $
#--------------------------------------------------------------------

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
# \brief <strong>SharedPaint</strong> is an AGTk shared application. With this shared application we try to provide a basic example to developh applications on AGTk. 
# \author William A. Romero R. wil-rome[at].uniandes.edu.co
# \author Eddy D&iacute;az edd-diaz[at]uniandes.edu.co 
# \version 1.1
# \date March 2007
# 
class AGTkApp(wx.App):
    def __init__(self, appurlOption):
        self.appurlOption = appurlOption
        wx.App.__init__(self, redirect=False)
        
        self.appUrl = appurlOption
        
    def OnInit(self):
        
        wx.InitAllImageHandlers()
        # Create the AG application
        app = WXGUIApplication()
        name = "SharedPaint"
        
        # Add command line options
        app.AddCmdLineOption(self.appurlOption)
        
        # Initialize the AG application
        app.Initialize(name)
        
         # Create the group panel
        appUrl = app.GetOption("appUrl")
        
        frame = FrameExtended(None, -1, 'SharedPaint', appUrl)
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
                          
    agktApp = AGTkApp(appurlOption)
    agktApp.MainLoop()