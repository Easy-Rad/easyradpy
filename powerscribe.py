from enum import StrEnum
from lxml import etree
from datetime import datetime
from zeep import Client, ns
from zeep.cache import SqliteCache
from zeep.transports import Transport
from reporter import Reporter
from util import save_json, within_ffs_hours

class Period(StrEnum):
    CUSTOM = 'Custom' # Use date range
    PAST_HOUR = 'PastHour'
    PAST_FOUR_HOURS = 'PastFourHours'
    TODAY = 'Today'
    YESTERDAY = 'Yesterday'
    PAST_TWO_DAYS = 'PastTwoDays'
    PAST_THREE_DAYS = 'PastThreeDays'
    PAST_WEEK = 'PastWeek'
    PAST_TWO_WEEKS = 'PastTwoWeeks'
    PAST_TWO_MONTH = 'PastMonth'

# Script configuration
LOAD_AUTH = False
PS_REPORTS_FILE = 'ps_reports.json'

# PowerScribe 360 constants
PAGE_SIZE = 500 # PS360
PS_HOST = "mschcpscappp4.cdhb.local" # 172.30.4.157
PS_VERSION = '7.0.212.0'
TIME_ZONE_ID = 'New Zealand Standard Time' # PS360
LOCALE = 'en-NZ' # PS360
NAMESPACES = {
    's': ns.SOAP_ENV_12,
    'ns1': 'Nuance/Radiology/Services/2010/01',
    'b':'http://schemas.datacontract.org/2004/07/Nuance.Radiology.Services.Contracts',
}

type Account = tuple[int, str]

class Powerscribe:

    def __init__(self, username: str, password: str):
        self._transport = Transport(cache=SqliteCache(timeout=None))
        client = Client(f'http://{PS_HOST}/RAS/Session.svc?wsdl', transport=self._transport)
        with client.settings(raw_response=True):
            signInResult = client.service.SignIn(
                loginName=username,
                password=password,
                adminMode=False,
                version=PS_VERSION,
                workstation='',
                locale=LOCALE,
                timeZoneId=TIME_ZONE_ID,
                )
        envelope = etree.fromstring(signInResult.text)
        self._account_session = envelope.find('./s:Header/AccountSession', NAMESPACES)
        sign_in_result = envelope.find('./s:Body/ns1:SignInResponse/ns1:SignInResult', NAMESPACES)
        self._account_id = int(sign_in_result.find('./b:AccountID', NAMESPACES).text)
        person = sign_in_result.find('./b:Person', NAMESPACES)
        self.first_name = person.find('./b:FirstName', NAMESPACES).text
        self.last_name = person.find('./b:LastName', NAMESPACES).text

    def getReports(self, account_id: int | None, period: Period, date_range: dict[str, datetime], ffs_hours_only: bool, save_last_request: bool):
        reports: dict[int, Reporter]

        if account_id is None:
            reports={(account_id:=self._account_id):Reporter(self.first_name, self.last_name)}
        else:
            client = Client(f'http://{PS_HOST}/RAS/Account.svc?wsdl', transport=self._transport)
            client.set_default_soapheaders([self._account_session])
            if account_id:
                p = client.service.GetAccount(account_id).Person
                reports={account_id:Reporter(p.FirstName, p.LastName)}
            else:
                reports = {account['ID']: Reporter.fromCommaSeparated(account['Name']) for account in client.service.GetAccountNames(activeOnly=False)}

        client = Client(f'http://{PS_HOST}/RAS/Explorer.svc?wsdl', transport=self._transport)
        client.set_default_soapheaders([self._account_session])
        page_number = 0
        total_reports = 0
        while True:
            page_number += 1
            result = client.service.BrowseOrdersDV(
                siteID=0,
                time=dict(Period=period,From=date_range['from'].isoformat(timespec='seconds'), To=date_range['to'].isoformat(timespec='seconds')),
                orderStatus='All',
                reportStatus='Final',
                # transferStatus='Sent', # filters out 'Rejected' (ELR, NMDHB) but also 'Ready' (recently signed)
                accountID=account_id,
                sort='LastModified ASC',
                pageSize=PAGE_SIZE,
                pageNumber=page_number,
            )
            for item in result:
                if (s := item.find('./SignerAcctID')) is None: # no signer on Powerscribe
                    continue
                signer_id = int(s.text)
                if account_id != 0 and signer_id != account_id: # target user is not the final reporter
                    continue 
                modified = datetime.fromisoformat(item.find('./LastModified').text)
                if not ffs_hours_only or within_ffs_hours(modified):
                    reports[signer_id].reports.append((
                        item.find('./Accession').text,
                        modified,
                    ))
                    total_reports += 1
            if len(result) < PAGE_SIZE:
                print(f"\nReports retrieved from Powerscribe: {(page_number-1)*PAGE_SIZE+len(result)}")
                break
        if save_last_request:
            save_json(PS_REPORTS_FILE, reports)
        if ffs_hours_only:
            print(f"Filtered reports (FFS hours only): {total_reports}")
        return [reporter for reporter in reports.values() if len(reporter.reports)]
