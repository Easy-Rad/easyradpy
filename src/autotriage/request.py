import re

from .error import AutoTriageError
from src.autotriage.modality import Modality
from .priority import Priority


class Request:
    def __init__(self, clipboard: str):
        try:
            data = {k:v for k,v in (item.split('=', 1) for item in re.search(r'\[(.*)]', clipboard)[1].split(', ') )}
        except TypeError:
            raise AutoTriageError('No match')
        try:
            self.modality = Modality[data['rf_exam_type']]
        except KeyError:
            raise AutoTriageError(f'Object missing "rf_exam_type"')
        except ValueError:
            raise AutoTriageError(f'Modality "{data['rf_exam_type']}" not supported')
        else:
            print(f'Modality: {self.modality}')
        try:
            self.exam = data['rf_reason']
            self.exam = re.sub(r'(\b(AND|LEFT|RIGHT|PLEASE)\b|\(GP\))', '', self.exam)
            self.exam = re.sub(r'\s+', ' ', self.exam.strip())
        except KeyError:
            raise AutoTriageError(f'Object missing "rf_reason"')
        else:
            print(f'Exam requested: {self.exam}')
        try:
            self.priority = Priority.from_string(data['rf_original_priority'])
        except KeyError:
            raise AutoTriageError(f'Object missing "rf_original_priority"')
        else:
            print(f'Priority: {self.priority}')




