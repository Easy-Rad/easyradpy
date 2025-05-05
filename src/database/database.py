import json

from ..autotriage import Request, Examination, BodyPart, Modality
from ..util.format import decode_key

import requests

FIREBASE_URL = 'https://cogent-script-128909-default-rtdb.firebaseio.com'

class Database:

    def __init__(self, session = requests.Session()):
        self.session = session

    def get_examination(self, request: Request) -> Examination:
        data = self.session.get(f'{FIREBASE_URL}/label/{request.modality}/{request.tokenised_exam()}.json').json()
        if data is not None:
            return BodyPart(data['bodyPart']), data['code']
        else:
            raise ExaminationNotFoundError(request)

class ExaminationNotFoundError(Exception):
    def __init__(self, request: Request):
        self.request = request