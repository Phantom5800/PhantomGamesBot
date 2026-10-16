import wx

class OnOffIndicator(wx.Panel):
    def __init__(self, parent, radius=8):
        super().__init__(parent)
        self.radius = radius
        self.SetMinSize((self.radius*3, self.radius*3))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.is_enabled = False

    def set_state(self, enable):
        self.is_enabled = enable
        self.Refresh(eraseBackground=True)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if gc:
            if self.is_enabled:
                gc.SetBrush(wx.GREEN_BRUSH)
                gc.SetPen(wx.GREEN_PEN)
            else:
                gc.SetBrush(wx.RED_BRUSH)
                gc.SetPen(wx.RED_PEN)

            w,h = self.GetSize()
            gc.DrawEllipse(
                (w / 2) - self.radius,
                (h / 2) - self.radius,
                self.radius * 2,
                self.radius * 2
            )
