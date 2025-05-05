import re
from dataclasses import dataclass

from .error import AutoTriageError
from .modality import Modality
from .priority import Priority
from ..util.format import tokenise_request, parse_comrad_db_object


@dataclass
class Request:
    modality: Modality
    exam: str
    priority: Priority = Priority.PLANNED # default for testing
    def tokenised_exam(self):
        return tokenise_request(self.exam)

def request_from_clipboard(clipboard: str) -> Request:
    try:
        data = parse_comrad_db_object(clipboard)
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
