from datetime import datetime
from os import environ

import dearpygui.dearpygui as dpg
from dearpygui.dearpygui import add_group

from requests.exceptions import ConnectionError
from errors import UsernameError, PasswordError, AuthError, InteleviewerServerError
from ffs import FFS_DATA
from inteleviewer import InteleViewer
from order import Order
from powerscribe import Powerscribe
from reporter import ffs_reports, Reporter
from reporter import unique_accessions
from search_config import Period, Account
from search_config import SearchConfig
from util import date_format, fee_format


class Gui:
    def __init__(self) -> None:
        self.ps = self.iv = None
        self.accounts: dict[str, int] = {}
        try:
            self.proxy = environ['proxy']
        except KeyError:
            self.proxy = None
        with dpg.window(label='Main') as self.main_window:
            dpg.set_primary_window(self.main_window, True)
            with dpg.child_window(label="Auth", auto_resize_y=True) as self.login_window:
                with dpg.group(horizontal=True):
                    with dpg.group(horizontal=True) as self.auth_input_fields:
                        dpg.add_text('Username:')
                        self.username_field = dpg.add_input_text(hint="Username", callback=self._on_login_request, on_enter=True,
                                                            auto_select_all=True, width=100)
                        dpg.add_text('Password:')
                        self.password_field = dpg.add_input_text(password=True, hint="Password", callback=self._on_login_request,
                                                            on_enter=True, auto_select_all=True, width=100)
                    self.login_button = dpg.add_button(label="Log in", callback=self._on_login_request)
                    self.loading = self._add_loading()
                    dpg.focus_item(self.username_field)
                    with dpg.group(horizontal=True, show=False) as self.auth_display:
                        self.user_greeting = dpg.add_text()
                        dpg.add_button(label="Log out", callback=self._on_logout_request)
                self.error_text = dpg.add_text(label="Error", show=False, color=(255, 255, 0))
            with dpg.child_window(label="Search", show=False) as self.search_window:
                with dpg.group(horizontal=True):
                    dpg.add_text('User:')
                    self._select_user = dpg.add_radio_button(items=list(Account), default_value=Account.ALL,
                                                             horizontal=True, callback=self._on_account_select)
                    self._select_named_user = dpg.add_combo([], default_value="Select...", fit_width=True, show=False)
                    dpg.add_text('Period:')
                    self._select_period = dpg.add_combo(list(Period), default_value=Period.PAST_HOUR,
                                                        fit_width=True, callback=self._on_period_select)
                    with dpg.group(horizontal=True, show=False) as self.custom_period_group:
                        for label, date in {
                            'from': (from_date := datetime.today().replace(hour=7, minute=0, second=0, microsecond=0)),
                            'to': from_date.replace(hour=23)}.items():
                            with dpg.popup(dpg.add_button(tag=f"{label}_date_time_button"),
                                           mousebutton=dpg.mvMouseButton_Left, no_move=False, modal=False):
                                dpg.add_date_picker(
                                    tag=f"{label}_date_picker",
                                    label=f"{label} date",
                                    default_value=dict(month_day=date.day, year=date.year - 1900, month=date.month - 1),
                                    callback=self._update_date_time,
                                    user_data=label,
                                )
                                dpg.add_time_picker(
                                    tag=f"{label}_time_picker",
                                    label=f"{label} time",
                                    hour24=True,
                                    default_value=dict(hour=date.hour, minute=date.minute, second=date.second),
                                    callback=self._update_date_time,
                                    user_data=label,
                                )
                                self._update_date_time(None, None, label)
                    dpg.add_text('FFS:')
                    self.ffs_checkbox = dpg.add_checkbox(default_value=True)
                    dpg.add_button(label="Search", callback=self._on_search)
                self.results = add_group()

    def _on_logout_request(self, _, __, to_delete=None):
        if to_delete is not None:
            dpg.delete_item(to_delete)
        dpg.delete_item(self.results, children_only=True, slot=1)
        self.ps = self.iv = None
        dpg.hide_item(self.search_window)
        dpg.hide_item(self.auth_display)
        dpg.show_item(self.login_button)
        dpg.show_item(self.auth_input_fields)

    def _on_login_request(self) -> None:
        username_value = dpg.get_value(self.username_field)
        password_value = dpg.get_value(self.password_field)
        if not username_value:
            dpg.focus_item(self.username_field)
        elif not password_value:
            dpg.focus_item(self.password_field)
        else:
            dpg.disable_item(self.username_field)
            dpg.disable_item(self.password_field)
            dpg.disable_item(self.login_button)
            dpg.hide_item(self.error_text)
            dpg.show_item(self.loading)
            try:
                try:
                    iv = InteleViewer.from_login_call(username_value, password_value, proxy=self.proxy)
                except ConnectionError:
                    dpg.set_value(self.error_text, 'InteleViewer connection error')
                    dpg.show_item(self.error_text)
                else:
                    try:
                        ps = Powerscribe.from_login_call(username_value, password_value, proxy=self.proxy)
                        accounts = ps.get_accounts()
                    except ConnectionError:
                        dpg.set_value(self.error_text, 'Powerscribe connection error')
                        dpg.show_item(self.error_text)
                    else:
                        self.on_login(ps, iv, accounts)
            except AuthError as e:
                dpg.set_value(self.error_text, e)
                dpg.show_item(self.error_text)
                if isinstance(e, UsernameError):
                    dpg.focus_item(self.username_field)
                elif isinstance(e, PasswordError):
                    dpg.focus_item(self.password_field)
            finally:
                dpg.enable_item(self.username_field)
                dpg.enable_item(self.password_field)
                dpg.enable_item(self.login_button)
                dpg.hide_item(self.loading)

    def on_login(self, ps: Powerscribe, iv: InteleViewer, accounts: dict[str, int]) -> None:
        self.ps = ps
        self.iv = iv
        self.accounts = accounts
        dpg.configure_item(self._select_named_user, items=(list(self.accounts.keys())))
        dpg.hide_item(self.login_button)
        dpg.hide_item(self.auth_input_fields)
        dpg.set_value(self.user_greeting, f'Logged in as {self.ps.first_name} {self.ps.last_name}')
        dpg.show_item(self.auth_display)
        dpg.show_item(self.search_window)

    def _on_account_select(self, _, app_data):
        if app_data == Account.OTHER:
            dpg.show_item(self._select_named_user)
        else:
            dpg.hide_item(self._select_named_user)

    @staticmethod
    def _get_datetime_from_widgets(pickers: list[int | str]):
        d, t = dpg.get_values(pickers)
        return datetime(
            year=d['year'] + 1900,
            month=d['month'] + 1,
            day=d['month_day'],
            hour=t['hour'],
            minute=t['min'],
            second=t['sec'],
        )

    def _update_date_time(self, _, __, tag_label):
        new_datetime = self._get_datetime_from_widgets(
            [f"{tag_label}_date_picker", f"{tag_label}_time_picker"])
        dpg.set_item_label(f"{tag_label}_date_time_button",
                           f'{tag_label} {date_format(new_datetime)}')

    def _on_period_select(self, _, app_data):
        if app_data == Period.CUSTOM:
            dpg.show_item(self.custom_period_group)
        else:
            dpg.hide_item(self.custom_period_group)

    @staticmethod
    def _on_progress(progress_bar: int, fetched: int, total: int):
        try:
            progress = fetched / total
        except ZeroDivisionError:
            progress = 1
        dpg.set_value(progress_bar, progress)
        dpg.configure_item(progress_bar, overlay=f'{fetched}/{total} ({progress:.0%})')

    def _on_search(self, search_button):
        dpg.disable_item(search_button)
        dpg.delete_item(self.results, children_only=True, slot=1)
        with dpg.group(parent=self.results) as progress_display:
            with dpg.group(horizontal=True):
                ps_progress = dpg.add_progress_bar()
                dpg.add_text("Powerscribe")
            with dpg.group(horizontal=True):
                iv_progress = dpg.add_progress_bar()
                dpg.add_text("Inteleviewer")
        search_config = self._get_search_config()
        reports = self.ps.get_reports(search_config, lambda fetched, total: self._on_progress(ps_progress, fetched, total))
        accessions = unique_accessions(reports)
        self._on_progress(iv_progress, 0, len(accessions))
        try:
            orders = self.iv.get_orders(accessions, search_config)
        except InteleviewerServerError as e:
            with dpg.window(modal=True) as error_window:
                dpg.add_text(f'InteleViewer server error')
                dpg.add_text(str(e), indent=1)
                dpg.add_button(label="Log out", callback=self._on_logout_request, user_data=error_window)
        else:
            self._on_progress(iv_progress, len(orders), len(orders))
            self._generate_table(self.results, reports, orders, search_config.ffs_only)
        finally:
            dpg.delete_item(progress_display)
            dpg.enable_item(search_button)

    def _get_search_config(self) -> SearchConfig:
        ffs = dpg.get_value(self.ffs_checkbox)
        account_id = 0
        match dpg.get_value(self._select_user):
            case Account.ME:
                account_id = None
            case Account.ALL:
                account_id = 0
            case Account.OTHER:
                account_id = self.accounts[dpg.get_value(self._select_named_user)]
        period = dpg.get_value(self._select_period)
        date_range = {
            tag_label: self._get_datetime_from_widgets([f"{tag_label}_date_picker", f"{tag_label}_time_picker"]) for
            tag_label in ('from', 'to')}
        return SearchConfig(
            ffs_only=ffs,
            account_id=account_id,
            period=period,
            from_date=date_range['from'],
            to_date=date_range['to'],
        )

    @staticmethod
    def _add_loading() -> int:
        return dpg.add_loading_indicator(show=False, style=0, color=(255, 255, 255), radius=1.5)

    @staticmethod
    def _generate_table(parent: int, reports: list[Reporter], orders: dict[str, Order], ffs: bool) -> None:
        with dpg.table(
            parent=parent,
            header_row=True,
            freeze_rows=1,
            scrollY=True,
            policy=dpg.mvTable_SizingFixedFit,
            resizable=True,
                reorderable=True,
                sortable=True,
                sort_multi=True,
                callback=Gui.sort_callback,
        ):
            dpg.add_table_column(label='Surname')
            dpg.add_table_column(label='First name')
            if ffs: dpg.add_table_column(label='Fee', width=400, width_stretch=False, width_fixed=True, init_width_or_weight=150)
            dpg.add_table_column(label='Studies', width_stretch=True, init_width_or_weight=1)
            for reporter in ffs_reports(reports, orders) if ffs else reports:
                with dpg.table_row():
                    dpg.add_text(reporter.last_name)
                    dpg.add_text(reporter.first_name)
                    if ffs:
                        with dpg.tree_node(label=fee_format(reporter.ffsProfile.fee), default_open=False):
                            with dpg.table():
                                dpg.add_table_column(label='n')
                                for modality_name, _ in FFS_DATA.values():
                                    dpg.add_table_column(label=modality_name)
                                for body_part_count in range(1, 5):
                                    with dpg.table_row():
                                        dpg.add_text(str(body_part_count))
                                        for modality_key in FFS_DATA.keys():
                                            try:
                                                dpg.add_text(
                                                    str(reporter.ffsProfile.studies[modality_key][body_part_count - 1]))
                                            except IndexError:
                                                dpg.add_text()
                                with dpg.table_row():
                                    dpg.add_text('T')
                                    for modality_key in FFS_DATA.keys():
                                        dpg.add_text(str(sum(reporter.ffsProfile.studies[modality_key])))
                    with dpg.tree_node(label=f'{len(reporter.reports)}', default_open=False):
                        with dpg.table(
                                label=f'{reporter.first_name} {reporter.last_name}',
                                header_row=True,
                                freeze_rows=1,
                                policy=dpg.mvTable_SizingFixedFit,
                                # resizable=True,
                                # policy=dpg.mvTable_SizingFixed,
                                resizable=True,
                        ):
                            dpg.add_table_column(label='Accession')
                            dpg.add_table_column(label='Modified')
                            dpg.add_table_column(label='Modality', init_width_or_weight=20)
                            if ffs:
                                dpg.add_table_column(label='Body parts', init_width_or_weight=20)
                                dpg.add_table_column(label='Fee')
                            dpg.add_table_column(label='Study Description', width_stretch=True, init_width_or_weight=1)
                            for accession, modified in reporter.reports:
                                order = orders[accession]
                                with dpg.table_row():
                                    dpg.add_text(accession)
                                    dpg.add_text(date_format(modified))
                                    dpg.add_text(order.modality)
                                    if ffs:
                                        dpg.add_text(str(order.ffs_body_part_count))
                                        dpg.add_text(fee_format(order.fee))
                                    dpg.add_text(order.study_description)

    @staticmethod
    def sort_callback(sender, sort_specs):
        if sort_specs is None: return
        rows = []
        columns = dpg.get_item_children(sender, 0)
        for row_id in dpg.get_item_children(sender, 1):
            keys = []
            for sort_col, direction in sort_specs:
                cell = dpg.get_item_children(row_id, 1)[columns.index(sort_col)]
                match dpg.get_item_label(sort_col):
                    case 'Surname' | 'First name':
                        keys.append(dpg.get_value(cell))
                    case 'Fee':
                        keys.append(int(dpg.get_item_label(cell)[1:].replace(',', '')))
                    case 'Studies':
                        keys.append(len(dpg.get_item_children(dpg.get_item_children(cell, 1)[0], 1)))
                    case label:
                        raise Exception(f'Unexpected sort column label: {label}')
            rows.append((row_id, tuple(keys)))
        for i, spec in reversed(list(enumerate(sort_specs))):
            rows.sort(key=lambda row: row[1][i], reverse=spec[1] < 0)
        dpg.reorder_items(sender, 1, [row_id for row_id, keys in rows])

if __name__ == '__main__':
    dpg.create_context()
    dpg.create_viewport(title='Dashboard', width=1200, height=600, always_on_top=False)
    gui = Gui()
    try: # load saved session from environment variables
        assert (ps_session := environ['ps_session'])
        assert (iv_session := environ['iv_session'])
    except (KeyError, AssertionError):
        pass
    else:
        assert (username := environ['username'])
        assert (ps_account_id := int(environ['ps_account_id']))
        powerscribe = Powerscribe.from_saved_session(ps_account_id, f'[{username}]', f'[ID#{ps_account_id}]' , ps_session,
                                            proxy=gui.proxy)
        inteleviewer = InteleViewer.from_saved_session(username, iv_session, proxy=gui.proxy)
        gui.on_login(powerscribe, inteleviewer, powerscribe.get_accounts())
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()