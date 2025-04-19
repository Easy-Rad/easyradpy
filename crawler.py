import requests
import json
from lxml import etree
from datetime import datetime
from zeep import Client, ns
from zeep.cache import SqliteCache
from zeep.transports import Transport
import _secrets
from order import Order

SIGNER_ID = 0 # None for all, 0 for self
DATE_RANGE = {
    'from':datetime(2025,4,10,18),
    'to':datetime(2025,4,17,23),
}

LOAD_AUTH = False # PS360
PAGE_SIZE = 500 # PS360
PS_HOST = "mschcpscappp4.cdhb.local" # 172.30.4.157
IV_HOST = "app-inteleradha-p.healthhub.health.nz" # "59.117.33.42"
PS_AUTH_FILE = 'ps_auth.xml'
PS_REPORTS_FILE = 'ps_reports.json'
IV_ORDERS_FILE = 'iv_orders.json'
NAMESPACES = {
    's': ns.SOAP_ENV_12,
    'ns1': 'Nuance/Radiology/Services/2010/01',
    'b':'http://schemas.datacontract.org/2004/07/Nuance.Radiology.Services.Contracts',
}

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def getReports(account_id: int = None): # use 0 for own account
    transport = Transport(cache=SqliteCache(timeout=None))
    if LOAD_AUTH:
        with open(PS_AUTH_FILE, mode='r') as f:
            signInResult = f.read()
    else:
        client = Client(f'http://{PS_HOST}/RAS/Session.svc?wsdl', transport=transport)
        with client.settings(raw_response=True):
            signInResult = client.service.SignIn(
                loginName=_secrets.USERNAME,
                password=_secrets.PASSWORD,
                adminMode=False,
                version='7.0.212.0',
                workstation='',
                locale='en-NZ',
                timeZoneId='New Zealand Standard Time',
                ).text
        with open(PS_AUTH_FILE, mode='w') as f:
            f.write(signInResult)
    envelope = etree.fromstring(signInResult)
    ps_session_id = envelope.find('./s:Header/AccountSession', NAMESPACES).text
    if account_id == 0:
        account_id = int(envelope.find('./s:Body/ns1:SignInResponse/ns1:SignInResult/b:AccountID', NAMESPACES).text)
    account_session = etree.Element('AccountSession')
    account_session.text = ps_session_id

    client = Client(f'http://{PS_HOST}/RAS/Account.svc?wsdl', transport=transport)
    client.set_default_soapheaders([account_session])

    if account_id:
        p = client.service.GetAccount(account_id).Person
        reports = {account_id: dict(name=f'{p.LastName}, {p.FirstName}', reports=[])}
    else:
        reports = {account['ID']: dict(name=account['Name'], reports=[]) for account in client.service.GetAccountNames(activeOnly=False)}

    client = Client(f'http://{PS_HOST}/RAS/Explorer.svc?wsdl', transport=transport)
    client.set_default_soapheaders([account_session])
    page_number = 0
    while True:
        page_number += 1
        result = client.service.BrowseOrdersDV(
            siteID=0,
            time=dict(Period='Custom',From=DATE_RANGE['from'].isoformat(timespec='seconds'), To=DATE_RANGE['to'].isoformat(timespec='seconds')),
            orderStatus='All',
            reportStatus='Final',
            transferStatus='Sent',
            accountID=account_id,
            sort='LastModified ASC',
            pageSize=PAGE_SIZE,
            pageNumber=page_number,
        )
        for item in result:
            s = item.find('./SignerAcctID')
            if s is None:
                print('No signer ID, skipping ', item.find('./Accession').text)
                continue
            signer_id = int(s.text)
            if account_id and (signer_id != account_id):
                continue
            modified = datetime.fromisoformat(item.find('./LastModified').text)
            if modified.hour >= 6 and modified.hour < 23 and (modified.isoweekday() >= 6 or (modified.hour < 8 or modified.hour >= 18)):
                reports[signer_id]['reports'].append((
                    item.find('./Accession').text,
                    modified,
                ))
        if len(result) < PAGE_SIZE:
            print(f"\nReports retrieved from Powerscribe: {(page_number-1)*PAGE_SIZE+len(result)} (Pages:{page_number})")
            break
    with open(PS_REPORTS_FILE, mode='w') as f:
        json.dump(reports, f, indent=2, default=json_serial)
    return reports

