import os
import sys
from ahk import AHK


def show_message():
    # Set the path to the bundled AHK executable if running as a compiled executable
    if getattr(sys, 'frozen', False):
        ahk = AHK(executable_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(sys.executable))), "AutoHotkey.exe"))
    
    else:
        ahk = AHK(version="v2")
        
    # Show a message box directly using AHK
    ahk.msg_box('This is a test')

if __name__ == "__main__":
    show_message() 