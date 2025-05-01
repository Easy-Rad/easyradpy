from dataclasses import dataclass
from enum import StrEnum

class BodyPart(StrEnum):
    HEAD = 'HEAD'
    NECK = 'NECK'
    SPINE = 'SPINE'
    CHEST = 'CHEST'
    ABDO_PELV = 'ABDO/PELV'
    PLV_HIP_TH = 'PLV/HIP/TH'
    OBST_GYNAE = 'OBST/GYNAE'
    KNEE_LOWLG = 'KNEE/LOWLG'
    ANKLE_FOOT = 'ANKLE/FOOT'
    SHLD_UPP = 'SHLD/UPP'
    ELB_FORARM = 'ELB/FORARM'
    WRIST_HAND = 'WRIST/HAND'
    LOWERLIMB = 'LOWERLIMB'
    UPPERLIMB = 'UPPERLIMB'
    CHEST_ABDO = 'CHEST/ABDO'
    OTHER = 'OTHER'
    NOTAPPLIC = 'NOTAPPLIC'

@dataclass
class Examination:
    body_part: BodyPart
    code: str
