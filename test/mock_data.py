from datetime import datetime

from order import Order
from reporter import Reporter

ACCESSION_1 = 'CA-12334-CT'
ACCESSION_2 = 'CA-52314-CT'
ACCESSION_3 = 'CA-54636-US'
ACCESSION_4 = 'CA-63345-NM'

_studies = [
    dict(
        accession=ACCESSION_1,
        body_parts=['Head', 'Abdomen'],
        modality='CT',
        study_description='CT HEAD ABDOMEN',
        image_count=40,
    ),
    dict(
        accession=ACCESSION_2,
        body_parts=['Head'],
        modality='CT',
        study_description='CT HEAD',
        image_count=30,
    ),
    dict(
        accession=ACCESSION_3,
        body_parts=['Toes'],
        modality='US',
        study_description='US toes',
        image_count=3,
    ),
    dict(
        accession=ACCESSION_4,
        body_parts=['Neck'],
        modality='NM',
        study_description='NM study of neck',
        image_count=300,
    ),
]

sample_orders = { study['accession']: Order(
    accession=study['accession'],
    body_parts=study['body_parts'],
    modality=study['modality'],
    study_description=study['study_description'],
    image_count=study['image_count'],
) for study in _studies }

sample_reports: list[Reporter] = [
    Reporter(
        first_name='Jean',
        last_name='Valjean',
        reports=[
            (ACCESSION_1, datetime(2020, 1, 1, 18, 59)),
            (ACCESSION_3, datetime(2023, 3, 22, 19,8)),
        ],
    ),
    Reporter(
        first_name='Alexander',
        last_name='Hamilton',
        reports=[
            (ACCESSION_2, datetime(2025, 1, 1, 22)),
        ],
    ),
]
