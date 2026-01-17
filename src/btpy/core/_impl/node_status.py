from enum import Enum


class NodeStatus(Enum):
    # IDLE = 0
    RUNNING = 1
    SUCCESS = 2
    FAILURE = 3
    SKIPPED = 4
