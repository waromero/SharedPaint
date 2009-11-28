#--------------------------------------------------------------------
# Name   : gui.py
# Purpose: GUI classes
# Author : William A. Romero R.
# ID     : $Id: gui.py,v 1.2 2007/03/27 16:59:59 accessgrid Exp $
#--------------------------------------------------------------------
import os
import wx
import wx.html
import datetime

import events
from doodle import DoodleWindow

from AccessGrid.SharedAppClient import SharedAppClient
from AccessGrid.Platform.Config import UserConfig
from AccessGrid.ClientProfile import ClientProfile


try:
    from twisted.internet import threadedselectreactor
    threadedselectreactor.install()
except:
    pass
from twisted.internet import reactor

## 
#
# \brief Frame with menu and events
# \author William A. Romero R. (wil-rome[at]uniandes.edu.co)
# \version 1.2
# \date March 2007
# 
class FrameExtended(wx.Frame):
    def __init__(self, parent, id, title, appUrl):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(800, 600))
        #wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(800, 600), wx.DEFAULT_FRAME_STYLE^(wx.RESIZE_BORDER | wx.MINIMIZE_BOX |wx.MAXIMIZE_BOX))
        #self.SetIcon(wx.Icon('ico/sharedpaint.ico', wx.BITMAP_TYPE_ICO))
        
        self.appUrl = appUrl

    # <AGtk code>        
        reactor.interleave(wx.CallAfter)
        
        # Create shared application client     
        self.sharedAppClient = SharedAppClient("SharedPaint")
        self.log = self.sharedAppClient.InitLogging()
        self.log.debug("GroupPaint.__init__: Started Group Paint")
        
         # Get client profile
        try:
            self.clientProfileFile = os.path.join(UserConfig.instance().GetConfigDir(), "profile")
            self.clientProfile = ClientProfile(self.clientProfileFile)
            
        except:
            self.log.info("SharedQuestionTool.__init__: Could not load client profile, set clientProfile = None")
            self.clientProfile = None
    
        # Join the application session
        self.sharedAppClient.Join(self.appUrl, self.clientProfile)
        self.publicId = self.sharedAppClient.GetPublicId()
        self.user = self.clientProfile.GetName()
        self.id = self.sharedAppClient.GetPublicId()
        
        # Register event callback               
        self.sharedAppClient.RegisterEventCallback(events.CONSOLE_EVENT, self.GetConsoleEventData)
        self.sharedAppClient.RegisterEventCallback(events.CLEAR_EVENT, self.GetClearEvent)
        #self.sharedAppClient.RegisterEventCallback(events.SET_BG_EVENT, self.GetSetBGEvent)                            
    # </AGtk code>    
        
        """
        Setting status bar
        """
        self.CreateStatusBar()
        
        workspace = wx.BoxSizer(wx.VERTICAL)
        imagePanel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
        """
        Painter
        """
        self.painter = DoodleWindow(imagePanel, -1, self.clientProfile, self.sharedAppClient)
        
        imageBox = wx.BoxSizer(wx.VERTICAL)
        imageBox.Add(self.painter, 1, wx.EXPAND | wx.ALL, 1)
        imagePanel.SetSizer(imageBox)
        """
        Console settings
        """        
        consolePanel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)       
        
        self.console = wx.TextCtrl(consolePanel, -1, style=wx.TE_MULTILINE)
        self.console.SetEditable(0)
        
        consoleBox = wx.BoxSizer(wx.VERTICAL)
        consoleBox.Add(self.console, 1, wx.EXPAND | wx.ALL, 1)
        consolePanel.SetSizer(consoleBox)        
        
        workspace.Add(imagePanel, 4, wx.EXPAND | wx.ALL, 1)
        workspace.Add(consolePanel, 1, wx.EXPAND | wx.ALL, 1)
        
        self.SetSizer(workspace)

    ## Makes the menu bar
    # @param self The object pointer    
    def MakeMenu(self):

        menu = wx.MenuBar()
        options = wx.Menu()
        """
        Adding menu item
        """
        options.Append(101, "&Open", "Open background image")
        options.AppendSeparator()
        options.Append(102, "Clear background", "Clear background image")
        options.Append(103, "Clear drawing", "Clear drawing area")
        options.AppendSeparator()
        options.Append(104, "Help/About", "Further information")
        options.AppendSeparator()
        close = wx.MenuItem(options, 105, "&Close\tCtrl+C", "Close application")
        """
        Adding an icon to the close menu option
        """
        #close.SetBitmap(wx.Image('./pixmaps/frame.gif', wx.BITMAP_TYPE_GIF).ConvertToBitmap())
        options.AppendItem(close)
        """
        Adding menu items
        """
        menu.Append(options, "Options")
        """
        Setting  menu bar
        """
        self.SetMenuBar(menu)
        
        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=101)
        self.Bind(wx.EVT_MENU, self.OnClearBackground, id=102)
        self.Bind(wx.EVT_MENU, self.OnClearDrawing, id=103)
        self.Bind(wx.EVT_MENU, self.OnHelp, id=104)
        self.Bind(wx.EVT_MENU, self.OnClose, id=105)
          
    ## Initialize the console object
    # @param self The object pointer         
    def LoadConsole(self):
        self.PrintStartMessage();

    ## Open an image file 
    # @param self The object pointer
    # @event event Menu event
    def OnOpenFile(self,event):
        dlg = wx.FileDialog(self, "Choose a image file", os.getcwd(), "", "*.jpg" , wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            self.SetStatusText("Image file: %s" % mypath)
            self.painter.SetBackground(path)
            self.ConsoleMessage("File " + mypath + " loaded on background")
            
        dlg.Destroy()
    
    ## Close the application
    # @param self The object pointer
    # @event event Menu event    
    def OnClose(self,event):
        dlg = wx.MessageDialog(self, "Are you sure you want to close SharedPaint?", "Confirm close" ,wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close()
        else:
            dlg.Destroy()
            
    ## Clear the background image
    # @param self The object pointer
    # @event event Menu event 
    def OnClearBackground(self, event):
        self.painter.SetBackground(None)
    # <AGtk event>        
        self.ConsoleMessage("Background image unloaded")
    # </AGtk event>        
        
    ## Clear the user drawing
    # @param self The object pointer
    # @event event Menu event 
    def OnClearDrawing(self,event):
        self.sharedAppClient.SendEvent(events.CLEAR_EVENT, "")

    
    ## Display help frame
    # @param self The object pointer
    # @event event Menu event 
    def OnHelp(self,event):
        helpFrame = HTMLFrame(self, -1, 'SharedPaint HELP')
        helpFrame.Centre()
        helpFrame.Show()
        
    ## Send a console message
    # @param self The object pointer
    # @param message The message
    def ConsoleMessage(self, _message):
        message = " " + self.user + " >> " + _message
        self.sharedAppClient.SendEvent(events.CONSOLE_EVENT, message)
 
    ## Print welcome message
    # @param self The object pointer
    def PrintStartMessage(self):
        startMessage = "*** AGTk - SharedPaint 1.2, Department of Systems and Computing Engineering, Universidad de los Andes ***" + "\n" + "See Help/About for further information" + "\n"
        self.console.WriteText(startMessage)

    ## Capture the console event
    # @param self The object pointer
    # @param event Event data
    def GetConsoleEventData(self, event):
        message = event.data
        dt = datetime.datetime.now()
        timestamp = "[" + dt.isoformat() + "]: " 
        line = timestamp + message
        self.console.WriteText("\n" + line)

    ## Capture the set background event
    # @param self The object pointer
    # @param event Event data 
    def GetSetBGEvent(self, event):
        pass

    ## Capture the clear drawing event
    # @param self The object pointer
    # @param event Event data 
    def GetClearEvent(self,event):
        self.painter.SetLinesData([])
        self.ConsoleMessage("Drawing area cleared")
    
## 
#
# \brief HTML Frame
# \author William A. Romero R. (wil-rome[at]uniandes.edu.co)
# \version 1.1
# \date March 2007
# 
class HTMLFrame(wx.Frame):
       def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(640, 480))
        htmlWindow = wx.html.HtmlWindow(self)
        
        htmlWindow.LoadFile("help.html")
        
        
        