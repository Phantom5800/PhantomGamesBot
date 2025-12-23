import threading
import wx

header_font = None
label_font = None

class MMBN1_Dashboard(wx.Panel):
    def __init__(self, *args, **kw):
        super(MMBN1_Dashboard, self).__init__(*args, **kw)

        self.box = wx.StaticBox(self, label="Battle Network Dashboard", pos=wx.Point(10,10), size=wx.Size(300,60))
        self.box.SetFont(header_font)
        self.chipCountText = wx.StaticText(self.box, label="RNG Chips(12): 0", pos=wx.Point(10,30))
        self.chipCountText.SetFont(label_font)

        self.chipCount = 0
        self.Bind(event=wx.EVT_KEY_UP, handler=self.on_key_up)

    def on_key_up(self, event):
        #wx.LogMessage(event.KeyCode)
        if event.KeyCode == wx.WXK_CONTROL:
            self.chipCount = self.chipCount + 1
        elif event.KeyCode == wx.WXK_NUMPAD_SUBTRACT:
            self.chipCount = self.chipCount - 1
        elif event.KeyCode == 104 or event.KeyCode == 72:
            self.chipCount = 0
        self.chipCountText.SetLabel(f"RNG Chips(12): {self.chipCount}")

def runGUIThread():
    global header_font
    global label_font

    app = wx.App()
    frame = wx.Frame(None, 
        title = "PhantomGamesBot",
        size = wx.Size(825,1300),
        style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.CLOSE_BOX)
    )
    header_font = wx.Font(wx.FontInfo(14).Bold().Underlined())
    label_font = wx.Font(wx.FontInfo(12))

    mmbn = MMBN1_Dashboard(frame)

    frame.Show()
    app.MainLoop()

guiThread = threading.Thread(target=runGUIThread)

def run_GUI(eventLoop, sharedResources):
    #runGUIThread()
    guiThread.start()
