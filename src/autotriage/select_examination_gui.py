import json
from collections.abc import Callable
from tkinter import *
from tkinter import ttk

from .examination import Examination, BodyPart
from .modality import Modality
from .request import Request


class SelectExaminationGUI:

    def __init__(self, request: Request, callback: Callable[[Examination], None], examinations: dict | None):
        self.request = request
        self.callback = callback
        self.examinations = examinations or self._get_examinations()
        self.root = Tk()
        self.root.geometry("600x400")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.attributes('-topmost', True)
        self.root.title("Select study to protocol")
        mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=NSEW)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=1)
        ttk.Label(mainframe, text="Requested study:").grid(column=0, row=0)
        requested_study_entry = ttk.Entry(mainframe)
        requested_study_entry.insert(0, request.exam)
        requested_study_entry.state(['readonly'])
        requested_study_entry.grid(column=1, row=0, sticky=EW)
        self.remember_alias = BooleanVar(value=False)
        ttk.Label(mainframe, text="Filter:").grid(column=0, row=1)
        self.search_var = StringVar()
        self.search_entry = ttk.Entry(mainframe, textvariable=self.search_var)
        self.search_entry.focus()
        self.search_entry.grid(column=1, row=1, sticky=EW)
        self.search_var.trace_add('write', self._filter_treeview)
        # ttk.Checkbutton(mainframe, text='Remember alias:', variable=self.remember_alias).grid(column=0, columnspan=2, row=1, sticky=EW)
        self.tree = ttk.Treeview(mainframe, columns=('code',))
        self.tree.heading('code', text='Code')
        self.tree.column('#0', width=300, stretch=True)
        self.tree.column('code', width=50)
        for code, data in self.examinations.items():
            self.tree.insert('', 'end', iid=code, text=data['name'], values=(code,), tags='exam')
        self.tree.tag_bind('exam', '<Double-Button-1>', self._select_study)
        self.tree.grid(column=0, columnspan=2, row=2, sticky=NSEW)
        self.root.mainloop()

    def _select_study(self, event):
        code = self.tree.identify_row(event.y)
        examination: Examination = BodyPart(self.examinations[code]['bodyPart']), code
        self.callback(examination)
        self.root.destroy()

    @staticmethod
    def _get_examinations():
        with open('test/mock_examinations.json', 'r') as f:
            return json.load(f)

    def _filter_treeview(self, *args):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for code, data in self.examinations.items():
            if search_term in data['name'].lower() or search_term in code.lower():
                self.tree.insert('', 'end', iid=code, text=data['name'], values=(code,), tags='exam')

if __name__ == "__main__":
    SelectExaminationGUI(Request(Modality.CT, 'CT HEAD ABDOMEN'), lambda x: print(x), None)