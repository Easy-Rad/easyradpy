import json

from ..autotriage import Request, Examination, BodyPart, Modality
from ..util.format import tokenise_request, decode_key

import requests

FIREBASE_URL = 'https://cogent-script-128909-default-rtdb.firebaseio.com'

class Database:

    def __init__(self, session = requests.Session()):
        self.session = session

    def get_examination(self, request: Request) -> Examination:
        tokenised_exam = tokenise_request(request.exam)
        data = self.session.get(f'{FIREBASE_URL}/examination/{request.modality}.json', params=dict(
            orderBy=json.dumps('tokenised'),
            equalTo=json.dumps(tokenised_exam),
            limitToFirst=1,
        )).json()
        if data is not None:
            code, examination = next(iter(data.items()))
            encoded_body_part = examination['bodyPart']
        else: # try alias
            code = self.session.get(f'{FIREBASE_URL}/label/{request.modality}/{tokenised_exam}.json').json()
            if code is None:
                raise ExaminationNotFoundError(request)
            encoded_body_part = self.session.get(f'{FIREBASE_URL}/examination/{request.modality}/{code}/bodyPart.json').json()
        return BodyPart(decode_key(encoded_body_part)), code

class ExaminationNotFoundError(Exception):
    def __init__(self, request: Request):
        self.request = request