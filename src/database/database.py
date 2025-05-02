from ..autotriage import Request, Examination, BodyPart

FIREBASE_URL = 'https://cogent-script-128909-default-rtdb.firebaseio.com'

class Database:
    def get_examination(self, request: Request) -> Examination:
        return Examination(BodyPart.LOWERLIMB, 'Q123') # todo replace stub
