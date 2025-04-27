from datetime import datetime
from typing import Callable

from lxml.etree import Element
from zeep import Client, ns, Plugin
from zeep.cache import SqliteCache
from zeep.exceptions import Fault
from zeep.transports import Transport

from .errors import PasswordError, UsernameError, AuthError, PowerscribeServerError
from .ffs import FFS_DATA, within_ffs_hours, get_local_date_time
from .json_encoding import save_json
from .reporter import Reporter
from .search_config import SearchConfig

# Script configuration
LOAD_AUTH = False
PS_REPORTS_FILE = 'ps_reports.json'

# PowerScribe 360 constants
PAGE_SIZE = 2000 # PS360 (default=500)
PS_VERSION = '7.0.212.0'
TIME_ZONE_ID = 'New Zealand Standard Time' # PS360
LOCALE = 'en-NZ' # PS360
ORDER_STATUS = 'All'
REPORT_STATUS = 'Final'
SORT = 'LastModified ASC'
SITE_ID = 0

NAMESPACES = {
    's': ns.SOAP_ENV_12,
    'b':'http://schemas.datacontract.org/2004/07/Nuance.Radiology.Services.Contracts',
    'ns1': 'Nuance/Radiology/Services/2010/01',
    'ns2': 'http://schemas.datacontract.org/2004/07/Nuance.Radiology.Services',
}
PS_HOST = "mschcpscappp4.cdhb.local"
# PS_HOST = "172.30.4.157"

