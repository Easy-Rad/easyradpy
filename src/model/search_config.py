from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class Account(StrEnum):
    ME = 'Me'
    ALL = 'All'
    OTHER = 'Other'

class Period(StrEnum):
    PAST_HOUR = 'PastHour'
    PAST_FOUR_HOURS = 'PastFourHours'
    TODAY = 'Today'
    YESTERDAY = 'Yesterday'
    PAST_TWO_DAYS = 'PastTwoDays'
    PAST_THREE_DAYS = 'PastThreeDays'
    PAST_WEEK = 'PastWeek'
    PAST_TWO_WEEKS = 'PastTwoWeeks'
    PAST_MONTH = 'PastMonth'
    CUSTOM = 'Custom' # Use date range

@dataclass
class SearchConfig:
    ffs_only: bool
    account_id: int | None
    period: Period
    from_date: datetime # ignored unless period is CUSTOM
    to_date: datetime # ignored unless period is CUSTOM
    save_last_request: bool = False
