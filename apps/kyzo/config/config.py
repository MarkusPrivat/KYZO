import enum

class UserRole(enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class InputType(enum.Enum):
    MANUAL = "manual"
    SCAN = "scan"
