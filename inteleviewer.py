import requests
import json
from order import Order
from util import save_json

IV_ORDERS_FILE = 'iv_orders.json'

# InteleViewer constants
IV_HOST = "app-inteleradha-p.healthhub.health.nz" # "59.117.33.42"

class InteleViewer:

    def __init__(self, username: str, password: str):
        self.iv_session = requests.Session()
        self.iv_session.headers['intelerad-serialization-protocol'] = 'JsonSerializationProtocol1.0'
        self.iv_session.params['username'] = username
        self.iv_session.params['sessionId'] = self._request(
            service='InteleViewerService',
            protocol='UserAuthenticationProtocol2.0',
            method='authenticateWithClientId',
            params= [
                username,
                password,
                'InteleViewer_5-6-1-P419',
                None
            ],
        )['mSessionId']

    def _request(self, service:str, protocol:str, method: str, params: list):
        result = self.iv_session.post(
            url=f'http://{IV_HOST}/{service}/{service}',
            headers={'intelerad-application-protocol': protocol},
            json=dict(method=method, params=params),
        ).json()
        if not result['success']:
            raise Exception('Server error')
        elif result['result'] is dict and (failure := result['result']['mFailureType']):
            raise Exception(json.dumps(failure))
        return result['result']
    
    def getOrders(self, accessions: set[str], ffs_only: bool, save_last_request: bool):
        print(f"Orders retrieved from InteleViewer: {len(accessions)}")
        orders = {}
        for data in self._request(
            service='WorklistService',
            protocol='WorklistProtocol8.2',
            method='getOrdersByAccessionNumbersWithoutReports',
            params= [list(accessions)],
        ):
            procedure = data['mRequestedProcedureList'][0]
            modality = procedure['mNormalizedModality']
            order = Order(
                data['mAccessionNumber'],
                data['mBodyPartList'],
                modality,
                procedure['mStudyDescription'],
                procedure['mRemoteImageCount'],
                )
            orders[order.accession] = order
        if ffs_only and len(orders) != len(accessions):
            print(f"Orders filtered for FFS: {len(orders)}")
        if save_last_request:
            save_json(IV_ORDERS_FILE, orders)
        return orders
