import os
import platform
import sys

from ahk import AHK
from src.gui import main as gui_main


def show_message():
    # Show a message box directly using AHK
    ahk.msg_box(f'Python version {platform.python_version()}\nAHK version {ahk.get_version()}')

if __name__ == "__main__":
    # Set the path to the bundled AHK executable if running as a compiled executable
    if getattr(sys, 'frozen', False):
        ahk = AHK(
            executable_path=os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(sys.executable))),
                                         "AutoHotkey.exe"))
    else:
        ahk = AHK(version="v2")
    ahk.add_hotkey('^+m', callback=show_message)
    ahk.start_hotkeys()  # start the hotkey process thread
    gui_main()