from enum import Enum, auto


class UserStatus(Enum):
    CURRENT = auto()
    PLANNING = auto()
    COMPLETED = auto()
    DROPPED = auto()
    PAUSED = auto()
    REPEATING = auto()


class MediaStatus(Enum):
    FINISHED = auto()
    RELEASING = auto()
    NOT_YET_RELEASED = auto()
    CANCELLED = auto()
    HIATUS = auto()


class MediaType(Enum):
    ANIME = auto()
    MANGA = auto()
