from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ResumeStatus(str, Enum):
    LOOKING_FOR_JOB = "looking_for_job"
    NOT_LOOKING_FOR_JOB = "not_looking_for_job"


class EmploymentIntent(str, Enum):
    COMMERCIAL = "commercial"
    NONCOMMERCIAL = "noncommercial"


class CommitmentLevel(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SIDE_PROJECT = "side_project"
