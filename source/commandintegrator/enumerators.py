from enum import Enum, auto


class CommandPronoun(Enum):
    """
    Identifiable pronouns in recieved commands.
    __lt__ is implemented in order for a sorted
    set of instances to be returned.
    """
    INTERROGATIVE = auto()
    PERSONAL = auto()
    POSSESSIVE = auto()
    UNIDENTIFIED = auto()

    def __lt__(self, other):
        return self.value < other.value