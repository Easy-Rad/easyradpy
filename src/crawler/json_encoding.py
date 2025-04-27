import json
from datetime import datetime

from .order import Order
from .reporter import Reporter


def save_json(filename: str, obj) -> None:
    with open(filename, mode='w') as f:
        json.dump(obj, f, indent=2, default=json_serial)


def json_serial(obj) -> str | dict:
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Reporter):
        return dict(
            first_name=obj.first_name,
            last_name=obj.last_name,
            reports=obj.reports,
        )
    elif isinstance(obj, Order):
        return dict(
            accession=obj.accession,
            body_parts=obj.body_parts,
            modality=obj.modality,
            study_description=obj.study_description,
            image_count=obj.image_count,
            ffs_body_part_count=obj.ffs_body_part_count,
            fee=obj.fee,
        )
    raise TypeError(f'Type {type(obj)} not serializable')
