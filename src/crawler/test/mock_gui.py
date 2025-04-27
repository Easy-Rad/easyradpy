import dearpygui.dearpygui as dpg

from ..gui import Gui
from .mock_data import sample_reports, sample_orders

if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport(title='Test Dashboard', width=1200, height=700, always_on_top=False)
    with dpg.window(label='All', width=1200, height=350) as w:
        Gui._generate_table(w, sample_reports, sample_orders, False)
    with dpg.window(label='FFS', width=1200, height=350, pos=[0,400]) as w:
        Gui._generate_table(w, sample_reports, sample_orders, True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
