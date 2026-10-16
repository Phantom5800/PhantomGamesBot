import errno, os, subprocess, threading, wx
from .toggle_indicator import OnOffIndicator

class SubprocessLauncher_Dashboard(wx.Panel):
    def __init__(self, *args,
                 bot, 
                 parent,
                 process_path: str, 
                 label: str,
                 **kw):
        super().__init__(
            parent=parent, 
            name=label, 
            *args, 
            **kw)
        if not os.path.exists(process_path):
            raise FileNotFoundError(errno.ENOENT, f"Could not find {process_path}")
        self.process_path = process_path
        self.process_thread = threading.Thread(target=self.run_process)
        
        self.dynamic_box = wx.BoxSizer(wx.HORIZONTAL)
        
        self.button = wx.Button(self, label = f"Launch - {label}", size=wx.Size(300,24))
        self.button.EventHandler.Bind(event=wx.EVT_BUTTON, handler=self.on_launch_button)
        self.dynamic_box.Add(self.button, 0, wx.ALL, 5)

        self.indicator = OnOffIndicator(self)
        self.dynamic_box.Add(self.indicator, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        self.SetSizerAndFit(self.dynamic_box)

    def run_process(self):
        self.indicator.set_state(True)
        subprocess.run(self.process_path, cwd=os.path.dirname(self.process_path))
        self.indicator.set_state(False)

    def on_launch_button(self, event):
        if not self.process_thread.is_alive():
            self.process_thread = threading.Thread(target=self.run_process)
            self.process_thread.start()
