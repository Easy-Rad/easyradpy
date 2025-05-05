import requests

from ..autotriage import Request, Examination, BodyPart, Modality

FIREBASE_URL = 'https://cogent-script-128909-default-rtdb.firebaseio.com'

class Database:

    def __init__(self, session = requests.Session()):
        self.session = session
        self.cached_examinations = {}

    def get_examination(self, request: Request) -> Examination:
        data = self.session.get(f'{FIREBASE_URL}/label/{request.modality}/{request.tokenised_exam()}.json').json()
        if data is not None:
            return BodyPart(data['bodyPart']), data['code']
        else:
            raise ExaminationNotFoundError

    def get_all_examinations(self, modality: Modality) -> dict[str, Examination]:
        if modality not in self.cached_examinations:
            data = self.session.get(f'{FIREBASE_URL}/examination/{modality}/.json').json() # REST API returns unsorted results
            self.cached_examinations[modality] = dict(sorted(data.items(), key=lambda x: x[1]['name'].lower()))
            print(f'Fetched {len(data)} examinations for {modality}')
        else:
            print(f'Using cached examinations for {modality}')
        return self.cached_examinations[modality]

class ExaminationNotFoundError(Exception):
    pass