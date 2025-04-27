import gzip
import json

import requests

from errors import UsernameError, PasswordError, InteleviewerServerError
from json_encoding import save_json
from order import Order
from search_config import SearchConfig

IV_ORDERS_FILE = 'iv_orders.json'
IV_HOST = "app-inteleradha-p.healthhub.health.nz"
# IV_HOST = "59.117.33.42"

class InteleViewer:

    @staticmethod
    def from_saved_session(username: str, session_id: str, host: str | None = None, proxy: str | None = None):
        iv = InteleViewer(username, host, proxy)
        iv._session.params['sessionId'] = session_id
        print(f'Using InteleViewer from saved session ID {session_id}')
        return iv

    @staticmethod
    def from_login_call(username: str, password: str, host: str | None = None, proxy: str | None = None):
        iv = InteleViewer(username, host, proxy)
        iv.login(username, password)
        return iv

    def __init__(self, username: str, host: str | None, proxy: str | None):
        self._host = host or IV_HOST
        self._session = requests.Session()
        if proxy:
            self._session.proxies['http'] = proxy
        self._session.headers['intelerad-serialization-protocol'] = 'JsonSerializationProtocol1.0'
        self._session.params['username'] = username

    def _request(self, service:str, protocol:str, method: str, params: list):
        result = self._session.post(
            url=f'http://{self._host}/{service}/{service}',
            headers={
                'Content-Encoding': 'gzip',
                'Content-Type': 'application/json',
                'intelerad-application-protocol': protocol,
            },
            data=gzip.compress(json.dumps(dict(method=method, params=params)).encode('utf-8')),
        ).json()
        if not result['success']:
            error = result['error']
            raise InteleviewerServerError(
                code=error['code'],
                message=error['message'],
                data=error['data'],
            )
        elif isinstance(result['result'], dict) and (failure := result['result']['mFailureType']):
            try:
                match failure['enumName']:
                    case 'BAD_USERNAME':
                        raise UsernameError('InteleViewer', 'username error (case sensitive)')
                    case 'BAD_PASSWORD':
                        raise PasswordError('InteleViewer', 'password error')
                    case e:
                        raise Exception(e)
            except KeyError:
                raise Exception(json.dumps(failure))
        else:
            return result['result']

    def login(self, username: str, password: str):
        sign_in_request = self._request(
            service='InteleViewerService',
            protocol='UserAuthenticationProtocol2.0',
            method='authenticateWithClientId',
            params= [
                username,
                password,
                'InteleViewer_5-6-1-P419',
                None
            ],
        )
        self._session.params['sessionId'] = session_id = sign_in_request['mSessionId']
        user = sign_in_request['mUser']
        print(f'Signed in to InteleViewer as {user['mFirstName']} {user['mLastName']} with session ID {session_id}')

    def get_orders(self, accessions: set[str], search_config: SearchConfig):
        orders = {}
        if len(accessions):
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
            print(f"Orders retrieved from InteleViewer: {len(orders)}")
            if search_config.save_last_request:
                save_json(IV_ORDERS_FILE, orders)
        return orders
