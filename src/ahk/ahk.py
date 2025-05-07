import os
import platform
import sys
import re

from ahk import AHK
from ahk.directives import NoTrayIcon

from src.autotriage.select_examination_gui import SelectExaminationGUI
from ..autotriage import AutoTriageError, Priority, BodyPart, request_from_clipboard, Examination, Request
from ..database import Database, ExaminationNotFoundError

class MyAHK:

    DEFAULT_RANK = 3 # todo make this configurable, None if setting rank is disabled
    COMRAD_WINDOW = 'COMRAD Medical Systems Ltd. ahk_class SunAwtFrame'
    database = Database()
    def __init__(self, block_forever=False):
        executable_path = os.path.join(
            getattr(sys, "_MEIPASS", os.path.dirname(os.path.realpath(sys.executable))),
            "AutoHotkey.exe",
        ) if getattr(sys, 'frozen', False) else ''
        self.ahk = AHK(executable_path=executable_path, version='v2', directives=[NoTrayIcon])
        self.ahk.set_send_mode('Event')
        self.ahk.set_title_match_mode(1)
        self.ahk.add_hotkey('^+m', self.show_message)
        self.ahk.add_hotkey('Numpad0', self.triage, self.autotriage_error_handler)  # skips rank entry
        self.ahk.add_hotkey('Numpad1', lambda: self.triage(1), self.autotriage_error_handler)
        self.ahk.add_hotkey('Numpad2', lambda: self.triage(2), self.autotriage_error_handler)
        self.ahk.add_hotkey('Numpad3', lambda: self.triage(3), self.autotriage_error_handler)
        self.ahk.add_hotkey('Numpad4', lambda: self.triage(4), self.autotriage_error_handler)
        self.ahk.add_hotkey('Numpad5', lambda: self.triage(5), self.autotriage_error_handler)
        self.ahk.add_hotkey('~MButton', lambda: self.triage(self.DEFAULT_RANK), self.autotriage_error_handler)
        self.ahk.add_hotkey('~RButton', self.complete_triage)
        self.ahk.start_hotkeys()  # start the hotkey process thread
        if block_forever:
            self.ahk.block_forever()

    def show_message(self):
        # Show a message box directly using AHK
        self.ahk.msg_box(f'Python version {platform.python_version()}\nAHK version {self.ahk.get_version()}')

    def autotriage_error_handler(self, _: str, e: Exception):
        self.ahk.show_error_traytip(e.__class__.__name__, e.message if isinstance(e, AutoTriageError) else str(e))

    def triage(self, rank: int | None = None):
        if not self.ahk.win_is_active(self.COMRAD_WINDOW): return
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
                raise AutoTriageError('No request found')
        finally:
            self.ahk.set_clipboard(restore_clipboard)
        request = request_from_clipboard(clipboard)
        self.ahk.send('{Tab}') # Tab to "Radiology Category"
        match request.priority:
            case Priority.UNKNOWN: self.ahk.show_info_traytip('No clinical category', '')
            case Priority.STAT: self.ahk.send('{Home}S')
            case Priority.HOURS_4: self.ahk.send('{Home}4')
            case Priority.HOURS_24: self.ahk.send('{Home}2')
            case Priority.DAYS_2: self.ahk.send('{Home}22')
            case Priority.WEEKS_2: self.ahk.send('{Home}222')
            case Priority.WEEKS_4: self.ahk.send('{Home}44')
            case Priority.WEEKS_6: self.ahk.send('{Home}6')
            case Priority.PLANNED: self.ahk.send('{Home}P')
        self.ahk.send('{Tab 7}') # Tab to "Rank"
        if rank is not None:
            self.ahk.send(f'^a{rank}') # select all, enter rank
        self.ahk.send('{Tab 2}') # Tab to "Body Part"
        try:
            print(f'Searching database for: "{request.exam}"')
            self.fill_out_examination(self.database.get_examination(request), request, True)
        except ExaminationNotFoundError:
            print(f'Examination not found in database')
            SelectExaminationGUI(request, self.fill_out_examination, self.database.get_all_examinations(request.modality))

    def fill_out_examination(self, examination: Examination, request: Request, found_in_database: bool):
        body_part, code = examination
        self.ahk.win_activate(self.COMRAD_WINDOW)
        match body_part:
            case BodyPart.CHEST: self.ahk.send('{Home}C')
            case BodyPart.CHEST_ABDO: self.ahk.send('{Home}CC')
            case body_part:
                self.ahk.send(body_part[:2 if body_part[0] in ('A','N','O','S') else 1])
        self.ahk.send(
            '{Tab 7}' # Tab to table (need 7 rather than 6 if CONT_SENST is showing)
            + '{Home}{Tab}' # Navigate to "Code" cell
            + code # Enter code
            + '{Tab}' # Tab out of cell
        )
        initials = re.search(r'(?<=User:)\w+', self.ahk.win_get_title())[0]
        self.database.log_examination(initials, examination, request, found_in_database)

    def complete_triage(self):
        if not self.ahk.win_is_active(self.COMRAD_WINDOW): return
        self.ahk.send('!s') # Alt-S


