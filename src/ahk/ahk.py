import os
import platform
import sys

from ahk import AHK


class MyAHK:

    def __init__(self, block_forever=False):
        executable_path = os.path.join(
            getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(sys.executable))),
            "AutoHotkey.exe",
        ) if getattr(sys, 'frozen', False) else ''
        self.ahk = AHK(executable_path=executable_path, version='v2')
        for hotkey, callback in (
            ('^+m', self.show_message),
        ): self.ahk.add_hotkey(hotkey, callback)
        self.ahk.start_hotkeys()  # start the hotkey process thread
        print('Created AHK instance')
        if block_forever:
            self.ahk.block_forever()

    def show_message(self):
        # Show a message box directly using AHK
        self.ahk.msg_box(f'Python version {platform.python_version()}\nAHK version {self.ahk.get_version()}')