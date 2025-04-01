import os
import sys
from ahk import AHK

def get_bundle_dir():
    """Get the directory where the bundled files are stored."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def show_message():
    # Set the path to the bundled AHK executable if running as a compiled executable
    if getattr(sys, 'frozen', False):
        bundle_dir = get_bundle_dir()
        ahk_exe_path = os.path.join(bundle_dir, "AutoHotkey.exe")
        if os.path.exists(ahk_exe_path):
            os.environ["AHK_PATH"] = ahk_exe_path
    
    # Initialize AHK
    ahk = AHK(version="v2")
    
    # Show a message box directly using AHK
    ahk.msg_box('This is a test')

if __name__ == "__main__":
    show_message() 