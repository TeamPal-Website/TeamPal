from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ResumeStatus(str, Enum):
    LOOKING_FOR_JOB = "looking_for_job"
    NOT_LOOKING_FOR_JOB = "not_looking_for_job"