import os
import platform
import sys
from time import sleep

from ahk import AHK

from src.autotriage.error import AutoTriageError
from src.autotriage.request import Request


class MyAHK:

    def __init__(self, block_forever=False):
        hotkeys = (
            ('^+m', self.show_message),
            ('^+t', self.triage),
        )
        executable_path = os.path.join(
            getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(sys.executable))),
            "AutoHotkey.exe",
        ) if getattr(sys, 'frozen', False) else ''
        self.ahk = AHK(executable_path=executable_path, version='v2')
        self.ahk.set_send_mode('Event')
        for hotkey, callback in hotkeys: self.ahk.add_hotkey(hotkey, callback)
        self.ahk.start_hotkeys()  # start the hotkey process thread
        print('Created AHK instance')
        if block_forever:
            self.ahk.block_forever()

    def show_message(self):
        # Show a message box directly using AHK
        self.ahk.msg_box(f'Python version {platform.python_version()}\nAHK version {self.ahk.get_version()}')

    def triage(self):
        self.ahk.send('!c') # Close any AMR popup with Alt+C
        self.ahk.send('{F6}{Tab}') # Focus on the tree
        restore_clipboard = self.ahk.get_clipboard()
        self.ahk.set_clipboard('')
        self.ahk.send('^c') # copy to clipboard
        try:
            self.ahk.clip_wait(0.1)
            clipboard = self.ahk.get_clipboard()
        except TimeoutError: # maybe the focus was originally on the pdf viewer, try again
            self.ahk.send('{F6}{Tab}^c')
            try:
                self.ahk.clip_wait(0.1)
                clipboard = self.ahk.get_clipboard()
            except TimeoutError:
                self.ahk.show_traytip('Error', 'No request found')
                return
        finally:
            self.ahk.set_clipboard(restore_clipboard)
        self.ahk.send('{Tab}') # Tab to "Radiology Category"
        try:
            request = Request(clipboard)
        except AutoTriageError as e:
            self.ahk.show_traytip('Error', e.message)
        else:
            self.ahk.show_traytip('Success', f'{request.modality.name} - {request.exam}')

