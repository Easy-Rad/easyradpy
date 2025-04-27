from dataclasses import dataclass
from datetime import datetime, date
from zoneinfo import ZoneInfo

import holidays

FFS_DATA = dict(
    CT=('CT', (60, 135, 160, 200)),
    CR=('XR', (12, 20, 35)),
    MR=('MR', (75,)),
    US=('US', (12,)),
)
USER_TIMEZONES = {
    75: 'America/Denver',  # VM
    94: 'America/Vancouver',  # RDT
    107: 'Europe/London',  # NOB
}
DEFAULT_TIMEZONE = ZoneInfo('Pacific/Auckland')
HOLIDAYS = holidays.country_holidays('NZ', subdiv='CAN')

@dataclass
class FFSprofile:
    study_count: int
    studies: dict[str,list[int]]
    fee: int


def get_local_date_time(dt: datetime, account_id: int):
    try:
        tz = ZoneInfo(USER_TIMEZONES[account_id])
    except KeyError:
        tz = DEFAULT_TIMEZONE
    return dt.astimezone(tz)


def within_ffs_hours(local_date_time: datetime):
    return 6 <= local_date_time.hour < 23 and outside_working_hours(local_date_time.astimezone(DEFAULT_TIMEZONE))


def outside_working_hours(dt: datetime):
    return dt.hour < 8 or dt.hour >= 18 or weekend_or_holiday(dt)

def weekend_or_holiday(d: date):
    return d.isoweekday() >= 6 or d in HOLIDAYS
