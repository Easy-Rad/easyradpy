from datetime import datetime
from powerscribe import Powerscribe, Period
from inteleviewer import InteleViewer
from reporter import unique_accessions, ffs_reports
import _secrets

SIGNER_ID = 0 # 0 for all, None for self
PERIOD = Period.CUSTOM
DATE_RANGE = { # Used if PERIOD = Period.CUSTOM
    'from':datetime(2025,4,18,1),
    'to':datetime(2025,4,18,11),
}
FFS_ONLY = False
PRINT_INDIVIDUAL_ORDERS = False
SAVE_LAST_REQUEST = True

if __name__=='__main__':
    powerscribe = Powerscribe(_secrets.USERNAME, _secrets.PASSWORD)
    reports = powerscribe.getReports(SIGNER_ID, PERIOD, DATE_RANGE, FFS_ONLY, SAVE_LAST_REQUEST)
    inteleviewer = InteleViewer(_secrets.USERNAME, _secrets.PASSWORD)
    orders = inteleviewer.getOrders(unique_accessions(reports), FFS_ONLY, SAVE_LAST_REQUEST)
    for reporter in (ffs_reports(reports, orders) if FFS_ONLY else reports):
        reporter.print(orders, PRINT_INDIVIDUAL_ORDERS)