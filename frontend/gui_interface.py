import threading, wx
import frontend.gui as gui

class PhantomGamesBotGUI:
    def __init__(self, sharedResources):
        self.sharedResources = sharedResources
        self.worker_thread = threading.Thread(target=self.run)

        self.wx_app = None
        self.wx_frame = None
        self.header_font = None
        self.label_font = None

    def run(self):
        self.wx_app = wx.App()
        self.wx_frame = wx.Frame(None, 
            title = "PhantomGamesBot",
            size = wx.Size(825,1300),
            style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.CLOSE_BOX)
        )
        self.header_font = wx.Font(wx.FontInfo(14).Bold().Underlined())
        self.label_font = wx.Font(wx.FontInfo(12))

        self.mmbn = gui.MMBN1_Dashboard(self, self.wx_frame)

        self.wx_frame.Show()
        self.wx_app.MainLoop()

    def start(self):
        self.worker_thread.start()

def run_GUI(eventLoop, sharedResources):
    guiBot = PhantomGamesBotGUI(sharedResources)
    guiBot.start()
