from datetime import datetime

from order import Order
from reporter import Reporter

ACCESSION_1 = 'CA-12334-CT'
ACCESSION_2 = 'CA-52314-CT'
ACCESSION_3 = 'CA-54636-US'
ACCESSION_4 = 'CA-63345-NM'
ACCESSION_5 = 'CA-23948-CR'
ACCESSION_6 = 'CA-23426-CR'
ACCESSION_7 = 'CA-52475-CR'

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
    dict(
        accession=ACCESSION_5,
        body_parts=['Chest'],
        modality='CR',
        study_description='Chest',
        image_count=3,
    ),
    dict(
        accession=ACCESSION_6,
        body_parts=['Chest'],
        modality='CR',
        study_description='Chest',
        image_count=3,
    ),
    dict(
        accession=ACCESSION_7,
        body_parts=['Chest'],
        modality='CR',
        study_description='Chest',
        image_count=3,
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
            # (ACCESSION_4, datetime(2025, 1, 1, 22)),
        ],
    ),
    Reporter(
        first_name='Alexander',
        last_name='Zamilton',
        reports=[
            (ACCESSION_2, datetime(2025, 1, 1, 22)),
            # (ACCESSION_4, datetime(2025, 1, 1, 22)),
        ],
    ),
    Reporter(
        first_name='Alexander',
        last_name='Zamilton',
        reports=[
            (ACCESSION_2, datetime(2025, 1, 1, 22)),
            (ACCESSION_5, datetime(2025, 1, 3, 20)),
        ],
    ),
    Reporter(
        first_name='Charles',
        last_name='Xavier',
        reports=[
            (ACCESSION_5, datetime(2025, 1, 3, 20)),
            (ACCESSION_6, datetime(2025, 1, 5, 22)),
            (ACCESSION_7, datetime(2025, 1, 4, 21)),
        ],
    ),
    Reporter(
        first_name='Jean',
        last_name='Paljean',
        reports=[
            (ACCESSION_1, datetime(2020, 1, 1, 18, 59)),
            (ACCESSION_3, datetime(2023, 3, 22, 19, 8)),
        ],
    ),

]
