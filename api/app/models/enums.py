import enum


class ActionStatus(str, enum.Enum):
    inbox = "inbox"
    active = "active"
    pending = "pending"
    complete = "complete"


class ProjectStatus(str, enum.Enum):
    active = "active"
    complete = "complete"


class TagCategory(str, enum.Enum):
    context = "context"
    time = "time"
    energy = "energy"
