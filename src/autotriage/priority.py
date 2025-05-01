from enum import Enum, auto

class Priority(Enum):
	UNKNOWN = auto()
	STAT = auto()
	HOURS_4 = auto()
	HOURS_24 = auto()
	DAYS_2 = auto()
	WEEKS_2 = auto()
	WEEKS_4 = auto()
	WEEKS_6 = auto()
	PLANNED = auto()

	@staticmethod
	def from_string(priority_string):
		s = priority_string.lower()
		if s == 'null': return Priority.UNKNOWN
		elif 'immediate' in s: return Priority.STAT
		elif '24 hours' in s: return Priority.HOURS_24
		elif '4 hours' in s: return Priority.HOURS_4 # this line has to be after the line matching 24 hours
		elif 'days'	in s: return Priority.DAYS_2 #2(-3) days
		elif '2 weeks' in s: return Priority.WEEKS_2
		elif '4 weeks' in s: return Priority.WEEKS_4
		elif '6 weeks' in s: return Priority.WEEKS_6 # never used
		else: return Priority.PLANNED