def getOrders(accessions: list, load: bool = False):
    if load:
        with open(IV_ORDERS_FILE, mode='r') as f:
            result = json.load(f)
    else:
        iv_session = requests.Session()
        iv_session.headers['intelerad-serialization-protocol'] = 'JsonSerializationProtocol1.0'
        iv_session.params['username'] = _secrets.USERNAME
        result = iv_session.post(
            url=f"http://{IV_HOST}/InteleViewerService/InteleViewerService",
            headers={'intelerad-application-protocol': 'UserAuthenticationProtocol2.0'},
            json={"method": "authenticateWithClientId", "params": [
                _secrets.USERNAME,
                _secrets.PASSWORD,
                "InteleViewer_5-6-1-P419",
                None
            ]},
        ).json()
        if not result['success']:
            raise Exception('Server error')
        elif failure := result['result']['mFailureType']:
            raise Exception(failure['enumName'])
        iv_session.params['sessionId'] = result['result']['mSessionId']
        print(f"Reports sent to InteleViewer: {len(accessions)}")
        result = iv_session.post(
            url=f"http://{IV_HOST}/WorklistService/WorklistService",
            headers={'intelerad-application-protocol': 'WorklistProtocol8.2'},
            json={"method": "getOrdersByAccessionNumbersWithoutReports", "params": [accessions]},
        ).json()
        with open(IV_ORDERS_FILE, mode='w') as f:
            json.dump(result, f, indent=2)
    return Order.dict_from(result)

if __name__=='__main__':    

    reports = getReports(SIGNER_ID)
    accessions = set()
    for reporter in reports.values():
        accessions.update([report[0] for report in reporter['reports']])
    iv_orders = getOrders(list(accessions), False)
    if len(iv_orders) != len(reports):
        print(f"Valid orders found on InteleViewer: {len(iv_orders)}")
    print()
    reporters = []
    for reporter in reports.values():
        ps_reports = [(accession,modified) for (accession,modified) in reporter['reports'] if accession in iv_orders ]
        if not len(ps_reports): continue
        study_count = 0
        fee = 0
        studies = {'CT':[0,0,0,0],'MR':[0],'CR':[0,0,0],'US':[0]}
        for (accession,modified) in ps_reports:
            order = iv_orders[accession]
            if order.ffs_body_part_count:
                study_count += 1
                fee += order.fee
                studies[order.modality][order.ffs_body_part_count-1] += 1
                # if order.ffs_body_part_count > 1:
                #     print(f"{order.modality}x{order.ffs_body_part_count}: {order.body_parts} ({order.study_description})")
            # print(f"{order} on {modified.strftime('%a %d %b %Y, %H:%M')}")
        if study_count:
            reporters.append(dict(name=reporter['name'], study_count=study_count, studies=studies, fee=fee))
    reporters.sort(key=lambda x:x['fee'], reverse=False)
    for reporter in reporters:
        print(reporter['name'])
        print(f"Studies: {reporter['study_count']}")
        for modality, body_part_counts in reporter['studies'].items():
            count = 0
            for i, body_part_count in enumerate(body_part_counts):
                if body_part_count:
                    count += body_part_count
            if count:
                s = f'{modality}: {count}'
                if len(studies[modality]) > 1:
                    s += f' ({', '.join([f"{body_part_count} x {i+1}p" for i, body_part_count in enumerate(body_part_counts) if body_part_count])})'
                print(s)
        print("FFS: ${:,d}\n".format(reporter['fee']))

            

