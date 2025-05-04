import re
from dataclasses import dataclass

from .error import AutoTriageError
from .modality import Modality
from .priority import Priority

@dataclass
class Request:
    modality: Modality
    exam: str
    priority: Priority = Priority.PLANNED # default for testing

    # def __post_init__(self):
    #     print(f'Modality: {self.modality}')
    #     print(f'Exam requested: {self.exam}')
    #     print(f'Priority: {self.priority}')

def request_from_clipboard(clipboard: str) -> Request:
    try:
        data = {k:v for k,v in (item.split('=', 1) for item in re.search(r'\[(.*)]', clipboard)[1].split(', ') )}
    except TypeError:
        raise AutoTriageError('No match')
    try:
        modality = Modality(data['rf_exam_type'])
    except KeyError:
        raise AutoTriageError(f'Object missing "rf_exam_type"')
    except ValueError:
        raise AutoTriageError(f'Modality "{data['rf_exam_type']}" not supported')
    try:
        exam = data['rf_reason']
        exam = re.sub(r'(\b(AND|LEFT|RIGHT|PLEASE)\b|\(GP\))', '', exam)
        exam = re.sub(r'\s+', ' ', exam.strip())
    except KeyError:
        raise AutoTriageError(f'Object missing "rf_reason"')
    try:
        priority = Priority.from_string(data['rf_original_priority'])
    except KeyError:
        raise AutoTriageError(f'Object missing "rf_original_priority"')
    return Request(modality, exam, priority)
