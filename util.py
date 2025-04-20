import json
from datetime import date, datetime
from reporter import Reporter
from order import Order
import holidays

HOLIDAYS = holidays.NZ(subdiv='CAN')

def weekend_or_holiday(d: date):
    return d.isoweekday() >= 6 or d in HOLIDAYS

def within_ffs_hours(dt: datetime):
    return dt.hour >= 6 and dt.hour < 23 and (dt.hour < 8 or dt.hour >= 18 or weekend_or_holiday(dt))

def save_json(filename: str, obj):
    with open(filename, mode='w') as f:
        json.dump(obj, f, indent=2, default=json_serial)

def json_serial(obj):
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
    raise TypeError (f'Type {type(obj)} not serializable')
