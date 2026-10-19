import wx

DASHBOARD_SIZE=wx.Size(300,60)

class MMBN1_Dashboard(wx.Panel):
    def __init__(self, bot, parent):
        super().__init__(parent=parent, size=DASHBOARD_SIZE)

        self.box = wx.StaticBox(self, label="Battle Network Dashboard", size=DASHBOARD_SIZE)
        self.box.SetFont(bot.header_font)

        self.chipCountText = wx.StaticText(self.box, label="RNG Chips(12): 0", pos=wx.Point(10,30))
        self.chipCountText.SetFont(bot.label_font)

        self.chipCount = 0
        self.Bind(event=wx.EVT_KEY_UP, handler=self.on_key_up)
        self.Bind(event=wx.EVT_SET_FOCUS, handler=self.on_focus_gain)
        self.Bind(event=wx.EVT_KILL_FOCUS, handler=self.on_focus_lost)

    def on_focus_gain(self, event):
        self.box.SetBackgroundColour(wx.Colour(190,240,240))
        self.Refresh()

    def on_focus_lost(self, event):
        self.box.SetBackgroundColour(wx.Colour(240,240,240))
        self.Refresh()

    def on_key_up(self, event):
        if event.KeyCode == wx.WXK_NUMPAD1:
            self.chipCount = self.chipCount + 1
        elif event.KeyCode == wx.WXK_NUMPAD2:
            self.chipCount = self.chipCount - 1
        elif event.KeyCode == wx.WXK_NUMPAD7:
            self.chipCount = 0
        self.chipCountText.SetLabel(f"RNG Chips(12): {self.chipCount}")
