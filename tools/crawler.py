import sys
from datetime import datetime

from src.interface import InteleViewer, Powerscribe
from src.model import unique_accessions, ffs_reports, SearchConfig, Period

SEARCH_CONFIG =SearchConfig(
    ffs_only=False,
    account_id=None, # 0 for all, None for self
    period=Period.PAST_TWO_WEEKS,
    from_date=datetime(2025,4,23,19, 17), # Used if PERIOD = Period.CUSTOM
    to_date=datetime(2025,4,23,19, 18), # Used if PERIOD = Period.CUSTOM
    save_last_request=True
)
PRINT_INDIVIDUAL_ORDERS = True

def on_progress(fetched: int, total: int):
    try: print(f'Fetched {fetched}/{total} ({fetched / total:.0%})')
    except ZeroDivisionError: pass

if __name__=='__main__':
    username = input('Enter username:')
    password = input('Enter password:')
    proxy = sys.argv[1] if len(sys.argv) > 1 else None
    ps_host = sys.argv[2] if len(sys.argv) > 2 else None
    iv_host = sys.argv[3] if len(sys.argv) > 3 else None
    powerscribe = Powerscribe.from_login_call(username, password, ps_host, proxy)
    inteleviewer = InteleViewer.from_login_call(username, password, iv_host, proxy)
    reports = powerscribe.get_reports(SEARCH_CONFIG, on_progress)
    orders = inteleviewer.get_orders(unique_accessions(reports), SEARCH_CONFIG)
    for reporter in (ffs_reports(reports, orders) if SEARCH_CONFIG.ffs_only else reports):
        print(reporter.get_report(orders, PRINT_INDIVIDUAL_ORDERS))