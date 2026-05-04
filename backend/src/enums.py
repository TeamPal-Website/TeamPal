from enum import Enum

class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'

class ResumeStatus(str, Enum):
    LOOKING_FOR_JOB = 'looking_for_job'
    NOT_LOOKING_FOR_JOB = 'not_looking_for_job'

class EmploymentIntent(str, Enum):
    COMMERCIAL = 'commercial'
    NONCOMMERCIAL = 'noncommercial'

class CommitmentLevel(str, Enum):
    FULL_TIME = 'full_time'
    PART_TIME = 'part_time'
    SIDE_PROJECT = 'side_project'

class ProjectsStatus(str, Enum):
    ACTIVE = 'active'
    PAUSED = 'paused'
    CLOSE = 'close'
    DELETED = 'deleted'

class ProjectVacancyExperience(str, Enum):
    NONE = 'none'
    LESS_THAN_ONE = '<1'
    ONE_TO_THREE = '1-3'
    THREE_TO_SIX = '3-6'
    SIX_PLUS = '6+'

class WorkFormat(str, Enum):
    REMOTE = 'remote'
    OFFICE = 'office'
    HYBRID = 'hybrid'

class Schedule(str, Enum):
    FIVE_TWO = '5/2'
    TWO_TWO = '2/2'
    FOUR_TWO = '4/2'
    THREE_THREE = '3/3'

class SalaryType(str, Enum):
    MONTHLY = 'monthly'
    PER_PROJECT = 'per_project'

class ContractType(str, Enum):
    GPH = 'gph'
    TK = 'tk'
    INTERNSHIP = 'internship'

class ApplicationStatus(str, Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'

class CancelReason(str, Enum):
    USER_WITHDRAWN = 'user_withdrawn'
    USER_LEFT = 'user_left'
    REMOVED_BY_OWNER = 'removed_by_owner'
    RESUME_UPDATED = 'resume_updated'
    ANOTHER_ACCEPTED = 'another_accepted'
    PROJECT_PAUSED = 'project_paused'
    PROJECT_DELETED = 'project_deleted'
    PROJECT_CLOSED = 'project_closed'

class NotificationEvent(str, Enum):
    APPLICATION_RECEIVED = 'application_received'
    APPLICATION_ACCEPTED = 'application_accepted'
    APPLICATION_REJECTED = 'application_rejected'
    APPLICATION_CANCELLED = 'application_cancelled'
    EMPLOYER_INVITED = 'employer_invited'
