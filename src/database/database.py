from ..autotriage import Request, Examination, BodyPart


class Database:
    def get_examination(self, request: Request) -> Examination:
        return Examination(BodyPart.LOWERLIMB, 'Q123') # todo replace stub
