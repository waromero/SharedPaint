#--------------------------------------------------------------------
# Name   : gui.py
# Purpose: GUI classes
# Author : William A. Romero R.
# ID     : $Id: gui.py,v 1.5 2007/05/23 16:31:20 accessgrid Exp $
#--------------------------------------------------------------------
import wxversion
import os
import wx
import wx.html
import datetime
import tempfile 
import string 
import sys

from wxPython.wx import *

import events
from doodle import DoodleWindow

try:
    import wxversion
    wxversion.select("2.6")
except:
    pass

# AGTk imports 
import agversion
agversion.select(3)
from AccessGrid.Toolkit import WXGUIApplication 
from AccessGrid.SharedAppClient import SharedAppClient 
from AccessGrid.Platform.Config import UserConfig 
from AccessGrid.ClientProfile import ClientProfile 
from AccessGrid.UIUtilities import MessageDialog
from AccessGrid.DataStoreClient import GetVenueDataStore 

try:
    from twisted.internet import threadedselectreactor
    threadedselectreactor.install()
except:
    pass
from twisted.internet import reactor 

## 
#
# \brief Frame with menu and events
# \author William A. Romero R.
# \version 1.3
# \date March 2007
# 
        
class FrameExtended(wx.Frame):
    def __init__(self, parent, id, title, appUrl, venueUrl, connectionId):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(800, 600))
        #wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(800, 600), wx.DEFAULT_FRAME_STYLE^(wx.RESIZE_BORDER | wx.MINIMIZE_BOX |wx.MAXIMIZE_BOX))
        #self.SetIcon(wx.Icon('ico/sharedpaint.ico', wx.BITMAP_TYPE_ICO))
        
        self.appUrl = appUrl
        self.venueUrl = venueUrl
        self.connectionId = connectionId
        
        print self.appUrl, self.venueUrl, self.connectionId
        
        

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
        self.sharedAppClient.RegisterEventCallback(events.SET_BG_EVENT, self.GetSetBGEvent)
        self.sharedAppClient.RegisterEventCallback(events.OPENFILE_EVENT, self.OpenFileEvent)                            
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
        
        self.file_to_load = self.sharedAppClient.GetData('current_file')
        if self.file_to_load:
            self.LoadFile(self.file_to_load)

    ## makes the menu bar
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
        options.Append(106, "Download", "Download image from server")
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
        self.Bind(wx.EVT_MENU, self.OnDowloadFile, id=106)
     
    ## Shows a file list from server
    # @param self The object pointer
    def OnDowloadFile(self, event):
        browser = ServerFileBrowser(self, -1, "Select file", self.venueUrl, self.connectionId)
        browser.ShowModal()
        fname = browser.getSelectedFile()
        if fname != None: 
            if self.LoadFile(fname): 
                self.sharedAppClient.SendEvent(event.OPENFILE_EVENT, fname) 
                self.sharedAppClient.SetData('current_file', fname) 
 
    ## Open image event
    # @param self The object pointer
    def OpenFileEvent(self, event):
        id = event.GetSenderId()
        nameImage = event.data
        if cmp(self.id, id) != 0: 
            self.LoadFile(nameImage)
                
    ## Open a image file after downloading
    # @param self The object pointer
    # @param pathfile path                 
    def LoadFile(self, nameImage): 
        # Create a temp file 
        t = string.split(nameImage, '.') 
        ext = '' 
        if len(t) > 1: 
            ext = '.' + t[len(t)-1] 
         
        (fd, tname) = tempfile.mkstemp(suffix = ext) 
        os.close(fd) 
        try:
            dsc = GetVenueDataStore(self.venueUrl, self.connectionId)
            dsc.Download(nameImage, tname)
            self.painter.SetBackground(tname)            
            return True  
        except Exception, e:
            print "No se pudo localizar el VenueDataStore: "+e[0].__str__()
            return False 
         
    ## initialize the console object
    # @param self The object pointer         
    def LoadConsole(self):
        self.PrintStartMessage();

    ## Open a image file 
    # @param self The object pointer
    # @param event Menu event
    def OnOpenFile(self,event):
        dlg = wx.FileDialog(self, "Choose a image file", os.getcwd(), "", "*.jpg" , wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            self.SetStatusText("Image file: %s" % mypath)
            self.ConsoleMessage("File " + mypath + " loaded on background")
            
            if (self.UploadFile(path, mypath)):
                self.sharedAppClient.SendEvent(events.SET_BG_EVENT, mypath)
                self.sharedAppClient.SetData('current_file', mypath)
                self.painter.SetBackground(path)
            else:
                pass
        dlg.Destroy()
        
    ## Load an image file to server
    # @param self The object pointer
    # @param pathfile path 
    # @param filename file name
    def UploadFile(self, pathfile, filename):
        try:
            dsc = GetVenueDataStore(self.venueUrl, self.connectionId) 
            dsc.Upload(pathfile)
            return True
        except Exception, e:
            dsc.RemoveFile(filename)
            dsc.Upload(pathfile)
            return True
    
    ## Close the application
    # @param self The object pointer
    # @param event Menu event    
    def OnClose(self,event):
        dlg = wx.MessageDialog(self, "Are you sure you want to close SharedPaint?", "Confirm close" ,wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            dlg.Destroy()
            self.Close()
        else:
            dlg.Destroy()
            
    ## Clear the background image
    # @param self The object pointer
    # @param event Menu event 
    def OnClearBackground(self, event):
        self.painter.SetBackground(None)
    # <AGtk event>        
        self.ConsoleMessage("Background image unloaded")
    # </AGtk event>        
        
    ## Clear the user drawing
    # @param self The object pointer
    # @param event Menu event 
    def OnClearDrawing(self,event):
        self.sharedAppClient.SendEvent(events.CLEAR_EVENT, "")

    
    ## Display help frame
    # @param self The object pointer
    # @param event Menu event 
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
        startMessage = "*** AGTk - SharedPaint 1.5, Department of Systems and Computing Engineering, Universidad de los Andes ***" + "\n" + "See Help/About for further information" + "\n"
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
        
        senderId = event.GetSenderId()
        
        if cmp(self.id, senderId) != 0:
            
            nameImage = event.data
            # Create a temporary file 
            t = string.split(nameImage, '.') 
            ext = '' 
            if len(t) > 1: 
                ext = '.' + t[len(t)-1] 
             
            (fd, tname) = tempfile.mkstemp(suffix = ext) 
            os.close(fd) 
            try: 
                dsc = GetVenueDataStore(self.venueUrl, self.connectionId) 
                dsc.Download(nameImage, tname)
                self.painter.SetBackground(tname)
                return True 
            except Exception, e:
                print "No se pudo localizar el VenueDataStore: "+e[0].__str__()
                return False         
            pass

    ## Capture the clear drawing event
    # @param self The object pointer
    # @param event Event data 
    def GetClearEvent(self,event):
        self.painter.SetLinesData([])
        self.ConsoleMessage("Drawing area cleared")
      


wildcard = ["*.jpg", "*.JPG", "*.gif", "*.GIF"]

#\"Gif Files (*.GIF)|*.gif|"\
#           "All Files (*.*)|*.*"

## 
#
# \brief Dialog to load a image file from server
# \author Eddy Díaz
# \version 1.1
# \date August 2007
# 

wildcard = ["*.jpg", "*.JPG"]

class ServerFileBrowser(wxDialog): 
    def __init__(self, parent, id, title, venueUrl, connectionId): 
        wxDialog.__init__(self, parent, id, title) 
       
        sizer = wxBoxSizer(wxVERTICAL)
 
        self.remote_files = wxListBox(self,-1) 
 
        bpanel = wxPanel(self, -1) 
        bsizer = wxBoxSizer(wxHORIZONTAL) 
 
        okbutton = wxButton(bpanel, wxNewId(), 'Ok') 
        cancelbutton = wxButton(bpanel, wxNewId(), 'Cancel') 
 
        bsizer.Add(okbutton, 1, wxEXPAND | wxALL, 5) 
        bsizer.Add(cancelbutton, 1, wxEXPAND | wxALL, 5) 
 
        bpanel.SetSizer(bsizer) 
        bsizer.SetSizeHints(bpanel) 
 
        sizer.Add(self.remote_files, 1, wxEXPAND | wxALL, 5) 
        sizer.Add(bpanel, 0, wxEXPAND | wxALL, 5) 
 
        self.SetSizer(sizer) 
        sizer.SetSizeHints(self) 
 
        self.selected_file = None 
 
        self.populateList(venueUrl, connectionId) 
 
        EVT_BUTTON(self, okbutton.GetId(), self.OnOk) 
        EVT_BUTTON(self, cancelbutton.GetId(), self.OnCancel) 

    ## OK action, open a image file
    # @param self The object pointer
    # @param event Menu event
    def OnOk(self, event): 
        self.selected_file = self.remote_files.GetStringSelection() 
        self.Close( True ) 
 
    ## CANCEL action
    # @param self The object pointer
    # @param event Menu event 
    def OnCancel(self, event): 
        self.Close( True )
        
    ## Shows a file list from server
    # @param self The object pointer
    # @param venueUrl venue URL
    # @param connectionId connection ID
    def populateList(self, venueUrl, connectionId): 
        self.remote_files.Clear() 
        dsc = GetVenueDataStore(venueUrl, connectionId) 
        files = dsc.QueryMatchingFilesMultiple(wildcard) 
        self.remote_files.InsertItems(files, 0) 

    ## Get the selected file
    # @param self The object pointer  
    def getSelectedFile(self): 
        if sys.platform == 'darwin': 
            return self.selected_file.__str__() 
        else: 
            return self.selected_file 


## 
#
# \brief HTML Frame
# \author William A. Romero R.
# \version 1.1
# \date March 2007
# 
class HTMLFrame(wx.Frame):
       def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(640, 480))
        htmlWindow = wx.html.HtmlWindow(self)
        
        htmlWindow.LoadFile("help.html")
        
        
        