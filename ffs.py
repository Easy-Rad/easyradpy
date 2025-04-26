from dataclasses import dataclass
from datetime import datetime, date

import holidays

FFS_DATA = dict(
    CT=('CT', (60, 135, 160, 200)),
    CR=('XR', (12, 20, 35)),
    MR=('MR', (75,)),
    US=('US', (12,)),
)
HOLIDAYS = holidays.country_holidays('NZ', subdiv='CAN')

@dataclass
class FFSprofile:
    study_count: int
    studies: dict[str,list[int]]
    fee: int

def within_ffs_hours(dt: datetime):
    return 6 <= dt.hour < 23 and (dt.hour < 8 or dt.hour >= 18 or weekend_or_holiday(dt))

def weekend_or_holiday(d: date):
    return d.isoweekday() >= 6 or d in HOLIDAYS
