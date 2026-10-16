import threading, wx
import frontend.gui as gui
from auto_all import public
from utils import getenv, getenv_int

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
        window_width = getenv_int("GUI_WIDTH", 825)
        window_height = getenv_int("GUI_HEIGHT", 1300)
        self.wx_frame = wx.Frame(None, 
            title = "PhantomGamesBot",
            size = wx.Size(window_width, window_height),
            style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.CLOSE_BOX)
        )
        
        self.main_area = wx.FlexGridSizer(2)
        self.header_font = wx.Font(wx.FontInfo(14).Bold().Underlined())
        self.label_font = wx.Font(wx.FontInfo(12))

        if getenv("OBS_PATH"):
            self.obs_launch = gui.SubprocessLauncher_Dashboard(
                bot=self, 
                parent=self.wx_frame, 
                process_path=getenv("OBS_PATH"), 
                label="OBS")
            self.main_area.Add(self.obs_launch, 0, wx.SHAPED | wx.ALL, 2)

        if getenv("STREAMNINJA_PATH"):
            self.streamninja = gui.SubprocessLauncher_Dashboard(
                bot=self,
                parent=self.wx_frame,
                process_path=getenv("STREAMNINJA_PATH"),
                label="StreamNinja"
            )
            self.main_area.Add(self.streamninja, 0, wx.SHAPED | wx.ALL, 2)

        self.mmbn = gui.MMBN1_Dashboard(self, parent=self.wx_frame)
        self.main_area.Add(self.mmbn, 0, wx.SHAPED | wx.ALL, 2)

        self.wx_frame.SetSizer(self.main_area)

        self.wx_frame.Show()
        self.wx_app.MainLoop()

    def start(self):
        self.worker_thread.start()

@public
def run_GUI(eventLoop, sharedResources):
    guiBot = PhantomGamesBotGUI(sharedResources)
    guiBot.start()