class Powerscribe:

    _account_id: int
    first_name: str
    last_name: str

    @staticmethod
    def from_login_call(username: str, password: str, host: str | None = None, proxy: str | None = None):
        ps = Powerscribe(host, proxy)
        ps.login(username, password)
        return ps

    @staticmethod
    def from_saved_session(account_id: int, first_name: str, last_name: str, session_id: str, host: str | None = None, proxy: str | None = None):
        ps = Powerscribe(host, proxy)
        ps._account_id = account_id
        ps.first_name = first_name
        ps.last_name = last_name
        ps._account_session = Element('AccountSession')
        ps._account_session.text = session_id
        print(f'Using Powerscribe from saved session ID {session_id}')
        return ps

    def __init__(self, host: str | None, proxy: str | None):
        self._account_session = None
        self._host = host or PS_HOST
        self._transport = Transport(cache=SqliteCache(timeout=None))
        if proxy:
            self._transport.session.proxies['http'] = proxy

    def login(self, username: str, password: str):
        client = Client(f'http://{self._host}/RAS/Session.svc?wsdl', transport=self._transport, plugins=[SaveAccountSessionPlugin(self)])
        try:
            sign_in_result = client.service.SignIn(
                loginName=username,
                password=password,
                adminMode=False,
                version=PS_VERSION,
                workstation='',
                locale=LOCALE,
                timeZoneId=TIME_ZONE_ID,
            )
        except Fault as f:
            raise self.to_error(f)
        assert self._account_session is not None
        self._account_id = sign_in_result.SignInResult.AccountID
        self.first_name = sign_in_result.SignInResult.Person.FirstName
        self.last_name = sign_in_result.SignInResult.Person.LastName
        print(f'Signed in to Powerscribe as {self.first_name} {self.last_name} with account ID {self._account_id} and session ID {self._account_session.text}')

    @staticmethod
    def to_error(f: Fault):
        exception = f.detail.find('./ns2:RasException', NAMESPACES)
        error_type = exception.find('./ns2:Type', NAMESPACES).text
        code = int(exception.find('./ns2:Code', NAMESPACES).text)
        match error_type, code:
            case 'Security', 3:
                return UsernameError('Powerscribe', f.message)
            case 'Security', 0:
                return AuthError('Powerscribe', f.message)
            case 'InvalidOperation', 4:
                return PasswordError('Powerscribe', f.message)
        stack_trace = exception.find('./ns2:Details', NAMESPACES).text.split('\r\n')
        return PowerscribeServerError(f.message, error_type, code, stack_trace)

    def get_accounts(self):
        client = Client(f'http://{self._host}/RAS/Account.svc?wsdl', transport=self._transport)
        client.set_default_soapheaders([self._account_session])
        try:
            accounts = {account['Name']: account['ID'] for account in
                sorted(client.service.GetAccountNames(activeOnly=True), key=lambda a: a['Name'])}
        except Fault as f:
            raise self.to_error(f)
        else:
            return accounts
    def get_reports(self, search_config: SearchConfig, on_progress_update: Callable[[int, int], None] | None = None):
        reports: dict[int, Reporter]
        if (account_id:=search_config.account_id) is None:
            reports={(account_id:=self._account_id):Reporter(self.first_name, self.last_name)}
        else:
            client = Client(f'http://{self._host}/RAS/Account.svc?wsdl', transport=self._transport)
            client.set_default_soapheaders([self._account_session])
            if account_id:
                p = client.service.GetAccount(account_id).Person
                reports={account_id:Reporter(p.FirstName, p.LastName)}
            else:
                reports = {account['ID']: Reporter.from_comma_separated(account['Name']) for account in
                           client.service.GetAccountNames(activeOnly=False)}

        client = Client(f'http://{self._host}/RAS/Explorer.svc?wsdl', transport=self._transport)
        client.set_default_soapheaders([self._account_session])
        time = dict(
            Period=search_config.period,
            From=search_config.from_date.isoformat(timespec='seconds'),
            To=search_config.to_date.isoformat(timespec='seconds'),
        )
        expected_reports = client.service.GetBrowseOrdersCount(
            siteID=SITE_ID,
            time=time,
            orderStatus=ORDER_STATUS,
            reportStatus=REPORT_STATUS,
            accountID=account_id
        )
        print(f"Reports expected from Powerscribe: {expected_reports}")
        page_number = 0
        retrieved_reports = 0
        filtered_reports = 0
        while True:
            if on_progress_update is not None:
                on_progress_update(retrieved_reports, expected_reports)
            page_number += 1
            result = client.service.BrowseOrdersDV(
                siteID=SITE_ID,
                time=time,
                orderStatus=ORDER_STATUS,
                reportStatus=REPORT_STATUS,
                accountID=account_id,
                sort=SORT,
                pageSize=PAGE_SIZE,
                pageNumber=page_number,
            )
            retrieved_reports += len(result)
            for item in result:
                if (s := item.find('./SignerAcctID')) is None: # no signer on Powerscribe
                    continue
                signer_id = int(s.text)
                if account_id != 0 and signer_id != account_id: # target user is not the final reporter
                    continue
                accession = item.find('./Accession').text
                if search_config.ffs_only and accession[-2:] not in FFS_DATA: # filter modality
                    continue
                modified = get_local_date_time(datetime.fromisoformat(item.find('./LastModified').text), signer_id)
                if search_config.ffs_only and not within_ffs_hours(modified): # filter last modified timestamp
                    continue
                reports[signer_id].reports.append((accession,modified))
                filtered_reports += 1
            if len(result) < PAGE_SIZE:
                print(f"Reports retrieved from Powerscribe: {retrieved_reports}")
                break
        if on_progress_update is not None:
            on_progress_update(retrieved_reports, retrieved_reports)
        if search_config.ffs_only:
            print(f"Filtered reports (FFS only): {filtered_reports}")
        if search_config.save_last_request:
            save_json(PS_REPORTS_FILE, reports)
        return [reporter for reporter in reports.values() if len(reporter.reports)]

class SaveAccountSessionPlugin(Plugin):
    def __init__(self, ps : Powerscribe):
        self.ps = ps

    def ingress(self, envelope, http_headers, operation):
        self.ps._account_session = envelope.find('./s:Header/AccountSession', NAMESPACES)
        return envelope, http_headers

